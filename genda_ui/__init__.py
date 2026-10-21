"""
Estilo visual común de los programas de GENDA.

Copiar la carpeta genda_ui completa a cualquier programa con
customtkinter y usar:

    from genda_ui import GendaApp, FolderPicker, StatusLog

    class MiPrograma(GendaApp):

        def __init__(self):

            super().__init__(
                "NOMBRE DEL PROGRAMA",
                subtitle="Descripción breve"
            )

            # Agregar los widgets dentro de self.body
"""

from genda_ui.theme import (
    COLORS,
    FONT_FAMILY,
    asset_path,
    color,
    font,
    setup_theme
)
from genda_ui.widgets import (
    FolderPicker,
    GendaApp,
    StatusLog,
    card,
    primary_button,
    secondary_button,
    section_label
)
