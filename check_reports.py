"""
Chequea las tablas de CNVs de los informes sin generar ningún documento.

Uso:
    python check_reports.py                  -> todos los PDFs de input/
    python check_reports.py carpeta          -> PDFs de esa carpeta (y subcarpetas)
    python check_reports.py informe.pdf      -> un solo informe
"""

import sys
from pathlib import Path

from config import INPUT

from extractors.text_extractor import extract_text
from extractors.table_extractor import extract_cnv_tables
from classification.parsers.cnv_table_parser import parse_cnv_tables
from validators.cnv_validator import validate_cnvs
from pipeline import format_issues


def check_report(pdf_path):
    """
    Devuelve (cnvs, issues) para un informe.
    """

    text = extract_text(pdf_path)

    tables, issues = extract_cnv_tables(pdf_path)

    cnvs = parse_cnv_tables(tables)

    issues = issues + validate_cnvs(cnvs, text)

    if not tables:

        issues.append({
            "level": "ERROR",
            "page": None,
            "message": "No se encontró ninguna tabla de CNVs en el informe."
        })

    return cnvs, issues


def print_issues(issues):

    for line in format_issues(issues):
        print(line)


def main():

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else INPUT

    if target.is_file():
        pdf_files = [target]
    else:
        pdf_files = sorted(target.rglob("*.pdf"))

    if not pdf_files:
        print("No se encontraron PDFs.")
        return 0

    with_errors = []

    for pdf in pdf_files:

        cnvs, issues = check_report(pdf)

        associations = sum(len(cnv["associations"]) for cnv in cnvs)

        print("=" * 80)
        print(f"{pdf.name}  ->  {len(cnvs)} CNVs, {associations} filas")
        print("=" * 80)

        if issues:
            print_issues(issues)
        else:
            print("  OK")

        print()

        if any(issue["level"] == "ERROR" for issue in issues):
            with_errors.append(pdf.name)

    print(f"Informes revisados: {len(pdf_files)}")
    print(f"Informes con errores: {len(with_errors)}")

    for name in with_errors:
        print(f"  - {name}")

    return 1 if with_errors else 0


if __name__ == "__main__":

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    sys.exit(main())
