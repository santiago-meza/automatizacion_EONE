from config import (
    NEGATIVE_TEMPLATE,
    POSITIVE_CNV_TEMPLATE
)


def select_template(data: dict):

    # Negative result
    if data.get("NEGATIVE"):
        return NEGATIVE_TEMPLATE


    # Positive CNV result
    text = data.get("TEXT", "").lower()


    if "*duplication" in text or "*deletion" in text:
        return POSITIVE_CNV_TEMPLATE


    raise ValueError(
        "No se pudo determinar el template correspondiente."
    )