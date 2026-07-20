"""Markup/text document conversion via Pandoc.

PDF output is intentionally excluded here — Pandoc's PDF writer needs a
LaTeX engine (MacTeX, a multi-GB install), which we're not requiring.
Office-format <-> PDF is handled by libreoffice_backend instead.
"""

from __future__ import annotations

import subprocess

from .. import bundled_paths

FORMATS = {"md", "html", "docx", "odt", "rtf", "txt", "tex", "epub", "rst", "textile", "org", "asciidoc"}


def category_for(fmt: str) -> str:
    return "Documents"


def is_available() -> bool:
    return bundled_paths.find_pandoc() is not None


def can_handle(fmt: str) -> bool:
    return fmt in FORMATS


def target_formats_for(fmt: str) -> set[str]:
    if fmt not in FORMATS:
        return set()
    return FORMATS - {fmt}


def convert(input_path: str, output_path: str, target_format: str) -> subprocess.CompletedProcess:
    cmd = [bundled_paths.find_pandoc(), input_path, "-o", output_path]
    print(f"[pandoc] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"[pandoc] exit code {result.returncode}")
    return result
