"""Locates ffmpeg/pandoc/soffice binaries.

When running as a packaged .app (PyInstaller sets sys.frozen), those tools
are bundled inside the app's own Resources directory and are found there
first — so the packaged app needs nothing installed on the host machine.
When running from source, falls back to whatever's on PATH or in
/Applications, which is how development/`python3 main.py` normally works.
"""

from __future__ import annotations

import os
import shutil
import sys


def _resources_dir() -> str | None:
    if getattr(sys, "frozen", False):
        # PyInstaller --windowed .app layout: the executable lives in
        # Contents/MacOS/<exe>, but --add-binary/--add-data files actually
        # land in Contents/Frameworks (confirmed by inspecting a real build
        # — despite --contents-directory "." not literally flattening
        # things onto Contents/MacOS for BUNDLE-mode macOS builds).
        macos_dir = os.path.dirname(sys.executable)
        return os.path.normpath(os.path.join(macos_dir, "..", "Frameworks"))
    return None


def find_ffmpeg() -> str | None:
    res = _resources_dir()
    if res:
        bundled = os.path.join(res, "ffmpeg")
        if os.path.exists(bundled):
            return bundled
    return shutil.which("ffmpeg")


def find_pandoc() -> str | None:
    res = _resources_dir()
    if res:
        bundled = os.path.join(res, "pandoc")
        if os.path.exists(bundled):
            return bundled
    return shutil.which("pandoc")


def find_soffice() -> str | None:
    res = _resources_dir()
    if res:
        # PyInstaller sanitizes ".app" in bundled data-file dirnames to
        # "__dot__app" to avoid macOS treating it as a nested bundle.
        for app_dirname in ("LibreOffice__dot__app", "LibreOffice.app"):
            bundled = os.path.join(res, app_dirname, "Contents", "MacOS", "soffice")
            if os.path.exists(bundled):
                return bundled

    system_app = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if os.path.exists(system_app):
        return system_app

    return shutil.which("soffice")
