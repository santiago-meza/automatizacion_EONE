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

        # Preserve placeholder for later table insertion
        "CNV_TABLE": "{{ CNV_TABLE }}"
    }

    doc.render(
        context,
        autoescape=False
    )

    doc.save(output_path)