from pathlib import Path

BASE_DIR = Path(__file__).parent

INPUT = BASE_DIR / "input"
OUTPUT = BASE_DIR / "output"
TEMPLATES = BASE_DIR / "templates"

NEGATIVE_TEMPLATE = TEMPLATES / "negativo.docx"

POSITIVE_CNV_TEMPLATE = TEMPLATES / "positivo_cnv.docx"

POSITIVE_LOH_TEMPLATE = TEMPLATES / "LOH.docx"

# Informes con CNVs y LOH a la vez
POSITIVE_CNV_LOH_TEMPLATE = TEMPLATES / "positivo_cnv_loh.docx"

# Glosario de enfermedades inglés -> español para la tabla de CNVs
DISEASE_GLOSSARY = BASE_DIR / "translations" / "enfermedades.json"

# Glosario de interpretaciones (texto libre) inglés -> español
INTERPRETATION_GLOSSARY = BASE_DIR / "translations" / "interpretaciones.json"

# Traducciones automáticas que todavía no revisó nadie
REVIEW_FILE = BASE_DIR / "translations" / "automaticas_a_revisar.json"

# API key de Anthropic para la traducción automática (opcional: también
# sirve la variable de entorno ANTHROPIC_API_KEY). No se sube a git.
API_KEY_FILE = BASE_DIR / "anthropic_api_key.txt"