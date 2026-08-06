from docxtpl import DocxTemplate
from pathlib import Path
from datetime import datetime


def generate_report(template_path: Path, output_path: Path, data: dict):
    """
    Completa un template Word con los datos del paciente.
    """
    doc = DocxTemplate(template_path)

    today = datetime.now().strftime("%d/%m/%Y")

    context = {
        "PACIENTE": data.get("PATIENT", ""),
        "PROTOCOLO": data.get("PROTOCOL", ""),
        "FECHA": today,
        "RESULTADO": data.get("RESULTADO", ""),

        # NEW placeholders (must exist in your .docx template)
        "RESULTADO_VARIANTES_PATOGENICAS": data.get(
            "RESULTADO_VARIANTES_PATOGENICAS",
            "No se hallaron Variantes Patogénicas."
        ),
        "CNV_DETECCION_PHRASE": data.get(
            "CNV_DETECCION_PHRASE",
            "Se detectó una variante en el Número de Copias (CNV):"
        ),

        # Preserve placeholder for later table insertion
        "CNV_TABLE": "{{ CNV_TABLE }}",
    }

    doc.render(context, autoescape=False)
    doc.save(output_path)
