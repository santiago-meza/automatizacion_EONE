from pathlib import Path
import pdfplumber


def extract_text(pdf_path: Path) -> str:
    """
    Extrae todo el texto del PDF.
    """

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text.replace("\xa0", " ").strip()