from pathlib import Path

BASE_DIR = Path(__file__).parent

INPUT = BASE_DIR / "input"
OUTPUT = BASE_DIR / "output"
TEMPLATES = BASE_DIR / "templates"

NEGATIVE_TEMPLATE = TEMPLATES / "negativo.docx"

POSITIVE_CNV_TEMPLATE = TEMPLATES / "positivo_cnv.docx"