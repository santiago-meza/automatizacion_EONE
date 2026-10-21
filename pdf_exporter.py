from pathlib import Path

import pythoncom
import win32com.client


WD_FORMAT_PDF = 17


class WordConverter:
    """
    Abre una única instancia de Word para toda la tanda de informes.

    DispatchEx siempre crea una instancia nueva, así que no toca los
    documentos que el usuario tenga abiertos en Word (con Dispatch se
    podría enganchar a su Word y Quit() se lo cerraría).
    """

    def __enter__(self):

        # Necesario cuando se llama desde un hilo (la GUI)
        pythoncom.CoInitialize()

        try:
            self.word = win32com.client.DispatchEx("Word.Application")
            self.word.Visible = False
            self.word.DisplayAlerts = 0
        except Exception:
            pythoncom.CoUninitialize()
            raise

        return self

    def convert(self, docx_path, pdf_path=None):

        docx_path = Path(docx_path).resolve()
        pdf_path = Path(pdf_path or docx_path.with_suffix(".pdf")).resolve()

        doc = self.word.Documents.Open(str(docx_path), ReadOnly=True)

        try:
            doc.SaveAs2(str(pdf_path), FileFormat=WD_FORMAT_PDF)
        finally:
            doc.Close(False)

        return pdf_path

    def __exit__(self, *exc):

        try:
            self.word.Quit()
        finally:
            pythoncom.CoUninitialize()


def docx_to_pdf(docx_path, pdf_path=None):
    """Convierte un .docx a .pdf usando Microsoft Word."""

    with WordConverter() as converter:
        return converter.convert(docx_path, pdf_path)
