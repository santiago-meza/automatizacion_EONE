from docxtpl import DocxTemplate
from pathlib import Path
from datetime import datetime
from html import escape


def generate_report(template_path: Path, output_path: Path, data: dict):
    doc = DocxTemplate(template_path)
    # Fecha en la que se genera el informe traducido
    today = datetime.now().strftime("%d/%m/%Y")

    # --- construir CNV_VARIANTES para el template ---
    parsed = data.get("CNV_INTERPRETATIONS_PARSED") or {}
    variants = parsed.get("variants", []) or []

    def classification_to_spanish_bold(classification: str) -> str:
        # Las variantes no patogénicas no llevan la clasificación en la
        # viñeta; el resto sí: "... en la región 7p22.1. – VUS."
        if not classification:
            return ""

        c = classification.strip().lower()
        if c in ("non-pathogenic", "non pathogenic"):
            return ""
        if c == "pathogenic":
            return "Patogénica"
        if c == "likely pathogenic":
            return "Probablemente patogénica"
        if c == "vus":
            return "VUS"

        # fallback por si llega otra clase
        return classification.strip()

    def format_variant_for_template(v: dict) -> dict:
        variant_type = (v.get("variant_type") or "").strip().lower()
        copy_number = v.get("copy_number", "")
        size_mb = v.get("size_mb", "")
        chromosome = v.get("chromosome", "")
        coord_start = v.get("coord_start", "")
        coord_end = v.get("coord_end", "")
        region = v.get("region", "")
        classification = v.get("classification", "")

        if variant_type == "deletion":
            action = "la deleción"
        elif variant_type == "duplication":
            action = "la duplicación"
        else:
            action = f"la {variant_type}"

        # Línea 1 sin negrita:
        prefix = (
            f"{action} (x {copy_number}) de {size_mb} MB "
            f"({chromosome}:{coord_start}-{coord_end}) "
            f"en la región {region}."
        )

        # sufijo que el template pone en negrita: "<prefix> – VUS."
        suffix_bold = classification_to_spanish_bold(classification)

        return {
            "prefix": prefix + (" – " if suffix_bold else ""),
            "suffix_bold": suffix_bold,
            "suffix_end": "." if suffix_bold else "",
        }

    cnv_variantes = [format_variant_for_template(v) for v in variants]

    context = {
        "PACIENTE": data.get("PATIENT", ""),
        "PROTOCOLO": data.get("PROTOCOL", ""),
        "FECHA": today,
        "RESULTADO": data.get("RESULTADO", ""),

        "RESULTADO_VARIANTES_PATOGENICAS": data.get(
            "RESULTADO_VARIANTES_PATOGENICAS",
            "No se hallaron Variantes Patogénicas."
        ),
        "CNV_DETECCION_PHRASE": data.get(
            "CNV_DETECCION_PHRASE",
            "Se detectó una variante en el Número de Copias (CNV):"
        ),
        # Lista para el loop del template
        "VARIANTS_FOUND": cnv_variantes,
        # texto libre del informe original: puede traer "&" o "<"
        "INTERPRETACION": escape(data.get("INTERPRETACION", ""), quote=False),

        # LOH
        "LOH_REGIONS": data.get("LOH_REGIONS", []),
        "LOH_DETECCION_PHRASE": data.get("LOH_DETECCION_PHRASE", ""),
        "LOH_RESULTADO_PHRASE": data.get("LOH_RESULTADO_PHRASE", ""),

        "REFERENCIAS": [
            escape(reference, quote=False)
            for reference in data.get("REFERENCIAS", [])
        ],
        "CNV_TABLE": "{{ CNV_TABLE }}",
    }

    doc.render(context, autoescape=False)
    doc.save(output_path)
