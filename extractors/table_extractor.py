import pdfplumber


def extract_tables(pdf_path):
    """
    Extrae todas las tablas encontradas en un PDF.

    Parameters
    ----------
    pdf_path : str or Path
        Ruta del PDF.

    Returns
    -------
    list
        Lista de tablas. Cada tabla es una lista de filas.
    """

    tables = []

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_tables = page.extract_tables()

            for table in page_tables:
                tables.append(table)

    return tables