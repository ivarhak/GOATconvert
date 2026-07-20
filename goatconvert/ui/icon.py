"""Renders the 🐐 emoji to a PNG once, used as the window/app icon.

Generated locally via Pillow's emoji-font rendering (no network fetch) —
uses whatever system emoji font is available (Apple Color Emoji on macOS).
"""

from __future__ import annotations

import os

_ICON_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "goat_icon.png")


def ensure_icon() -> str:
    icon_path = os.path.abspath(_ICON_PATH)
    if os.path.exists(icon_path):
        return icon_path

    from PIL import Image, ImageDraw, ImageFont

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = None
    for font_path in (
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc",
    ):
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, size - 40)
                break
            except OSError:
                continue

    if font is not None:
        draw.text((size // 2, size // 2), "\U0001F410", font=font, anchor="mm", embedded_color=True)
    else:
        # Fallback: simple colored circle with "G" if no emoji font found
        draw.ellipse((10, 10, size - 10, size - 10), fill=(220, 200, 160, 255))
        draw.text((size // 2, size // 2), "G", fill=(60, 40, 20, 255), anchor="mm")

    os.makedirs(os.path.dirname(icon_path), exist_ok=True)
    img.save(icon_path)
    print(f"[icon] generated {icon_path}")
    return icon_path
