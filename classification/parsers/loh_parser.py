"""
loh_parser.py

Parser para los informes con ausencia de heterocigosidad (LOH).

Trabaja sobre el texto libre del informe:

    LOH (14 Mb - chr15:56,000,000-70,000,000) was detected. There is an
    increased risk for autosomal recessive disorders within this region of LOH.
    ...
    The OMIM genes included in the LOH region are AAGAB, ADAM10, ...
"""

import re


# Cada región: "(14 Mb - chr15:56,000,000-70,000,000)"
LOH_REGION_PATTERN = re.compile(
    r'\(\s*(?P<size>[\d.]+)\s*Mb\s*-\s*'
    r'(?P<chrom>chr\w+)\s*:\s*(?P<start>[\d,]+)\s*-\s*(?P<end>[\d,]+)\s*\)',
    re.IGNORECASE
)

# Lista de genes de la región (puede ocupar varias líneas).
LOH_GENES_PATTERN = re.compile(
    r'The\s+OMIM\s+genes\s+included\s+in\s+the\s+LOH\s+region\s+are\s+'
    r'(?P<genes>.+?)(?=The\s+OMIM\s+genes|\Z)',
    re.IGNORECASE | re.DOTALL
)

LOH_RISK_SENTENCE = (
    "There is an increased risk for autosomal recessive disorders "
    "within this region of LOH"
)


def parse_loh(text: str) -> dict:
    """
    Extrae las regiones LOH del informe.

    Returns
    -------
    dict
        {
            "regions": [
                {
                    "size_mb": "14",
                    "size": "14Mb",
                    "position": "chr15:56,000,000-70,000,000",
                    "genes": "AAGAB, ADAM10, ..."
                }
            ],
            "issues": ["..."]   # problemas detectados, en texto
        }
    """

    result = {
        "regions": [],
        "issues": []
    }

    if not text or "LOH" not in text:
        return result

    # El resumen llega hasta la tabla de la página siguiente.
    summary = " ".join(text.split("CytoBand Position", 1)[0].split())

    if not re.search(r"LOH\s*\(", summary):
        return result

    gene_lists = [
        ", ".join(
            gene.strip()
            for gene in " ".join(match.group("genes").split()).split(",")
            if gene.strip()
        )
        for match in LOH_GENES_PATTERN.finditer(text)
    ]

    for index, match in enumerate(LOH_REGION_PATTERN.finditer(summary)):

        start = int(match.group("start").replace(",", ""))
        end = int(match.group("end").replace(",", ""))

        position = (
            f"{match.group('chrom')}:"
            f"{match.group('start')}-{match.group('end')}"
        )

        genes = gene_lists[index] if index < len(gene_lists) else ""

        if not genes:

            result["issues"].append(
                f"{position}: no se encontró la lista de genes de la región LOH."
            )

        if abs((end - start) / 1_000_000 - float(match.group("size"))) > 0.5:

            result["issues"].append(
                f"{position}: el informe indica {match.group('size')} Mb pero "
                f"las coordenadas dan {(end - start) / 1_000_000:.1f} Mb."
            )

        result["regions"].append({
            "size_mb": match.group("size"),
            "size": f"{match.group('size')}Mb",
            "position": position,
            "genes": genes
        })

    if not result["regions"]:

        result["issues"].append(
            "El informe menciona LOH pero no se pudo leer la región."
        )

    if len(gene_lists) > len(result["regions"]):

        result["issues"].append(
            "Hay más listas de genes que regiones LOH."
        )

    # La interpretación del template es fija: avisar si el original dice otra cosa.
    if result["regions"] and LOH_RISK_SENTENCE.lower() not in summary.lower():

        result["issues"].append(
            "La interpretación del LOH no es la frase habitual; el informe "
            "generado usa la frase estándar, revisar."
        )

    return result


def loh_detection_phrase(region_count: int, end: str = ":") -> str:
    """
    "Se detectó una región con ausencia de heterocigosidad (LOH):"

    Con end="." es la frase que va en Resultado, antes de la tabla de
    LOH, en los informes que tienen CNV y LOH.
    """

    if region_count >= 2:

        return (
            f"Se detectaron {region_count} regiones con ausencia de "
            f"heterocigosidad (LOH){end}"
        )

    return f"Se detectó una región con ausencia de heterocigosidad (LOH){end}"
