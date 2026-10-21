# cnv_translator.py

from __future__ import annotations

import re

from classification.parsers.auto_translator import resolve_translations


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


UNLIKELY_PATTERN = re.compile(
    r"^The\s+(?:above\s+)?"
    r"(?P<subject>(?:deletion|duplication)s?"
    r"(?:\s+and\s+(?:deletion|duplication)s?)?)\s+"
    r"(?:is|are)\s+unlikely\s+to\s+cause\s+pathogenic\s+phenotypes?\.?$",
    re.IGNORECASE
)

SUBJECT_ES = {
    "deletion": "deleción",
    "deletions": "deleciones",
    "duplication": "duplicación",
    "duplications": "duplicaciones",
}


def translate_interpretation_sentence(sentence: str) -> str | None:
    """
    Traduce las frases de interpretación de formato conocido:

        "The duplication is unlikely to cause pathogenic phenotypes."
        -> "Es poco probable que la duplicación cause fenotipos patogénicos."

        "The above deletion and duplication is unlikely to cause pathogenic phenotypes."
        -> "Es poco probable que la deleción y duplicación causen fenotipos patogénicos."

    Devuelve None si la frase no se reconoce.
    """
    match = UNLIKELY_PATTERN.match(" ".join(sentence.split()))

    if not match:
        return None

    nouns = re.split(r"\s+and\s+", match.group("subject").lower())

    article = "las" if nouns[0].endswith("s") else "la"
    subject = f"{article} " + " y ".join(SUBJECT_ES[noun] for noun in nouns)

    plural = len(nouns) > 1 or nouns[0].endswith("s")
    verb = "causen" if plural else "cause"

    return f"Es poco probable que {subject} {verb} fenotipos patogénicos."


def translate_interpretations(parsed_report: dict) -> tuple[str, list[dict]]:
    """
    Arma el párrafo de interpretación en español a partir del texto
    que acompaña a cada variante en el informe original.

    Las frases de formato fijo se traducen por patrón; el resto con el
    glosario translations/interpretaciones.json o traducción automática.

    Devuelve (texto, issues). Lo que no se pudo traducir queda en inglés
    dentro del texto.
    """
    texts = [
        variant.get("interpretation_en", "")
        for variant in parsed_report.get("variants", []) or []
        if variant.get("interpretation_en")
    ]

    fixed = {
        english: translate_interpretation_sentence(english)
        for english in texts
    }

    translations, issues = resolve_translations(
        "interpretaciones",
        [english for english in texts if fixed[english] is None]
    )

    sentences = []

    for english in texts:

        spanish = fixed[english] or translations.get(english, english)

        if spanish not in sentences:
            sentences.append(spanish)

    return " ".join(sentences), issues


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
