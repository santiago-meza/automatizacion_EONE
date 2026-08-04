import json

from extractors.table_extractor import extract_tables
from classification.parsers.cnv_table_parser import parse_cnv_tables


PDF = "input/cnv_large.pdf"

OUTPUT = "output/cnv_result.json"


tables = extract_tables(PDF)

cnvs = parse_cnv_tables(tables)


with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        cnvs,
        f,
        indent=4,
        ensure_ascii=False
    )


print(f"Saved {len(cnvs)} CNVs")