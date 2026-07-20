"""Renders the 🐐 emoji to a PNG once, used as the window/app icon.

Rendered via Qt's own text painter rather than Pillow's font engine — Qt
uses macOS's native CoreText backend, which handles Apple Color Emoji's
color glyph tables correctly. Pillow's raqm-less renderer silently fails
to draw color glyphs from that font, producing a blank icon.
"""

from __future__ import annotations

import os
import sys
import tempfile

from .. import bundled_paths

_ICON_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "goat_icon.png")


def _render_goat_png(icon_path: str) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QGuiApplication, QImage, QPainter

    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(sys.argv[:1])

    size = 512
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)

    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    font = QFont()
    font.setPointSize(int(size * 0.7))
    painter.setFont(font)
    painter.drawText(img.rect(), Qt.AlignmentFlag.AlignCenter, "\U0001F410")
    painter.end()

    os.makedirs(os.path.dirname(icon_path), exist_ok=True)
    img.save(icon_path)
    print(f"[icon] generated {icon_path}")


def ensure_icon() -> str:
    if getattr(sys, "frozen", False):
        # Packaged builds ship this file baked in (the build script
        # generates it before running PyInstaller and bundles it as a flat
        # top-level file, sitting next to ffmpeg/pandoc — see
        # bundled_paths.py). If it's somehow missing at runtime, don't try
        # to write into the read-only app bundle — fall back to a temp
        # file instead.
        res = bundled_paths._resources_dir()
        bundled = os.path.join(res, "goat_icon.png") if res else None
        if bundled and os.path.exists(bundled):
            return bundled

        fallback = os.path.join(tempfile.gettempdir(), "goatconvert_goat_icon.png")
        if os.path.exists(fallback):
            return fallback
        _render_goat_png(fallback)
        return fallback

    icon_path = os.path.abspath(_ICON_PATH)
    if os.path.exists(icon_path):
        return icon_path
    _render_goat_png(icon_path)
    return icon_path
