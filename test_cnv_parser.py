from extractors.table_extractor import extract_tables
from classification.parsers.cnv_table_parser import parse_cnv_tables


PDF = "input/cnv_large.pdf"


tables = extract_tables(PDF)


cnvs = parse_cnv_tables(tables)


print("\n====================")
print("CNVs FOUND:", len(cnvs))
print("====================\n")


for i, cnv in enumerate(cnvs, start=1):

    print(f"CNV {i}")
    print("----------------")
    print("CytoBand:", cnv["cytoband"])
    print("Position:", cnv["position"])
    print("Type:", cnv["type"])

    print("\nAssociations:")

    for assoc in cnv["associations"]:
        print(
            "-",
            assoc["gene"],
            "|",
            assoc["disease"],
            "|",
            assoc["inheritance"],
            "|",
            assoc["reference"]
        )

    print("\n")