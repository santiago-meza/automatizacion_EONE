import re
from copy import deepcopy

from classification.parsers.auto_translator import resolve_translations


TYPE_ES = {
    "AMP": "Duplicación",
    "DEL": "Deleción",
}

INHERITANCE_ES = {
    "-": "-",
    "Autosomal dominant": "Autosómica dominante",
    "Autosomal recessive": "Autosómica recesiva",
    "X-linked": "Ligada al X",
    "X-linked dominant": "Ligada al X dominante",
    "X-linked recessive": "Ligada al X recesiva",
    "Y-linked": "Ligada al Y",
    "Pseudoautosomal dominant": "Pseudoautosómica dominante",
    "Pseudoautosomal recessive": "Pseudoautosómica recesiva",
    "Digenic dominant": "Digénica dominante",
    "Digenic recessive": "Digénica recesiva",
    "Mitochondrial": "Mitocondrial",
    "Multifactorial": "Multifactorial",
    "Isolated cases": "Casos aislados",
    "Somatic mutation": "Mutación somática",
    "Somatic mosaicism": "Mosaicismo somático",
    "Inherited chromosomal imbalance": "Desequilibrio cromosómico heredado",
}


def translate_type(value):
    """
    "AMP(X3)" -> "Duplicación x3"
    "DEL(X1)" -> "Deleción x1"

    Si el formato no se reconoce se deja el valor original.
    """

    match = re.match(r"^(AMP|DEL)\(X(\d+)\)$", value)

    if not match:
        return value

    return f"{TYPE_ES[match.group(1)]} x{match.group(2)}"


def translate_inheritance(value):
    """
    Traduce la herencia. Una celda puede traer varios modos separados
    por coma. Si alguno no se reconoce (ej: celda cortada) se deja la
    celda original completa.
    """

    modes = [mode.strip() for mode in value.split(",")]

    if not all(mode in INHERITANCE_ES for mode in modes):
        return value

    return ", ".join(INHERITANCE_ES[mode] for mode in modes)


def translate_cnvs(cnvs):
    """
    Devuelve una copia de los CNVs con tipo, enfermedad y herencia en español.

    Las enfermedades se traducen con el glosario translations/enfermedades.json
    y, las que no están, con traducción automática (queda guardada en el
    glosario y marcada para revisar). Si no se puede, quedan en inglés.

    Returns
    -------
    tuple
        (cnvs_traducidos, issues)
    """

    translated = deepcopy(cnvs)

    diseases = [
        assoc["disease"]
        for cnv in translated
        for assoc in cnv.get("associations", [])
        if assoc.get("disease") and assoc["disease"] != "-"
    ]

    translations, issues = resolve_translations("enfermedades", diseases)

    for cnv in translated:

        cnv["type"] = translate_type(cnv.get("type", ""))

        for assoc in cnv.get("associations", []):

            assoc["inheritance"] = translate_inheritance(
                assoc.get("inheritance", "")
            )

            assoc["disease"] = translations.get(
                assoc.get("disease", ""),
                assoc.get("disease", "")
            )

    return translated, issues
