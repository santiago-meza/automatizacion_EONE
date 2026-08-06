import pdfplumber
from config import INPUT

pdf_path = INPUT / "cnv_2.pdf"

def extract_tables(pdf_path):
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            for table in page_tables:
                tables.append(table)
    return tables

tables = extract_tables(pdf_path)
print(tables)
