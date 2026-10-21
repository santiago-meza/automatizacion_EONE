import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

from config import TEMPLATES

from extractors.text_extractor import extract_text
from extractors.table_extractor import extract_cnv_tables, make_issue

from classification.parsers.report_parser import parse_report
from classification.parsers.cnv_table_parser import parse_cnv_tables
from classification.parsers.cnv_table_translator import translate_cnvs
from classification.parsers.interpretacion_cnv_parser import parse_cnv_interpretations
from classification.parsers.cnv_translator import translate_interpretations
from classification.parsers.loh_parser import parse_loh, loh_detection_phrase
from validators.cnv_validator import validate_cnvs

from classifier import select_template
from template_engine import generate_report
from generators.cnv_table import generate_cnv_table
from document_merger import insert_table_at_placeholder
from pdf_exporter import WordConverter


CNV_TABLE_TEMPLATE = TEMPLATES / "table_cnv.docx"

LEVELS = ["ERROR", "AVISO", "INFO"]


def format_issues(issues):
    """
    Devuelve los issues como líneas de texto, los más graves primero.
    """

    lines = []

    for issue in sorted(issues, key=lambda i: LEVELS.index(i["level"])):

        page = f" (pág. {issue['page']})" if issue["page"] else ""

        lines.append(f"  [{issue['level']}]{page} {issue['message']}")

    return lines


def safe_filename(name):
    """
    Saca los caracteres que Windows no permite en nombres de archivo.
    """

    name = re.sub(r'[<>:"/\\|?*]', "", name)

    return re.sub(r"\s+", " ", name).strip()


def build_variants(parsed):
    """
    Arma las variantes que usa el template para las viñetas de la
    interpretación, a partir de las líneas del resumen del informe:

        *duplication(X3) of 0.16 MB (chr11:18,342,081-18,503,737) in the
        11p15.1 region, Non-Pathogenic
    """

    return [
        {
            **variant,
            # tamaño tal cual figura en el informe
            "size_mb": variant["size_text"],
        }
        for variant in parsed["variants"]
    ]


def process_report(pdf, output_dir, converter=None):
    """
    Genera el informe en español de un PDF, en Word y en PDF.

    Parameters
    ----------
    converter : WordConverter, optional
        Instancia de Word abierta para exportar el PDF. Sin ella solo
        se genera el Word.

    Returns
    -------
    tuple
        (output_file, pdf_file, issues)
    """

    pdf = Path(pdf)
    output_dir = Path(output_dir)

    # =====================================
    # 1. Extract text and parse report data
    # =====================================

    text = extract_text(pdf)

    data = parse_report(text)

    # Keep full report text for classification
    data["TEXT"] = text

    # =====================================
    # 2. Extract, validate and translate CNV table
    # =====================================

    tables, issues = extract_cnv_tables(pdf)

    cnvs = parse_cnv_tables(tables)

    issues = issues + validate_cnvs(cnvs, text)

    # Tabla en español (tipo, enfermedad y herencia)
    cnvs_es, translation_issues = translate_cnvs(cnvs)

    issues = issues + translation_issues

    # =====================================
    # 3. Interpretation (bullets and translated sentence)
    # =====================================

    parsed = parse_cnv_interpretations(text)

    data["CNV_INTERPRETATIONS_PARSED"] = {"variants": build_variants(parsed)}

    data["INTERPRETACION"], interpretation_issues = translate_interpretations(parsed)

    issues = issues + interpretation_issues

    data["REFERENCIAS"] = parsed["references"]

    # =====================================
    # 4. LOH regions
    # =====================================

    loh = parse_loh(text)

    data["LOH_REGIONS"] = loh["regions"]
    data["LOH_DETECCION_PHRASE"] = loh_detection_phrase(len(loh["regions"]))
    data["LOH_RESULTADO_PHRASE"] = loh_detection_phrase(len(loh["regions"]), end=".")

    for message in loh["issues"]:
        issues.append(make_issue("ERROR", message))

    # =====================================
    # 5. Select template and generate main report
    # =====================================

    template = select_template(data)

    if not data["PROTOCOL"] or not data["PATIENT"]:
        raise ValueError(
            "No se pudo leer el protocolo o el nombre del paciente."
        )

    base_filename = safe_filename(
        f"{data['PROTOCOL']}, {data['PATIENT']}, Genda"
    )

    output_file = output_dir / f"{base_filename}.docx"

    generate_report(
        template,
        output_file,
        data
    )

    # =====================================
    # 6. Generate CNV table and insert it into the report
    # =====================================

    if cnvs_es:

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_cnv_table = Path(temp_dir) / "temp_cnv_table.docx"

            generate_cnv_table(
                CNV_TABLE_TEMPLATE,
                cnvs_es,
                temp_cnv_table
            )

            insert_table_at_placeholder(
                output_file,
                temp_cnv_table,
                output_file
            )

    # =====================================
    # 7. Export PDF
    # =====================================

    pdf_file = None

    if converter:

        try:
            pdf_file = converter.convert(output_file)

        except Exception as error:
            issues.append(make_issue(
                "ERROR",
                f"Se generó el Word pero no el PDF: {error}"
            ))

    return output_file, pdf_file, issues


@contextmanager
def open_word(log):
    """
    Abre Word para exportar los PDFs. Si no se puede, devuelve None y
    se generan solo los .docx.
    """

    try:
        converter = WordConverter()
        converter.__enter__()

    except Exception as error:
        log(f"[AVISO] No se pudo abrir Word; solo se generarán los .docx ({error}).")
        log("")
        yield None
        return

    try:
        yield converter
    finally:
        converter.__exit__(None, None, None)


def process_folder(input_dir, output_dir, log=print, on_progress=None):
    """
    Procesa todos los PDFs de una carpeta. Un informe que falla no
    detiene al resto.

    Parameters
    ----------
    log : callable
        Recibe cada línea de texto del progreso.

    on_progress : callable, optional
        Recibe (procesados, total) después de cada informe.

    Returns
    -------
    list
        Un dict por PDF: {"pdf", "output", "pdf_output", "issues", "error"}.
    """

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        log("No se encontraron PDFs.")
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    # Una sola instancia de Word para exportar todos los PDFs
    with open_word(log) as converter:
        results = process_pdfs(pdf_files, output_dir, converter, log, on_progress)

    # -----------------------------------------
    # Resumen
    # -----------------------------------------

    failed = [r for r in results if r["error"]]

    with_errors = [
        r for r in results
        if any(issue["level"] == "ERROR" for issue in r["issues"])
    ]

    log(f"Informes generados: {len(results) - len(failed)} de {len(results)}")

    if with_errors:

        log("Generados con ERRORES (revisar a mano):")

        for r in with_errors:
            log(f"  - {r['pdf'].name}")

    if failed:

        log("No generados:")

        for r in failed:
            log(f"  - {r['pdf'].name}: {r['error']}")

    return results


def process_pdfs(pdf_files, output_dir, converter, log, on_progress):

    results = []

    for index, pdf in enumerate(pdf_files, start=1):

        log("=" * 80)
        log(pdf.name)
        log("=" * 80)

        result = {
            "pdf": pdf,
            "output": None,
            "pdf_output": None,
            "issues": [],
            "error": None
        }

        try:

            (
                result["output"],
                result["pdf_output"],
                result["issues"]
            ) = process_report(
                pdf,
                output_dir,
                converter
            )

        except PermissionError as error:

            result["error"] = (
                "No se pudo escribir el archivo de salida; si está abierto "
                f"en Word, cerralo y volvé a generar ({Path(error.filename or '').name})."
            )

            log(f"NO SE PUDO GENERAR: {result['error']}")

        except Exception as error:

            result["error"] = str(error) or type(error).__name__

            log(f"NO SE PUDO GENERAR: {result['error']}")

        else:

            if result["issues"]:

                log("REVISAR ESTE INFORME:")

                for line in format_issues(result["issues"]):
                    log(line)

            log("Generado:")
            log(str(result["output"]))

            if result["pdf_output"]:
                log(str(result["pdf_output"]))

        log("")

        results.append(result)

        if on_progress:
            on_progress(index, len(pdf_files))

    return results
