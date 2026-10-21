# genda_ui

Estilo visual común para los programas de GENDA hechos con customtkinter:
paleta violeta (modo claro y oscuro), encabezado con los logos, ícono de
ventana y componentes básicos.

## Usarlo en otro programa

1. Copiar la carpeta `genda_ui/` completa a la raíz del programa.
2. Heredar de `GendaApp` y poner los widgets dentro de `self.body`:

```python
import tkinter as tk

from genda_ui import FolderPicker, GendaApp, StatusLog, card, primary_button


class MiPrograma(GendaApp):

    def __init__(self):

        super().__init__(
            "NOMBRE DEL PROGRAMA",
            subtitle="Descripción breve",
            size=(820, 700),
            resizable=True
        )

        self.carpeta = tk.StringVar()

        panel = card(self.body)
        panel.pack(fill="x")

        FolderPicker(panel, "Carpeta de entrada", self.carpeta).pack(
            fill="x", padx=20, pady=16
        )

        primary_button(self.body, "Procesar", self.procesar).pack(pady=20)

        self.log = StatusLog(self.body)
        self.log.pack(fill="both", expand=True)

    def procesar(self):

        self.log.write("✓ Listo", "success")   # success | warning | error | info | muted


MiPrograma().mainloop()
```

3. Con PyInstaller, agregar al `.spec`:

```python
datas=[('genda_ui/assets', 'genda_ui/assets')],
...
icon='genda_ui/assets/icono.ico',
```

## Contenido

| Archivo | Uso |
|---|---|
| `assets/genda_violeta.json` | Tema de customtkinter (colores de todos los widgets) |
| `assets/isotipo.svg` | Isotipo vectorial (favicon para web / documentos) |
| `assets/icono.ico` | Ícono de ventana, barra de tareas y .exe |
| `assets/isotipo*.png`, `assets/logo_texto*.png` | Logos con fondo transparente (claro / oscuro) |
| `theme.py` | Paleta `COLORS`, `font()`, `color()` |
| `widgets.py` | `GendaApp`, `card`, `section_label`, `primary_button`, `secondary_button`, `FolderPicker`, `StatusLog` |

Si se cambian los logos, regenerar los PNG e ICO con:

```
python -m genda_ui.build_assets icon_1.jpg icon_2.jpg
```

Los colores están en dos lugares que deben coincidir:
`theme.py` (`COLORS`) y `assets/genda_violeta.json`.
