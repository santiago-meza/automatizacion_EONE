import re


def parse_report(text: str, tables=None) -> dict:
    """
    Extrae los datos necesarios del informe.

    Parameters
    ----------
    text : str
        Texto extraído del PDF.

    tables : list, optional
        Tablas extraídas del PDF.

    Returns
    -------
    dict
        Diccionario con los datos del paciente y del informe.
    """

    data = {
        "PATIENT": "",
        "SEX": "",
        "PROTOCOL": "",
        "DATE": "",
        "NEGATIVE": False,
        "RESULTADO": "",
        "CNVS": []
    }

    lines = [line.strip() for line in text.splitlines() if line.strip()]


    # ----------------------------------------------------
    # Paciente + sexo
    # ----------------------------------------------------

    if lines:

        match = re.match(
            r"(.+?)\s+(Male|Female)$",
            lines[0]
        )

        if match:
            # "PEREZ,JUAN CARLOS" -> "PEREZ JUAN CARLOS"
            data["PATIENT"] = " ".join(
                match.group(1).replace(",", " ").split()
            )
            data["SEX"] = match.group(2)

    # Formato EDGC:
    # "Examinee Name ZABALA,JULIA Gender Unknown"
    if not data["PATIENT"]:

        match = re.search(
            r"Examinee\s+Name\s+(.+?)\s+Gender\s+(\w+)",
            text
        )

        if match:
            data["PATIENT"] = " ".join(
                match.group(1).replace(",", " ").split()
            )
            data["SEX"] = match.group(2)



    # ----------------------------------------------------
    # Protocolo
    # ----------------------------------------------------

    protocol_match = re.search(
        r"\b([AD]\d{7})\b",
        text
    )

    if protocol_match:
        data["PROTOCOL"] = protocol_match.group(1)



    # ----------------------------------------------------
    # Fecha del informe
    # ----------------------------------------------------

    date_match = re.search(
        r"GENDA\s+Pilar\s+Igarreta\s+(\d{2}-[A-Za-z]{3}-\d{4})",
        text
    )

    if date_match:
        data["DATE"] = date_match.group(1)

    else:
        # Formato EDGC: "Report Date 2026-Oct-29"
        date_match = re.search(
            r"Report\s+Date\s+(\d{4}-[A-Za-z]{3}-\d{2})",
            text
        )

        if date_match:
            data["DATE"] = date_match.group(1)



    # ----------------------------------------------------
    # Resultado negativo
    # ----------------------------------------------------

    # El cariotipo puede venir cortado en dos líneas:
    # "arr[GRCh37](X,Y)x1," + "(1-22)x2."
    flat_text = " ".join(text.split())

    if "According to the CMA result" in flat_text:

        if "arr[GRCh37](X,Y)x1, (1-22)x2" in flat_text:

            data["NEGATIVE"] = True
            data["RESULTADO"] = "(arr(X,Y)x1, (1-22)x2)"


        elif "arr[GRCh37](X)x2, (1-22)x2" in flat_text:

            data["NEGATIVE"] = True
            data["RESULTADO"] = "(arr(X)x2, (1-22)x2)"



    # ----------------------------------------------------
    # Resultado CNV
    # ----------------------------------------------------

    if tables:

        from parsers.cnv_table_parser import parse_cnv_tables

        cnvs = parse_cnv_tables(tables)

        if cnvs:
            data["CNVS"] = cnvs

    # 1) RESULTADO_VARIANTES_PATOGENICAS
    # Se completa en el pipeline con las clasificaciones de las variantes
    # (pathogenic_result_phrase); acá queda el valor por defecto.
    data["RESULTADO_VARIANTES_PATOGENICAS"] = pathogenic_result_phrase([])

    # 2) CNV_DETECCION_PHRASE (plural vs singular)
    cnv_count = len(re.findall(r"\*(deletion|duplication)\s*\(", text, flags=re.IGNORECASE))

    # if you prefer: fall back to parsed CNVS when present
    if cnv_count == 0 and data.get("CNVS"):
        cnv_count = len(data["CNVS"])

    # "Se detectaron dos variantes en el número de copias (CNV):"
    number_words = {
        2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis",
        7: "siete", 8: "ocho", 9: "nueve", 10: "diez"
    }

    data["CNV_DETECCION_PHRASE"] = (
        f"Se detectaron {number_words.get(cnv_count, cnv_count)} "
        "variantes en el número de copias (CNV):"
        if cnv_count >= 2
        else "Se detectó una variante en el número de copias (CNV):"
    )


    return data


def pathogenic_result_phrase(classifications) -> str:
    """
    Frase del resultado según la clasificación de cada variante:

        ["Non-Pathogenic", "Pathogenic"] -> "Se hallaron Variantes Patogénicas."
        ["VUS"]                          -> "No se hallaron Variantes Patogénicas."

    No se busca "pathogenic" en el texto del informe: la interpretación de
    una VUS puede decir "Pathogenic variants ... involving PRODH ...".
    """

    for classification in classifications:

        c = " ".join((classification or "").lower().replace("-", " ").split())

        if c in ("pathogenic", "likely pathogenic"):
            return "Se hallaron Variantes Patogénicas."

    return "No se hallaron Variantes Patogénicas."
