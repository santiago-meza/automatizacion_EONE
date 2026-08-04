from config import NEGATIVE_TEMPLATE


def select_template(data: dict):

    if data["NEGATIVE"]:
        return NEGATIVE_TEMPLATE

    raise ValueError(
        "No se pudo determinar el template correspondiente."
    )