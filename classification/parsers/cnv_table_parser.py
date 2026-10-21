from collections import OrderedDict
import re


def clean(value):
    """
    Limpieza general de texto extraído del PDF.
    """

    if value is None:
        return ""

    value = str(value)

    # palabra partida con guion al final de la línea
    # Ej: "telomere-\nrelated" -> "telomere-related"
    value = re.sub(r"-\n(?=[a-z])", "-", value)

    # unir saltos de línea
    value = value.replace("\n", " ")

    # eliminar espacios múltiples
    value = re.sub(r"\s+", " ", value)

    return value.strip()



def clean_cytoband(value):
    """
    Corrige CytoBand partidas por salto de línea o leídas con
    espacios (una CytoBand nunca lleva espacios).
    Ej:
    5p15.33- 15.2 -> 5p15.33-15.2
    4p 1 6 .3-1 6 .2 -> 4p16.3-16.2
    """

    value = clean(value)

    return re.sub(r"\s+", "", value)



def clean_inheritance(value):
    """
    Normaliza herencia.

    No se adivinan valores: si la celda llega cortada o mezclada
    (ej: "Autosomal Autosomal") se deja tal cual para que lo
    detecte validate_cnvs().
    """

    return clean(value)



def parse_cnv_tables(tables):
    """
    Convierte tablas CNV extraídas del PDF
    en una estructura organizada por CNV.
    """

    cnvs = OrderedDict()

    current_cytoband = ""
    current_position = ""
    current_type = ""


    for table in tables:

        if not table:
            continue


        # eliminar encabezado repetido
        if table[0][0] == "CytoBand":
            rows = table[1:]

        else:
            rows = table


        for row in rows:

            if len(row) < 7:
                continue


            cytoband = clean_cytoband(row[0])
            position = clean(row[1])
            cnv_type = clean(row[2])

            disease = clean(row[3])
            inheritance = clean_inheritance(row[4])
            gene = clean(row[5])
            reference = clean(row[6])


            # mantener valores de celdas combinadas

            if cytoband:
                current_cytoband = cytoband

            if position:
                current_position = position

            if cnv_type:
                current_type = cnv_type


            if not disease:
                continue


            key = (
                current_cytoband,
                current_position,
                current_type
            )


            if key not in cnvs:

                cnvs[key] = {

                    "cytoband": current_cytoband,
                    "position": current_position,
                    "type": current_type,
                    "associations": []

                }


            cnvs[key]["associations"].append(
                {
                    "disease": disease,
                    "inheritance": inheritance,
                    "gene": gene,
                    "reference": reference
                }
            )


    return list(cnvs.values())