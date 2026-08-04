from config import INPUT, OUTPUT
from extractor import extract_text
from parser import parse_report
from classifier import select_template
from template_engine import generate_report
from datetime import datetime


def main():

    pdf_files = sorted(INPUT.glob("*.pdf"))

    if not pdf_files:
        print("No se encontraron PDFs.")
        return


    for pdf in pdf_files:

        print("=" * 80)
        print(pdf.name)
        print("=" * 80)


        # 1. Extraer texto
        text = extract_text(pdf)


        # 2. Parsear datos
        data = parse_report(text)


        # 3. Seleccionar template
        template = select_template(data)


        # Fecha para nombre del archivo
        today_filename = datetime.now().strftime("%d.%m.%Y")


        # Nombre final
        output_file = (
            OUTPUT /
            f"{data['PROTOCOL']} {data['PATIENT']} {today_filename}.docx"
        )


        # Generar informe
        generate_report(
            template,
            output_file,
            data
        )


        print("Generado:")
        print(output_file)
        print()


if __name__ == "__main__":
    main()