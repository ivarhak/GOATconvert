"""Office document <-> PDF conversion via headless LibreOffice.

soffice --convert-to only lets you pick the target format; it always writes
into a directory (same basename, new extension), so we convert into a temp
dir and move the result to the exact output_path the caller wants.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import bundled_paths

CATEGORY = "Documents"

OFFICE_FORMATS = {"doc", "docx", "odt", "rtf", "xls", "xlsx", "ods", "ppt", "pptx", "odp", "csv"}
FORMATS = OFFICE_FORMATS | {"pdf"}


def is_available() -> bool:
    return bundled_paths.find_soffice() is not None


def can_handle(fmt: str) -> bool:
    return fmt in FORMATS


def target_formats_for(fmt: str) -> set[str]:
    if fmt in OFFICE_FORMATS:
        return {"pdf"} | (OFFICE_FORMATS - {fmt})
    if fmt == "pdf":
        # PDF import is limited but soffice supports it for these
        return {"docx", "odt"}
    return set()


def convert(input_path: str, output_path: str, target_format: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [bundled_paths.find_soffice(), "--headless", "--convert-to", target_format, "--outdir", tmpdir, input_path]
        print(f"[libreoffice] running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"[libreoffice] exit code {result.returncode}")

        if result.returncode == 0:
            produced = Path(tmpdir) / (Path(input_path).stem + "." + target_format)
            if produced.exists():
                shutil.move(str(produced), output_path)
            else:
                print(f"[libreoffice] expected output {produced} not found after conversion")
                result.returncode = 1

        return result
