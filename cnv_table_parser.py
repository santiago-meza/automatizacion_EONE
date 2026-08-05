def clean_cell(value):
    """
    Cleans text extracted from PDF cells.
    Keeps the content but removes line breaks caused by wrapping.
    """

    if value is None:
        return ""

    return " ".join(str(value).split())


def parse_cnv_tables(tables):
    """
    Parses CNV tables extracted with pdfplumber.

    Expected columns:
    CytoBand | Position | Type | Disease | Inheritance | Gene | Reference

    Returns:
    [
        {
            "cytoband": "",
            "position": "",
            "type": "",
            "associations": [
                {
                    "disease": "",
                    "inheritance": "",
                    "gene": "",
                    "reference": ""
                }
            ]
        }
    ]
    """

    cnvs = []

    current_cnv = None

    for table in tables:

        if not table:
            continue

        # Skip tables without CNV header
        header = table[0]

        if not header:
            continue

        if "CytoBand" not in header:
            continue


        for row in table[1:]:

            if len(row) < 7:
                continue


            cytoband = clean_cell(row[0])
            position = clean_cell(row[1])
            cnv_type = clean_cell(row[2])

            disease = clean_cell(row[3])
            inheritance = clean_cell(row[4])
            gene = clean_cell(row[5])
            reference = clean_cell(row[6])


            # New CNV detected
            if cytoband or position or cnv_type:

                current_cnv = {
                    "cytoband": cytoband,
                    "position": position,
                    "type": cnv_type,
                    "associations": []
                }

                cnvs.append(current_cnv)


            # Safety check
            if current_cnv is None:
                continue


            # Add association
            if disease or gene:

                current_cnv["associations"].append(
                    {
                        "disease": disease,
                        "inheritance": inheritance,
                        "gene": gene,
                        "reference": reference
                    }
                )


    return cnvs