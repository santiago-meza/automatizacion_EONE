import pdfplumber
from pathlib import Path


PDF = Path("input/cnv_large.pdf")


def extract_tables(pdf_path):

    tables = []

    with pdfplumber.open(pdf_path) as pdf:

        print(f"Pages: {len(pdf.pages)}")

        for page_number, page in enumerate(pdf.pages, start=1):

            print(f"\n--- PAGE {page_number} ---")

            page_tables = page.extract_tables()

            print(f"Tables found: {len(page_tables)}")

            for table_number, table in enumerate(page_tables, start=1):

                print(f"\nTABLE {table_number}")

                for row in table:
                    print(row)

                tables.append(table)

    return tables


if __name__ == "__main__":

    extract_tables(PDF)