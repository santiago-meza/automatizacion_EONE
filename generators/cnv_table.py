from copy import deepcopy

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn


# Una CNV con más asociaciones que esto no se lista en la tabla:
# se muestra una sola fila con "Ver informe original"
MAX_ASSOCIATIONS = 6

TOO_MANY_ASSOCIATIONS_TEXT = "Ver informe original"


# =====================================================
# AUXILIARY FUNCTIONS
# =====================================================

def duplicate_row(table, row):
    """
    Duplicate a table row preserving all formatting.
    """
    new_row = deepcopy(row._tr)
    table._tbl.append(new_row)


def write_cell(cell, text):
    """
    Write text preserving the formatting of the template.
    """
    paragraph = cell.paragraphs[0]

    if paragraph.runs:
        paragraph.runs[0].text = str(text)

        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        run = paragraph.add_run(str(text))

        # La fila vacía del template no tiene runs: el formato (tamaño de
        # letra) está en la marca de párrafo y hay que copiarlo al run.
        paragraph_properties = paragraph._p.pPr

        mark_format = (
            paragraph_properties.find(qn("w:rPr"))
            if paragraph_properties is not None
            else None
        )

        if mark_format is not None:

            run_format = deepcopy(mark_format)

            # el resaltado del template es solo una marca de edición
            for highlight in run_format.findall(qn("w:highlight")):
                run_format.remove(highlight)

            run._r.insert(0, run_format)


def collapse_long_cnvs(cnvs):
    """
    Marca los CNVs con más de MAX_ASSOCIATIONS asociaciones: se les
    quitan las asociaciones (así no se validan ni se traducen) y en la
    tabla se muestran como una sola fila con "Ver informe original".
    """

    return [
        {**cnv, "associations": [], "too_many_associations": True}
        if len(cnv.get("associations", [])) > MAX_ASSOCIATIONS
        else cnv
        for cnv in cnvs
    ]


def center_cell(cell):
    """
    Center a cell vertically and horizontally.
    """
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    for paragraph in cell.paragraphs:
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER


def merge_vertical(table, column, start_row, end_row):
    """
    Merge cells vertically in a single column.
    """

    if start_row == end_row:
        center_cell(table.cell(start_row, column))
        return

    merged = table.cell(start_row, column).merge(
        table.cell(end_row, column)
    )

    center_cell(merged)


# =====================================================
# CNV TABLE GENERATOR
# =====================================================

def generate_cnv_table(template_path, cnvs, output_path):
    """
    Generates a CNV Word table from parsed CNV data.

    Parameters
    ----------
    template_path : str | Path
        Word template containing:
            - Header row
            - Empty formatting row

    cnvs : list
        Output of parse_cnv_tables().

    output_path : str | Path
        Destination DOCX.
    """

    doc = Document(template_path)

    if not doc.tables:
        raise ValueError("The template does not contain any tables.")

    table = doc.tables[0]

    # Row 0 -> Header
    # Row 1 -> Empty template row

    if len(table.rows) < 2:
        raise ValueError(
            "The template must contain a header row and one empty template row."
        )

    template_row = table.rows[1]

    # Remove the empty template row
    table._tbl.remove(template_row._tr)

    current_row = 1

    for cnv in cnvs:

        associations = cnv.get("associations", [])

        # Demasiadas enfermedades para la tabla: una sola fila que
        # remite al informe original
        if cnv.get("too_many_associations"):
            associations = [{"disease": TOO_MANY_ASSOCIATIONS_TEXT}]

        if not associations:
            continue

        start_row = current_row

        # -----------------------------------------
        # Create one row per association
        # -----------------------------------------

        for assoc in associations:

            duplicate_row(table, template_row)

            row = table.rows[-1]

            values = [
                assoc.get("disease", ""),
                assoc.get("inheritance", ""),
                assoc.get("gene", "")
            ]

            # CNV sin enfermedades asociadas: un solo "-" que ocupa
            # Enfermedad, Herencia y Gen
            if values[0] == TOO_MANY_ASSOCIATIONS_TEXT:

                write_cell(row.cells[3], TOO_MANY_ASSOCIATIONS_TEXT)

                center_cell(row.cells[3].merge(row.cells[5]))

            elif all(value in ("-", "") for value in values):

                write_cell(row.cells[3], "-")

                center_cell(row.cells[3].merge(row.cells[5]))

            else:

                write_cell(row.cells[3], values[0])
                write_cell(row.cells[4], values[1])
                write_cell(row.cells[5], values[2])

            current_row += 1

        end_row = current_row - 1

        # -----------------------------------------
        # Fill CNV information
        # -----------------------------------------

        write_cell(table.cell(start_row, 0), cnv.get("cytoband", ""))
        write_cell(table.cell(start_row, 1), cnv.get("position", ""))
        write_cell(table.cell(start_row, 2), cnv.get("type", ""))

        # -----------------------------------------
        # Merge repeated columns
        # -----------------------------------------

        merge_vertical(table, 0, start_row, end_row)
        merge_vertical(table, 1, start_row, end_row)
        merge_vertical(table, 2, start_row, end_row)

    doc.save(output_path)