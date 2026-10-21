import sys

from pathlib import Path

import customtkinter as ctk


# ============================================================
# Paleta (modo claro, modo oscuro)
# Debe coincidir con assets/genda_violeta.json
# ============================================================

COLORS = {
    "brand": ("#6C1A5A", "#B98AC9"),
    "brand_hover": ("#551446", "#A5509A"),
    "background": ("#F6F1F7", "#17111A"),
    "surface": ("#FFFFFF", "#221A26"),
    "border": ("#E6DAEA", "#3A2D40"),
    "text": ("#2A1630", "#F1E9F3"),
    "muted": ("#7A6680", "#B9A8BF"),
    "success": ("#2E7D4F", "#6FCF97"),
    "warning": ("#9A5B00", "#F5C46B"),
    "error": ("#B3261E", "#F2B8B5"),
    "info": ("#6C1A5A", "#D2B3DD")
}

FONT_FAMILY = "Segoe UI"


# ============================================================
# Recursos
# ============================================================

def asset_path(name):

    # Con PyInstaller los recursos quedan en sys._MEIPASS/genda_ui/assets
    if getattr(sys, "frozen", False):

        base = Path(sys._MEIPASS) / "genda_ui"

    else:

        base = Path(__file__).resolve().parent

    return base / "assets" / name


def color(name):

    """Color del modo de apariencia actual (para widgets de tk puros)."""

    light, dark = COLORS[name]

    return dark if ctk.get_appearance_mode() == "Dark" else light


def font(size=13, weight="normal"):

    return ctk.CTkFont(
        family=FONT_FAMILY,
        size=size,
        weight=weight
    )


def setup_theme(appearance="System"):

    ctk.set_appearance_mode(appearance)

    ctk.set_default_color_theme(
        str(asset_path("genda_violeta.json"))
    )
