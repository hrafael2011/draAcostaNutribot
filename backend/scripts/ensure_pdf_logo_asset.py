"""Generate default PNG logo for diet PDF header if missing (Pillow)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_ASSETS = Path(__file__).resolve().parent.parent / "app" / "assets"
_LOGO = _ASSETS / "logo.png"


def main() -> None:
    _ASSETS.mkdir(parents=True, exist_ok=True)
    w, h = 520, 140
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([4, 4, w - 5, h - 5], radius=18, fill=(30, 58, 95, 255))
    font = ImageFont.load_default()
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
    print(_LOGO)


if __name__ == "__main__":
    main()
