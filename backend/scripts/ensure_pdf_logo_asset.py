"""Generate default PNG logo for diet PDF header if missing (Pillow).

Uses DejaVu Sans Bold when available for readable text on the fallback logo.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_ASSETS = Path(__file__).resolve().parent.parent / "app" / "assets"
_LOGO = _ASSETS / "logo.png"

# Prefer a readable system font over PIL's tiny bitmap default
_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main() -> None:
    _ASSETS.mkdir(parents=True, exist_ok=True)
    w, h = 520, 140
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [4, 4, w - 5, h - 5],
        radius=18,
        fill=(30, 58, 95, 255),  # #1e3a5f
    )
    font = _load_font(28)
    title = "Dra. Acosta · Nutrisoft"
    bbox = draw.textbbox((0, 0), title, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        ((w - tw) / 2, (h - th) / 2),
        title,
        fill=(255, 255, 255, 255),
        font=font,
    )
    img.save(_LOGO, format="PNG")
    print(f"Logo generated: {_LOGO}")


if __name__ == "__main__":
    main()
