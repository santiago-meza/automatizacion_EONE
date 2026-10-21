"""
interpretacion_cnv_parser.py

Parser para extraer las variantes CNV individuales (bullets) junto con su
texto interpretativo asociado y las referencias del informe original.

Este parser trabaja sobre el texto libre del informe (no las tablas),
específicamente sobre el bloque que contiene las líneas:
    *deletion(X1) of 0.52 MB (chr15:22,759,530-23,279,684) in the 15q11.2 region, Pathogenic
    <texto interpretativo opcional>
    References:
    <urls>
"""

import re


# ----------------------------------------------------
# Patrones
# ----------------------------------------------------

# Detecta cada línea de variante y captura sus componentes.
CNV_LINE_PATTERN = re.compile(
    r'\*\s*(?P<type>deletion|duplication)\s*\(\s*X\s*(?P<copy>\d+)\s*\)\s+'
    r'of\s+(?P<size>[\d.]+)\s*MB\s+'
    r'\(\s*(?P<chrom>chr\w+)\s*:\s*(?P<start>[\d,]+)\s*-\s*(?P<end>[\d,]+)\s*\)\s+'
    r'in\s+the\s+(?P<region>[\w.\-]+)\s+region\s*,\s*'
    r'(?P<classification>[^\n\r]+)',
    re.IGNORECASE
)

# Detecta el inicio del bloque de referencias (para saber dónde cortar
# el texto interpretativo de la última variante).
REFERENCES_PATTERN = re.compile(
    r'References?\s*:',
    re.IGNORECASE
)

# Detecta URLs individuales dentro del bloque de referencias.
URL_PATTERN = re.compile(
    r'https?://\S+'
)

# Referencias sueltas del tipo "OMIM: 617751".
OMIM_REFERENCE_PATTERN = re.compile(
    r'^OMIM:\s*\S.*$',
    re.MULTILINE
)

# Frase de LOH que puede venir después de las variantes (informes con
# CNV y LOH). La procesa loh_parser, no es interpretación de un CNV.
LOH_SENTENCE_PATTERN = re.compile(
    r'LOH\s*\([^)]*\)\s*(?:was|were)\s+detected\.'
    r'(?:\s*There\s+is\s+an\s+increased\s+risk.*?LOH\.)?',
    re.IGNORECASE | re.DOTALL
)


# ----------------------------------------------------
# Helpers
# ----------------------------------------------------

def _clean_text(value: str) -> str:
    """
    Limpieza básica de texto: colapsa espacios/saltos de línea múltiples
    y remueve espacios al inicio/fin.
    """
    if not value:
        return ""

    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _clean_classification(value: str) -> str:
    """
    Limpia la clasificación extraída (ej: 'Pathogenic', 'Non-Pathogenic', 'VUS').
    A veces puede venir con espacios extra o algún caracter residual.
    """
    value = _clean_text(value)

    # Remueve posible punto final u otros caracteres residuales
    value = value.rstrip(".")

    return value


def _extract_references_block(text: str) -> tuple[str, list[str]]:
    """
    Separa el texto en (texto_sin_referencias, lista_de_urls).

    Busca la primera aparición de 'References:' y todo lo que sigue
    se considera bloque de referencias. Si no se encuentra, se asume
    que no hay referencias y se devuelve el texto completo + lista vacía.
    """
    match = REFERENCES_PATTERN.search(text)

    if not match:
        return text, []

    main_text = text[:match.start()]
    references_block = text[match.end():]

    urls = URL_PATTERN.findall(references_block)

    return main_text, urls


# ----------------------------------------------------
# Parser principal
# ----------------------------------------------------

def parse_cnv_interpretations(text: str) -> dict:
    """
    Extrae las variantes CNV individuales (con su interpretación)
    y las referencias del bloque de texto libre del informe original.

    Parameters
    ----------
    text : str
        Texto extraído del PDF (el mismo que recibe parse_report).

    Returns
    -------
    dict
        {
            "variants": [
                {
                    "variant_type": "deletion",
                    "copy_number": 1,
                    "size_mb": 0.52,
                    "chromosome": "chr15",
                    "coord_start": "22,759,530",
                    "coord_end": "23,279,684",
                    "region": "15q11.2",
                    "classification": "Pathogenic",
                    "interpretation_en": "The deletion is likely to cause pathogenic phenotypes."
                },
                ...
            ],
            "references": [
                "https://pmc.ncbi.nlm.nih.gov/articles/PMC4346944/",
                ...
            ]
        }
    """

    result = {
        "variants": [],
        "references": []
    }

    if not text:
        return result

    # Separamos el texto principal (bullets + interpretaciones) del
    # bloque de referencias, y capturamos las URLs.
    main_text, references = _extract_references_block(text)
    result["references"] = references

    # Si no hay referencias, el texto sigue con la tabla de la página
    # siguiente: se corta ahí para que no entre en la interpretación.
    main_text = main_text.split("CytoBand Position", 1)[0]

    # Referencias OMIM y frase de LOH: no son parte de la interpretación.
    result["references"] = (
        [" ".join(ref.split()) for ref in OMIM_REFERENCE_PATTERN.findall(main_text)]
        + result["references"]
    )

    main_text = OMIM_REFERENCE_PATTERN.sub("", main_text)
    main_text = LOH_SENTENCE_PATTERN.sub("", main_text)

    # Encontramos todas las coincidencias de líneas de variante,
    # junto con su posición en el texto, para poder extraer el
    # texto interpretativo entre una variante y la siguiente.
    matches = list(CNV_LINE_PATTERN.finditer(main_text))

    for i, match in enumerate(matches):

        variant_type = match.group("type").lower()
        copy_number = int(match.group("copy"))
        size_mb = float(match.group("size"))
        chromosome = match.group("chrom")
        coord_start = match.group("start")
        coord_end = match.group("end")
        region = match.group("region")
        classification = _clean_classification(match.group("classification"))

        # El texto interpretativo va desde el final de esta coincidencia
        # hasta el inicio de la siguiente variante (o hasta el final del
        # texto principal, si es la última variante).
        start_interpretation = match.end()

        if i + 1 < len(matches):
            end_interpretation = matches[i + 1].start()
        else:
            end_interpretation = len(main_text)

        interpretation_raw = main_text[start_interpretation:end_interpretation]
        interpretation_en = _clean_text(interpretation_raw)

        result["variants"].append({
            "variant_type": variant_type,
            "copy_number": copy_number,
            "size_mb": size_mb,
            # tal cual figura en el informe (ej: "0.50")
            "size_text": match.group("size"),
            "chromosome": chromosome,
            "coord_start": coord_start,
            "coord_end": coord_end,
            "region": region,
            "classification": classification,
            "interpretation_en": interpretation_en
        })

    return result
