import re


def parse_report(text: str) -> dict:
    """
    Extrae los datos necesarios del informe.

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
        "RESULTADO": ""
    }

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # ----------------------------------------------------
    # Paciente + sexo
    # Ejemplo:
    # HOPPE ISABELLA IRIEL Female
    # ----------------------------------------------------
    if lines:
        match = re.match(r"(.+?)\s+(Male|Female)$", lines[0])

        if match:
            data["PATIENT"] = match.group(1)
            data["SEX"] = match.group(2)

    # ----------------------------------------------------
    # Protocolo
    # Ejemplo:
    # D2637601 24-Jun-2026 2021-03-18
    # ----------------------------------------------------
    protocol_match = re.search(r"\b([AD]\d{7})\b", text)

    if protocol_match:
        data["PROTOCOL"] = protocol_match.group(1)

    # ----------------------------------------------------
    # Fecha del informe
    # Ejemplo:
    # GENDA Pilar Igarreta 03-Jul-2026
    # ----------------------------------------------------
    date_match = re.search(
        r"GENDA\s+Pilar\s+Igarreta\s+(\d{2}-[A-Za-z]{3}-\d{4})",
        text
    )

    if date_match:
        data["DATE"] = date_match.group(1)

    # ----------------------------------------------------
    # Resultado negativo
    # ----------------------------------------------------
    if "According to the CMA result" in text:

        if "arr[GRCh37](X,Y)x1, (1-22)x2" in text:

            data["NEGATIVE"] = True
            data["RESULTADO"] = "(arr(X,Y)x1, (1-22)x2)"

        elif "arr[GRCh37](X)x2, (1-22)x2" in text:

            data["NEGATIVE"] = True
            data["RESULTADO"] = "(arr(X)x2, (1-22)x2)"

    return data