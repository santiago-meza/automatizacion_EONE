import re

from extractors.table_extractor import make_issue
from classification.parsers.interpretacion_cnv_parser import parse_cnv_interpretations


POSITION_PATTERN = re.compile(r"^(chr(?:\d{1,2}|X|Y)):(\d+)-(\d+)$")

TYPE_PATTERN = re.compile(r"^(AMP|DEL)\(X(\d+)\)$")

CYTOBAND_PATTERN = re.compile(
    r"^(\d{1,2}|X|Y)[pq]\d+(\.\d+)?(-[pq]?\d+(\.\d+)?)?$"
)

REFERENCE_PATTERN = re.compile(r"^(\d{6}|-)$")

# Modos de herencia de OMIM. Una celda puede traer varios separados por coma.
INHERITANCE_VALUES = {
    "-",
    "Autosomal dominant",
    "Autosomal recessive",
    "X-linked",
    "X-linked dominant",
    "X-linked recessive",
    "Y-linked",
    "Pseudoautosomal dominant",
    "Pseudoautosomal recessive",
    "Digenic dominant",
    "Digenic recessive",
    "Mitochondrial",
    "Multifactorial",
    "Isolated cases",
    "Somatic mutation",
    "Somatic mosaicism",
    "Inherited chromosomal imbalance",
}

TYPE_NAMES = {
    "DEL": "deletion",
    "AMP": "duplication",
}

# Diferencia tolerada entre el tamaño del resumen y el de la tabla (MB).
SIZE_TOLERANCE_MB = 0.02


def _validate_cnv(cnv):
    """
    Chequea el formato de un CNV y de cada una de sus asociaciones.
    """

    issues = []

    label = cnv.get("position") or cnv.get("cytoband") or "(sin posición)"

    position_match = POSITION_PATTERN.match(cnv.get("position", ""))

    if not position_match:

        issues.append(make_issue(
            "ERROR",
            f"{label}: posición con formato inesperado: "
            f"\"{cnv.get('position', '')}\""
        ))

    elif int(position_match.group(2)) >= int(position_match.group(3)):

        issues.append(make_issue(
            "ERROR",
            f"{label}: el inicio de la posición no es menor que el fin."
        ))

    if not TYPE_PATTERN.match(cnv.get("type", "")):

        issues.append(make_issue(
            "ERROR",
            f"{label}: tipo con formato inesperado: \"{cnv.get('type', '')}\""
        ))

    cytoband_match = CYTOBAND_PATTERN.match(cnv.get("cytoband", ""))

    if not cytoband_match:

        issues.append(make_issue(
            "ERROR",
            f"{label}: CytoBand con formato inesperado: "
            f"\"{cnv.get('cytoband', '')}\""
        ))

    elif position_match and "chr" + cytoband_match.group(1) != position_match.group(1):

        issues.append(make_issue(
            "ERROR",
            f"{label}: el CytoBand \"{cnv['cytoband']}\" no corresponde al "
            "cromosoma de la posición. Las filas pueden estar mezcladas."
        ))

    for assoc in cnv.get("associations", []):

        row = f"{label} / {assoc.get('gene') or '(sin gen)'}"

        if not assoc.get("gene") or " " in assoc["gene"]:

            issues.append(make_issue(
                "ERROR",
                f"{row}: gen vacío o con más de un valor: "
                f"\"{assoc.get('gene', '')}\" "
                f"(enfermedad: \"{assoc.get('disease', '')}\")"
            ))

        if not REFERENCE_PATTERN.match(assoc.get("reference", "")):

            issues.append(make_issue(
                "ERROR",
                f"{row}: referencia OMIM con formato inesperado: "
                f"\"{assoc.get('reference', '')}\""
            ))

        inheritance = assoc.get("inheritance", "")

        modes = [mode.strip() for mode in inheritance.split(",")]

        if not all(mode in INHERITANCE_VALUES for mode in modes):

            issues.append(make_issue(
                "ERROR",
                f"{row}: herencia incompleta o no reconocida: "
                f"\"{inheritance}\" "
                f"(enfermedad: \"{assoc.get('disease', '')}\")"
            ))

    return issues


def _validate_against_summary(cnvs, text):
    """
    Compara los CNVs de la tabla con las líneas del resumen del informe:

        *deletion(X1) of 0.52 MB (chr15:22,759,530-23,279,684) in the
        15q11.2 region, Pathogenic

    Son dos fuentes independientes dentro del mismo PDF, así que si la
    tabla se extrajo mal o está incompleta no van a coincidir.
    """

    issues = []

    summary = {}

    for variant in parse_cnv_interpretations(text)["variants"]:

        position = (
            f"{variant['chromosome']}:"
            f"{variant['coord_start'].replace(',', '')}-"
            f"{variant['coord_end'].replace(',', '')}"
        )

        summary[position] = variant

    table = {cnv.get("position", ""): cnv for cnv in cnvs}

    for position in summary:

        if position not in table:

            issues.append(make_issue(
                "ERROR",
                f"{position}: figura en el resumen del informe pero no en "
                "la tabla."
            ))

    for position, cnv in table.items():

        variant = summary.get(position)

        if variant is None:

            issues.append(make_issue(
                "ERROR",
                f"{position or '(sin posición)'}: figura en la tabla pero no "
                "en el resumen del informe."
            ))

            continue

        type_match = TYPE_PATTERN.match(cnv.get("type", ""))

        if type_match and (
            TYPE_NAMES[type_match.group(1)] != variant["variant_type"]
            or int(type_match.group(2)) != variant["copy_number"]
        ):

            issues.append(make_issue(
                "ERROR",
                f"{position}: la tabla dice {cnv['type']} y el resumen "
                f"{variant['variant_type']}(X{variant['copy_number']})."
            ))

        if cnv.get("cytoband") != variant["region"]:

            issues.append(make_issue(
                "ERROR",
                f"{position}: la tabla dice CytoBand \"{cnv.get('cytoband')}\" "
                f"y el resumen \"{variant['region']}\"."
            ))

        position_match = POSITION_PATTERN.match(position)

        if position_match:

            size_mb = (
                int(position_match.group(3)) - int(position_match.group(2))
            ) / 1_000_000

            if abs(size_mb - variant["size_mb"]) > SIZE_TOLERANCE_MB:

                issues.append(make_issue(
                    "AVISO",
                    f"{position}: el resumen indica {variant['size_mb']} MB "
                    f"pero las coordenadas dan {size_mb:.2f} MB."
                ))

    return issues


def validate_cnvs(cnvs, text):
    """
    Valida los CNVs devueltos por parse_cnv_tables().

    Parameters
    ----------
    cnvs : list
        Salida de parse_cnv_tables().

    text : str
        Texto completo del informe (extract_text()).

    Returns
    -------
    list
        Lista de issues {"level", "page", "message"}.
        Lista vacía si no se detectó ningún problema.
    """

    issues = []

    for cnv in cnvs:
        issues.extend(_validate_cnv(cnv))

    issues.extend(_validate_against_summary(cnvs, text))

    return issues
