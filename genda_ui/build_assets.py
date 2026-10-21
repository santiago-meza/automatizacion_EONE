"""
Regenera los recursos gráficos de genda_ui/assets a partir de
los logos originales (icon_1.jpg = GENDA, icon_2.jpg = isotipo).

Uso (desde la raíz del proyecto):

    python -m genda_ui.build_assets icon_1.jpg icon_2.jpg

Genera:
    logo_texto.png / logo_texto_oscuro.png   (icon_1, fondo transparente)
    isotipo.png / isotipo_oscuro.png         (icon_2, fondo transparente)
    icono.ico                                (ventana, barra de tareas y .exe)

El favicon vectorial (isotipo.svg) está dibujado a mano y no se
regenera.
"""

import sys

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


ASSETS = Path(__file__).resolve().parent / "assets"

# Color del texto en modo oscuro (lavanda claro)
DARK_TEXT_COLOR = (226, 196, 236)


# ============================================================
# Fondo blanco -> transparente
# ============================================================

def text_logo_alpha(image):

    """
    Logo de un solo color sobre blanco: la opacidad sale de qué tan
    lejos está cada píxel del blanco (conserva los bordes suaves y
    los huecos de letras como la D o la A).
    """

    rgb = image.convert("RGB")

    darkness = ImageChops.invert(
        rgb.convert("L")
    )

    # Ruido de compresión JPG en el fondo -> totalmente transparente
    return darkness.point(
        lambda v: 0 if v < 12 else min(255, int(v * 1.35))
    )


def symbol_alpha(image):

    """
    Isotipo con brillo blanco en la esfera: solo el blanco conectado
    con el borde de la imagen es fondo.
    """

    rgb = image.convert("RGB")

    width, height = rgb.size

    mask = Image.new("L", rgb.size, 255)

    filled = rgb.copy()

    for corner in (
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1)
    ):

        ImageDraw.floodfill(
            filled,
            corner,
            (0, 255, 0),
            thresh=60
        )

    green = Image.new("RGB", rgb.size, (0, 255, 0))

    background = ImageChops.difference(
        filled,
        green
    ).convert("L").point(
        lambda v: 255 if v < 8 else 0
    )

    mask.paste(0, mask=background)

    # Bordes suaves
    return mask.filter(
        ImageFilter.GaussianBlur(1.2)
    )


def with_alpha(image, alpha, color=None):

    rgba = image.convert("RGB")

    if color:

        rgba = Image.new("RGB", rgba.size, color)

    rgba = rgba.convert("RGBA")

    rgba.putalpha(alpha)

    return rgba.crop(
        alpha.point(lambda v: 255 if v > 20 else 0).getbbox()
    )


def lighten(image, amount):

    """Aclara los colores (para modo oscuro) sin tocar la opacidad."""

    rgb = image.convert("RGB")

    white = Image.new("RGB", rgb.size, (255, 255, 255))

    light = Image.blend(rgb, white, amount).convert("RGBA")

    light.putalpha(image.getchannel("A"))

    return light


# ============================================================
# Build
# ============================================================

def build(text_logo_path, symbol_path):

    ASSETS.mkdir(exist_ok=True)

    text_logo = Image.open(text_logo_path)

    alpha = text_logo_alpha(text_logo)

    # El texto es de un solo color: se pinta plano para que
    # no queden halos blancos en los bordes
    brand = text_logo.convert("RGB").getpixel(
        (90, 240)
    )

    if sum(brand) > 600:
        brand = (108, 26, 90)

    with_alpha(text_logo, alpha, brand).save(
        ASSETS / "logo_texto.png"
    )

    with_alpha(text_logo, alpha, DARK_TEXT_COLOR).save(
        ASSETS / "logo_texto_oscuro.png"
    )

    symbol = Image.open(symbol_path)

    symbol = with_alpha(
        symbol,
        symbol_alpha(symbol)
    )

    symbol.save(ASSETS / "isotipo.png")

    lighten(symbol, 0.30).save(
        ASSETS / "isotipo_oscuro.png"
    )

    # Ícono cuadrado para Windows
    side = max(symbol.size)

    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))

    square.paste(
        symbol,
        ((side - symbol.width) // 2, (side - symbol.height) // 2)
    )

    square.save(
        ASSETS / "icono.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
               (64, 64), (128, 128), (256, 256)]
    )


if __name__ == "__main__":

    if len(sys.argv) != 3:

        print(__doc__)

        sys.exit(1)

    build(sys.argv[1], sys.argv[2])

    print(f"Recursos generados en {ASSETS}")
