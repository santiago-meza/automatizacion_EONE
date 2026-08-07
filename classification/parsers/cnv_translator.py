# cnv_translator.py

from __future__ import annotations


def classification_to_spanish(classification: str | None) -> str:
    """
    Convierte la clasificación del parser a la etiqueta en español.
    Ajustá si en tu parser llegan más valores.
    """
    if not classification:
        return ""

    c = classification.strip().lower()

    mapping = {
        "pathogenic": "Patogénica",
        "non-pathogenic": "No patogénica",
        "non pathogenic": "No patogénica",
    }

    # fallback: si viene algo raro, devolvemos tal cual pero capitalizado un poco
    return mapping.get(c, classification)


def format_bullet_es(variant: dict) -> dict:
    """
    Devuelve una estructura lista para python-docx con:
      - prefix: texto normal (sin bold)
      - suffix_bold: texto final que va en negrita (o "" si no corresponde)

    Espera input con campos como los que devolvió parse_cnv_interpretations():
      {
        'variant_type': 'deletion'|'duplication',
        'copy_number': int,
        'size_mb': float,
        'chromosome': 'chr15',
        'coord_start': '22,759,530',
        'coord_end': '23,279,684',
        'region': '15q11.2',
        'classification': 'Pathogenic'|'Non-Pathogenic'...
      }
    """
    variant_type = (variant.get("variant_type") or "").strip().lower()
    copy_number = variant.get("copy_number", "")
    size_mb = variant.get("size_mb", "")
    chromosome = variant.get("chromosome", "")
    coord_start = variant.get("coord_start", "")
    coord_end = variant.get("coord_end", "")
    region = variant.get("region", "")
    classification = variant.get("classification", "")

    # “la deleción/duplicación”
    if variant_type == "deletion":
        action = "la deleción"
    elif variant_type == "duplication":
        action = "la duplicación"
    else:
        # fallback por si cambia nombre
        action = f"la {variant_type}"

    # Texto base según tu ejemplo
    # Ej: "la deleción (x 1) de 0.52 MB (chr15:22,759,530-23,279,684) en la región 15q11.2. "
    prefix = (
        f"{action} (x {copy_number}) de {size_mb} MB "
        f"({chromosome}:{coord_start}-{coord_end}) "
        f"en la región {region}. "
    )

    # En negrita: "- Patogénica" o "- No patogénica"
    class_es = classification_to_spanish(classification)
    suffix_bold = f"- {class_es}" if class_es else ""

    return {
        "prefix": prefix,
        "suffix_bold": suffix_bold,
    }


def format_bullets_es_for_report(parsed_report: dict) -> list[dict]:
    """
    parsed_report debería venir del parser:
      {
        "variants": [...],
        "references": [...]
      }

    Devuelve lista de bullets ya formateadas para el docx.
    """
    variants = parsed_report.get("variants", []) or []
    return [format_bullet_es(v) for v in variants]
