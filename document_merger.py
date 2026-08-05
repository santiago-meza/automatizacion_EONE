from docx import Document
from copy import deepcopy


def insert_table_at_placeholder(report_path, table_path, output_path):

    report = Document(report_path)
    table_doc = Document(table_path)

    placeholder = "{{ CNV_TABLE }}"

    inserted = False


    for paragraph in report.paragraphs:

        full_text = "".join(
            run.text
            for run in paragraph.runs
        )

        if placeholder in full_text:

            print("CNV_TABLE placeholder found")


            # Remove placeholder text
            for run in paragraph.runs:
                run.text = ""


            body = report._body._body

            index = list(body).index(
                paragraph._p
            )


            for element in table_doc.element.body:

                if element.tag.endswith("tbl"):

                    body.insert(
                        index + 1,
                        deepcopy(element)
                    )

                    index += 1


            inserted = True
            break


    if not inserted:
        raise ValueError(
            "Placeholder {{ CNV_TABLE }} not found in body."
        )


    report.save(output_path)