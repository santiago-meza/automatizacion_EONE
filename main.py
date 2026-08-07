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
        def parse_position(position: str):
            # "chr2:140659-638144"
            # devuelve ("chr2", 140659, 638144)
            chrom, rest = position.split(":")
            start_s, end_s = rest.split("-")
            return chrom, int(start_s), int(end_s)

        def type_to_variant_type(cnv_type: str):
            # "AMP(X3)" -> duplication
            # "DEL(X1)" -> deletion
            t = (cnv_type or "").upper()
            if t.startswith("DEL"):
                return "deletion"
            if t.startswith("AMP"):
                return "duplication"
            # fallback
            return ""

        def type_to_copy_number(cnv_type: str):
            # "AMP(X3)" -> "3"
            import re
            m = re.search(r"\(X(\d+)\)", cnv_type or "")
            return m.group(1) if m else ""

        variants = []
        for cnv in cnvs or []:
            chromosome, coord_start, coord_end = parse_position(cnv.get("position", ""))
            variant_type = type_to_variant_type(cnv.get("type", ""))
            copy_number = type_to_copy_number(cnv.get("type", ""))

            # size_mb aproximado por tamaño en bp
            size_bp = abs(coord_end - coord_start)
            size_mb = round(size_bp / 1_000_000, 3)

            variants.append({
                "variant_type": variant_type,
                "copy_number": copy_number,
                "size_mb": size_mb,
                "chromosome": chromosome,
                "coord_start": coord_start,
                "coord_end": coord_end,
                "region": cnv.get("cytoband", ""),
                # IMPORTANTE: por ahora no veo "classification" en tu sample.
                # Si tu parser mete clasificación en algún campo, cámbialo aquí.
                "classification": "",
            })

        data["CNV_INTERPRETATIONS_PARSED"] = {"variants": variants}

        print("variants built:", len(variants))
        print("first built variant:", variants[:1])


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