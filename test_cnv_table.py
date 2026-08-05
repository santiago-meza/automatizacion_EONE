import json

from config import INPUT, OUTPUT, TEMPLATES
from generators.cnv_table import generate_cnv_table


TEMPLATE = TEMPLATES / "table_cnv.docx"

JSON_FILE = INPUT / "cnv_example.json"

OUTPUT_FILE = OUTPUT / "cnv_test.docx"


with open(JSON_FILE, encoding="utf-8") as f:
    cnvs = json.load(f)


generate_cnv_table(
    TEMPLATE,
    cnvs,
    OUTPUT_FILE
)

print("CNV table generated successfully.")