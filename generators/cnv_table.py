from copy import deepcopy

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


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
        paragraph.add_run(str(text))


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

        if not associations:
            continue

        start_row = current_row

        # -----------------------------------------
        # Create one row per association
        # -----------------------------------------

        for assoc in associations:

            duplicate_row(table, template_row)

            row = table.rows[-1]

            write_cell(row.cells[3], assoc.get("disease", ""))
            write_cell(row.cells[4], assoc.get("inheritance", ""))
            write_cell(row.cells[5], assoc.get("gene", ""))

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