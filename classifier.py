from config import (
    NEGATIVE_TEMPLATE,
    POSITIVE_CNV_TEMPLATE,
    POSITIVE_LOH_TEMPLATE,
    POSITIVE_CNV_LOH_TEMPLATE
)


def select_template(data: dict):

    # Negative result
    if data.get("NEGATIVE"):
        return NEGATIVE_TEMPLATE


    text = data.get("TEXT", "").lower()

    has_cnv = "*duplication" in text or "*deletion" in text
    has_loh = bool(data.get("LOH_REGIONS"))


    # Positive CNV + LOH result
    if has_cnv and has_loh:
        return POSITIVE_CNV_LOH_TEMPLATE


    # Positive CNV result
    if has_cnv:
        return POSITIVE_CNV_TEMPLATE


    # Positive LOH result
    if has_loh:
        return POSITIVE_LOH_TEMPLATE


    raise ValueError(
        "No se pudo determinar el template correspondiente."
    )
