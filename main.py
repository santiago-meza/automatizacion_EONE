from config import INPUT, OUTPUT, TEMPLATES

from extractors.text_extractor import extract_text
from classification.parsers.report_parser import parse_report
from classifier import select_template
from template_engine import generate_report

from extractors.table_extractor import extract_tables
from classification.parsers.cnv_table_parser import parse_cnv_tables

from generators.cnv_table import generate_cnv_table
from document_merger import insert_table_at_placeholder

from datetime import datetime


def main():

    pdf_files = sorted(INPUT.glob("*.pdf"))

    if not pdf_files:
        print("No se encontraron PDFs.")
        return


    # CNV table template
    cnv_table_template = TEMPLATES / "table_cnv.docx"

    # Temporary file for generated CNV table
    temp_cnv_table = OUTPUT / "temp_cnv_table.docx"


    for pdf in pdf_files:

        print("=" * 80)
        print(pdf.name)
        print("=" * 80)


        # =====================================
        # 1. Extract text
        # =====================================

        text = extract_text(pdf)


        # =====================================
        # 2. Parse report data
        # =====================================

        # 2. Parsear datos
        data = parse_report(text)

        # Keep full report text for classification
        data["TEXT"] = text


        # =====================================
        # 3. Extract CNV tables
        # =====================================

        tables = extract_tables(pdf)

        cnvs = parse_cnv_tables(tables)


        print(
            "CNVs encontrados:",
            len(cnvs)
        )


        # =====================================
        # 4. Select report template
        # =====================================

        template = select_template(data)


        today_filename = datetime.now().strftime("%d.%m.%Y")


        output_file = (
            OUTPUT /
            f"{data['PROTOCOL']} {data['PATIENT']} {today_filename}.docx"
        )


        # =====================================
        # 5. Generate main report
        # =====================================

        generate_report(
            template,
            output_file,
            data
        )


        # =====================================
        # 6. Generate CNV table
        # =====================================

        if cnvs:

            generate_cnv_table(
                cnv_table_template,
                cnvs,
                temp_cnv_table
            )


            # =================================
            # 7. Insert table into report
            # =================================

            insert_table_at_placeholder(
                output_file,
                temp_cnv_table,
                output_file
            )


        print("Generado:")
        print(output_file)
        print()



if __name__ == "__main__":
    main()