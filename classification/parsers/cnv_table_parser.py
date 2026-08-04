from collections import OrderedDict


def clean(value):
    """Convierte None en '' y elimina saltos de línea."""
    if value is None:
        return ""

    return str(value).replace("\n", " ").strip()


def parse_cnv_tables(tables):

    cnvs = OrderedDict()

    last_cytoband = ""
    last_position = ""
    last_type = ""

    for table in tables:

        if not table:
            continue

        # Saltar encabezado
        rows = table[1:]

        for row in rows:

            # Ignorar filas incompletas
            if len(row) < 7:
                continue

            cytoband = clean(row[0])
            position = clean(row[1])
            cnv_type = clean(row[2])
            disease = clean(row[3])
            inheritance = clean(row[4])
            gene = clean(row[5])
            reference = clean(row[6])

            # Heredar valores de celdas combinadas
            if cytoband:
                last_cytoband = cytoband

            if position:
                last_position = position

            if cnv_type:
                last_type = cnv_type

            if not disease:
                continue

            key = (
                last_cytoband,
                last_position,
                last_type
            )

            if key not in cnvs:

                cnvs[key] = {
                    "cytoband": last_cytoband,
                    "position": last_position,
                    "type": last_type,
                    "entries": []
                }

            cnvs[key]["entries"].append(
                {
                    "disease": disease,
                    "inheritance": inheritance,
                    "gene": gene,
                    "reference": reference
                }
            )

    return list(cnvs.values())