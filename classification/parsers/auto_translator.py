"""
auto_translator.py

Traducción automática (API de Claude) de los textos que no están en los
glosarios: nombres de enfermedades e interpretaciones en texto libre.

Solo se envían esos textos; nunca datos del paciente.

Cada traducción automática se guarda en el glosario correspondiente (no se
vuelve a pedir) y queda anotada en translations/automaticas_a_revisar.json.
Mientras esté anotada ahí, el informe avisa que hay que revisarla. Una vez
revisada (y corregida en el glosario si hace falta) se borra de esa lista.

La API key se toma de la variable de entorno ANTHROPIC_API_KEY o del archivo
anthropic_api_key.txt en la carpeta del proyecto.
"""

import json

import anthropic

from config import (
    API_KEY_FILE,
    DISEASE_GLOSSARY,
    INTERPRETATION_GLOSSARY,
    REVIEW_FILE
)
from extractors.table_extractor import make_issue


MODEL = "claude-opus-5-5"

GLOSSARIES = {
    "enfermedades": DISEASE_GLOSSARY,
    "interpretaciones": INTERPRETATION_GLOSSARY,
}

INSTRUCTIONS = {
    "enfermedades": (
        "Cada texto es el nombre de una enfermedad o fenotipo de OMIM, tal "
        "como figura en la tabla de un informe de microarray cromosómico. "
        "Traducí el nombre con la terminología médica en español que usa la "
        "genética clínica. Conservá sin cambios los símbolos de genes, los "
        "números y tipos (\"type IIE\" -> \"tipo IIE\") y los epónimos. No "
        "agregues ni quites información: si un nombre parece incompleto, "
        "traducí solo lo que está escrito."
    ),
    "interpretaciones": (
        "Cada texto es la interpretación clínica de una variante en el número "
        "de copias (CNV) de un informe de microarray cromosómico. Traducila "
        "al español con el registro de un informe de genética clínica. "
        "Conservá sin cambios los símbolos de genes, las regiones "
        "cromosómicas, las siglas y los números. No agregues, quites ni "
        "suavices ninguna afirmación."
    ),
}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "translations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "translation": {"type": "string"}
                },
                "required": ["index", "translation"],
                "additionalProperties": False
            }
        }
    },
    "required": ["translations"],
    "additionalProperties": False
}

# Si la API falla por un motivo que no se va a arreglar solo (sin key, key
# inválida), no se vuelve a intentar en el resto de la corrida.
_disabled_reason = None


def normalize(value):
    """
    Clave de búsqueda: sin distinguir mayúsculas ni espacios repetidos.
    """

    return " ".join(value.split()).lower()


def load_json(path, default):

    if not path.exists():
        return default

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):

    path.parent.mkdir(exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_api_key():
    """
    Key del archivo anthropic_api_key.txt, si existe. Si no, None y el
    SDK usa la variable de entorno ANTHROPIC_API_KEY.
    """

    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text(encoding="utf-8").strip() or None

    return None


def _build_system_prompt(kind, glossary):
    """
    Instrucciones más las traducciones ya revisadas como guía de estilo.
    """

    examples = [
        {"en": english, "es": spanish}
        for english, spanish in glossary.items()
        if spanish
    ]

    return (
        "Sos traductor médico del inglés al español para un laboratorio de "
        "genética de Argentina.\n\n"
        + INSTRUCTIONS[kind]
        + "\n\nRespondé con una traducción por cada texto, identificada por "
        "su índice.\n\nTraducciones ya aprobadas por el laboratorio; seguí "
        "su estilo y su terminología:\n"
        + json.dumps(examples, ensure_ascii=False, indent=1)
    )


def request_translations(kind, texts, glossary):
    """
    Pide a la API la traducción de una lista de textos.

    Devuelve (traducciones, error): un dict {texto: traducción} y, si
    falló, el motivo en texto (con el dict vacío).
    """

    global _disabled_reason

    if _disabled_reason:
        return {}, _disabled_reason

    try:

        client = anthropic.Anthropic(api_key=get_api_key(), timeout=120.0)

        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={
                "effort": "medium",
                "format": {
                    "type": "json_schema",
                    "schema": RESPONSE_SCHEMA
                }
            },
            system=_build_system_prompt(kind, glossary),
            messages=[{
                "role": "user",
                "content": json.dumps(
                    [
                        {"index": index, "text": text}
                        for index, text in enumerate(texts)
                    ],
                    ensure_ascii=False,
                    indent=1
                )
            }]
        )

    except (TypeError, anthropic.AuthenticationError) as error:

        # TypeError: el SDK no encontró ninguna credencial
        if isinstance(error, TypeError):
            _disabled_reason = (
                "no hay API key (variable ANTHROPIC_API_KEY o archivo "
                f"{API_KEY_FILE.name})"
            )
        else:
            _disabled_reason = "la API key no es válida"

        return {}, _disabled_reason

    except anthropic.PermissionDeniedError:

        _disabled_reason = "la API key no tiene permiso para usar el modelo"

        return {}, _disabled_reason

    except anthropic.RateLimitError:
        return {}, "se alcanzó el límite de uso de la API; reintentar más tarde"

    except anthropic.APIStatusError as error:
        return {}, f"error de la API ({error.status_code}): {error.message}"

    except anthropic.APIConnectionError:
        return {}, "no hay conexión con la API"

    if response.stop_reason != "end_turn":
        return {}, f"la API no completó la respuesta ({response.stop_reason})"

    data = json.loads(
        next(block.text for block in response.content if block.type == "text")
    )

    translations = {}

    for item in data["translations"]:

        if 0 <= item["index"] < len(texts) and item["translation"].strip():
            translations[texts[item["index"]]] = item["translation"].strip()

    return translations, None


def resolve_translations(kind, texts):
    """
    Traduce una lista de textos: primero con el glosario y, lo que falte,
    con la API.

    Parameters
    ----------
    kind : str
        "enfermedades" o "interpretaciones".

    texts : list
        Textos en inglés.

    Returns
    -------
    tuple
        (translations, issues)

        translations: dict {texto en inglés: traducción}. Los que no se
        pudieron traducir no están.
    """

    glossary_path = GLOSSARIES[kind]

    glossary = load_json(glossary_path, {})

    lookup = {
        normalize(english): spanish
        for english, spanish in glossary.items()
        if spanish
    }

    review = load_json(REVIEW_FILE, {})
    pending_review = {normalize(text) for text in review.get(kind, [])}

    translations = {}
    issues = []
    missing = []

    for text in dict.fromkeys(texts):

        if normalize(text) in lookup:
            translations[text] = lookup[normalize(text)]

        else:
            missing.append(text)

    # -----------------------------------------
    # Traducción automática de lo que falta
    # -----------------------------------------

    if missing:

        automatic, error = request_translations(kind, missing, glossary)

        if error:

            issues.append(make_issue(
                "AVISO",
                f"No se pudo traducir automáticamente: {error}."
            ))

        for text, translation in automatic.items():

            translations[text] = translation
            glossary[text] = translation
            pending_review.add(normalize(text))
            review.setdefault(kind, []).append(text)

        if automatic:

            save_json(glossary_path, glossary)
            save_json(REVIEW_FILE, review)

    # -----------------------------------------
    # Avisos
    # -----------------------------------------

    for text in dict.fromkeys(texts):

        if text not in translations:

            issues.append(make_issue(
                "AVISO",
                f"Sin traducción (queda en inglés): \"{text}\""
            ))

        elif normalize(text) in pending_review:

            issues.append(make_issue(
                "AVISO",
                f"Traducción automática sin revisar: \"{text}\" -> "
                f"\"{translations[text]}\""
            ))

    return translations, issues
