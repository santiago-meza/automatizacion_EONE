import sys

from tkinter import filedialog

import customtkinter as ctk

from PIL import Image

from genda_ui.theme import COLORS, asset_path, color, font, setup_theme


LOGO_HEIGHT = 46


# ============================================================
# Ventana base
# ============================================================

class GendaApp(ctk.CTk):

    """
    Ventana con el estilo de GENDA: ícono, encabezado con los logos
    y el nombre del programa. El contenido va dentro de self.body.
    """

    def __init__(
        self,
        title,
        subtitle="",
        size=(820, 820),
        resizable=False,
        appearance="System",
        app_id=None
    ):

        setup_theme(appearance)

        set_windows_app_id(app_id or f"GENDA.{title}")

        super().__init__()

        self.title(title)

        self._fit_to_screen(*size)

        self.resizable(resizable, resizable)

        self.minsize(640, 560)

        self.iconbitmap(str(asset_path("icono.ico")))

        self._create_header(title, subtitle)

        self.body = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.body.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(20, 20)
        )

    def _fit_to_screen(self, width, height):

        # Centrada y sin pasarse de la pantalla (deja lugar para
        # la barra de título y la barra de tareas)
        scaling = self._get_window_scaling()

        screen_width = self.winfo_screenwidth() / scaling
        screen_height = self.winfo_screenheight() / scaling

        width = int(min(width, screen_width - 40))
        height = int(min(height, screen_height - 110))

        x = int((screen_width - width) / 2)
        y = int(max(0, (screen_height - 110 - height) / 2))

        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_header(self, title, subtitle):

        header = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=COLORS["surface"]
        )

        header.pack(fill="x")

        logos = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )

        logos.pack(
            side="left",
            padx=(28, 0),
            pady=16
        )

        # Isotipo (icon_2) a la izquierda del logo GENDA (icon_1)
        ctk.CTkLabel(
            logos,
            text="",
            image=brand_image("isotipo", LOGO_HEIGHT)
        ).pack(side="left")

        ctk.CTkLabel(
            logos,
            text="",
            image=brand_image("logo_texto", LOGO_HEIGHT - 6)
        ).pack(side="left", padx=(12, 0))

        titles = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )

        titles.pack(
            side="right",
            padx=(0, 28)
        )

        ctk.CTkLabel(
            titles,
            text=title,
            font=font(24, "bold"),
            text_color=COLORS["brand"]
        ).pack(anchor="e")

        if subtitle:

            ctk.CTkLabel(
                titles,
                text=subtitle,
                font=font(13),
                text_color=COLORS["muted"]
            ).pack(anchor="e")

        # Línea de acento violeta
        ctk.CTkFrame(
            self,
            height=3,
            corner_radius=0,
            fg_color=COLORS["brand"]
        ).pack(fill="x")


def brand_image(name, height):

    light = Image.open(asset_path(f"{name}.png"))
    dark = Image.open(asset_path(f"{name}_oscuro.png"))

    width = round(light.width * height / light.height)

    return ctk.CTkImage(
        light_image=light,
        dark_image=dark,
        size=(width, height)
    )


def set_windows_app_id(app_id):

    # Sin esto, la barra de tareas muestra el ícono de Python
    if sys.platform != "win32":
        return

    try:

        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            app_id
        )

    except (AttributeError, OSError):

        pass


# ============================================================
# Componentes
# ============================================================

def card(parent):

    return ctk.CTkFrame(
        parent,
        border_width=1
    )


def section_label(parent, text):

    return ctk.CTkLabel(
        parent,
        text=text,
        font=font(14, "bold"),
        text_color=COLORS["text"]
    )


def primary_button(parent, text, command, **kwargs):

    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        height=kwargs.pop("height", 44),
        font=font(15, "bold"),
        **kwargs
    )


def secondary_button(parent, text, command, **kwargs):

    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        height=kwargs.pop("height", 36),
        font=font(13),
        fg_color="transparent",
        border_width=1,
        border_color=COLORS["brand"],
        text_color=COLORS["brand"],
        hover_color=COLORS["border"],
        **kwargs
    )


class FolderPicker(ctk.CTkFrame):

    """Etiqueta + campo de ruta + botón Examinar."""

    def __init__(
        self,
        parent,
        label,
        variable,
        dialog_title=None,
        on_change=None
    ):

        super().__init__(parent, fg_color="transparent")

        self.variable = variable
        self.dialog_title = dialog_title or label
        self.on_change = on_change

        section_label(self, label).pack(anchor="w")

        row = ctk.CTkFrame(self, fg_color="transparent")

        row.pack(fill="x", pady=(4, 0))

        ctk.CTkEntry(
            row,
            textvariable=variable,
            height=38,
            font=font(13)
        ).pack(side="left", fill="x", expand=True)

        secondary_button(
            row,
            "Examinar…",
            self.browse,
            width=110,
            height=38
        ).pack(side="right", padx=(10, 0))

    def browse(self):

        folder = filedialog.askdirectory(
            title=self.dialog_title,
            initialdir=self.variable.get() or None
        )

        if folder:

            self.variable.set(folder)

            if self.on_change:
                self.on_change()


class StatusLog(ctk.CTkTextbox):

    """Cuadro de mensajes con colores según el tipo de línea."""

    KINDS = ("success", "warning", "error", "info", "muted")

    def __init__(self, parent, **kwargs):

        super().__init__(
            parent,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            **kwargs
        )

        self.configure(state="disabled")

    def write(self, message, kind=None):

        # Los colores se recalculan por si cambió el modo claro/oscuro
        for name in self.KINDS:
            self.tag_config(name, foreground=color(name))

        self.configure(state="normal")

        self.insert(
            "end",
            message + "\n",
            kind or ()
        )

        self.see("end")

        self.configure(state="disabled")

    def clear(self):

        self.configure(state="normal")

        self.delete("1.0", "end")

        self.configure(state="disabled")
