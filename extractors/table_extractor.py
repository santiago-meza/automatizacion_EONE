import statistics

import pdfplumber


CNV_HEADER = [
    "CytoBand",
    "Position",
    "Type",
    "Disease",
    "Inheritance",
    "Gene",
    "Reference"
]

# El generador del PDF nunca dibuja más de 3 líneas por celda:
# lo que no entra se pierde.
MAX_CELL_LINES = 3

# Desfasaje vertical (en puntos) a partir del cual se avisa.
OFFSET_TOLERANCE = 1.5

# Palabras con las que no suele terminar un nombre completo.
DANGLING_ENDINGS = ("and", "or", "with", "the", "due", ",", "-", "/")


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


def make_issue(level, message, page=None):
    """
    level: "ERROR" (el dato no es confiable), "AVISO" (revisar) o "INFO".
    """

    return {
        "level": level,
        "page": page,
        "message": message
    }


def _nearest_index(values, value):

    return min(
        range(len(values)),
        key=lambda i: abs(values[i] - value)
    )


def _unique_sorted(values, tolerance=1.0):

    result = []

    for value in sorted(values):

        if not result or value - result[-1] > tolerance:
            result.append(value)

    return result


def _words_to_text(words):
    """
    Une las palabras de una celda respetando sus líneas.
    Devuelve (texto, cantidad_de_lineas).
    """

    lines = []

    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):

        if lines and abs(word["top"] - lines[-1][0]["top"]) <= 3:
            lines[-1].append(word)
        else:
            lines.append([word])

    text = "\n".join(
        " ".join(w["text"] for w in sorted(line, key=lambda w: w["x0"]))
        for line in lines
    )

    return text, len(lines)


def _extract_cnv_table(page, table, page_number):
    """
    Reconstruye una tabla CNV a partir de la posición de cada palabra.

    En algunos informes el texto está dibujado unos puntos más abajo que
    la grilla, y pdfplumber termina mezclando el final de una fila con el
    comienzo de la siguiente. Acá se mide ese desfasaje con el encabezado
    y se corrige antes de asignar cada palabra a su celda.

    Devuelve (filas, issues) o (None, []) si la tabla no es de CNVs.
    """

    issues = []

    xs = _unique_sorted(cell[0] for cell in table.cells)
    ys = _unique_sorted(cell[1] for cell in table.cells)

    if len(xs) != len(CNV_HEADER):
        return None, []

    left, top, right, bottom = table.bbox

    header_bottom = min(
        cell[3] for cell in table.cells
        if abs(cell[1] - ys[0]) <= 1
    )

    words = [
        w for w in page.extract_words()
        if left <= (w["x0"] + w["x1"]) / 2 <= right
        and w["top"] >= top - 5
    ]

    # -----------------------------------------
    # Desfasaje vertical, medido en el encabezado
    # -----------------------------------------

    header_words = [
        w for w in words
        if w["text"] in CNV_HEADER
        and w["top"] <= header_bottom + (header_bottom - top)
    ]

    if "CytoBand" not in [w["text"] for w in header_words]:
        return None, []

    offset = statistics.median(
        (w["top"] + w["bottom"]) / 2 for w in header_words
    ) - (top + header_bottom) / 2

    if abs(offset) > OFFSET_TOLERANCE:

        issues.append(make_issue(
            "AVISO",
            f"El texto de la tabla está desfasado {offset:+.1f} pt respecto "
            "de la grilla (se corrigió al extraer).",
            page_number
        ))

    # -----------------------------------------
    # Asignar cada palabra a su celda
    # -----------------------------------------

    # Las celdas combinadas quedan en None, salvo en su primera fila.
    rows = [[None] * len(xs) for _ in ys]
    cell_words = {}

    for cell in table.cells:

        key = (_nearest_index(ys, cell[1]), _nearest_index(xs, cell[0]))

        rows[key[0]][key[1]] = ""
        cell_words[key] = []

    outside = []

    for word in words:

        x = (word["x0"] + word["x1"]) / 2
        y = (word["top"] + word["bottom"]) / 2 - offset

        for cell in table.cells:

            if cell[0] <= x <= cell[2] and cell[1] <= y <= cell[3]:

                key = (_nearest_index(ys, cell[1]), _nearest_index(xs, cell[0]))
                cell_words[key].append(word)
                break

        else:

            if bottom < y <= bottom + 15:
                outside.append(word)

    if outside:

        issues.append(make_issue(
            "ERROR",
            "Hay texto por debajo de la tabla que no entra en ninguna celda: "
            + " ".join(w["text"] for w in outside),
            page_number
        ))

    # -----------------------------------------
    # Armar el texto de cada celda y chequear
    # -----------------------------------------

    disease_col = CNV_HEADER.index("Disease")
    gene_col = CNV_HEADER.index("Gene")

    line_counts = {}

    for (r, c), cell_word_list in cell_words.items():
        rows[r][c], line_counts[(r, c)] = _words_to_text(cell_word_list)

    for (r, c), line_count in line_counts.items():

        if r == 0:
            continue

        text = rows[r][c]

        if c == disease_col and line_count >= MAX_CELL_LINES:

            flat = " ".join(text.replace("-\n", "-").split())

            if flat.lower().endswith(DANGLING_ENDINGS):

                issues.append(make_issue(
                    "ERROR",
                    f"Enfermedad cortada en el PDF (ocupa las {MAX_CELL_LINES} "
                    f"líneas de la celda y queda inconclusa): \"{flat}\"",
                    page_number
                ))

            else:

                issues.append(make_issue(
                    "INFO",
                    f"Enfermedad que ocupa las {MAX_CELL_LINES} líneas de la "
                    f"celda; si el nombre real es más largo, está cortado: "
                    f"\"{flat}\"",
                    page_number
                ))

        if c == gene_col and line_count != 1:

            if line_count > 1 or rows[r][disease_col]:

                issues.append(make_issue(
                    "AVISO",
                    f"Fila {r}: se esperaba un gen por fila y hay "
                    f"{line_count} líneas (\"{' '.join(text.split())}\"). "
                    "Las filas pueden estar mezcladas.",
                    page_number
                ))

    return rows, issues


def extract_cnv_tables(pdf_path):
    """
    Extrae las tablas de CNVs (CytoBand | Position | Type | Disease |
    Inheritance | Gene | Reference) corrigiendo el desfasaje entre el
    texto y la grilla, y reporta los problemas detectados.

    Returns
    -------
    tuple
        (tables, issues)

        tables: mismo formato que extract_tables(), solo tablas CNV.
        issues: lista de dicts {"level", "page", "message"}.
    """

    tables = []
    issues = []

    with pdfplumber.open(pdf_path) as pdf:

        for page_number, page in enumerate(pdf.pages, start=1):

            for table in page.find_tables():

                rows, table_issues = _extract_cnv_table(
                    page,
                    table,
                    page_number
                )

                if rows is None:
                    continue

                tables.append(rows)
                issues.extend(table_issues)

    return tables, issues
