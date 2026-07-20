"""Locates ffmpeg/pandoc/soffice binaries, cross-platform.

When running as a packaged app (PyInstaller sets sys.frozen), those tools
are bundled inside the app's own resource directory and are found there
first — so the packaged app needs nothing installed on the host machine.
When running from source, falls back to whatever's on PATH or each OS's
usual install location, which is how development/`python3 main.py`
normally works.
"""

from __future__ import annotations

import os
import shutil
import sys

_IS_WINDOWS = sys.platform.startswith("win")
_IS_MACOS = sys.platform == "darwin"


def _exe(name: str) -> str:
    return name + ".exe" if _IS_WINDOWS else name


def _resources_dir() -> str | None:
    if not getattr(sys, "frozen", False):
        return None

    exe_dir = os.path.dirname(sys.executable)

    if _IS_MACOS:
        # PyInstaller --windowed .app layout: the executable lives in
        # Contents/MacOS/<exe>, but --add-binary/--add-data files actually
        # land in Contents/Frameworks (confirmed by inspecting a real build
        # — despite --contents-directory "." not literally flattening
        # things onto Contents/MacOS for BUNDLE-mode macOS builds).
        return os.path.normpath(os.path.join(exe_dir, "..", "Frameworks"))

    # Windows (and Linux) onedir builds: bundled files sit right next to
    # the executable, no special subfolder.
    return exe_dir


def find_ffmpeg() -> str | None:
    res = _resources_dir()
    if res:
        bundled = os.path.join(res, _exe("ffmpeg"))
        if os.path.exists(bundled):
            return bundled
    return shutil.which("ffmpeg")


def find_pandoc() -> str | None:
    res = _resources_dir()
    if res:
        bundled = os.path.join(res, _exe("pandoc"))
        if os.path.exists(bundled):
            return bundled
    return shutil.which("pandoc")


def find_soffice() -> str | None:
    # On macOS, LibreOffice.app ships as a separate item in the DMG rather
    # than nested inside our own .app bundle (see build_app.sh for why —
    # nesting a huge pre-signed third-party app broke code signing in
    # several distinct ways), so there's no "look inside our own bundle"
    # case there. On Windows, PyInstaller's onedir layout doesn't have that
    # problem, so LibreOffice is bundled directly alongside the .exe.
    if _IS_WINDOWS:
        res = _resources_dir()
        if res:
            bundled = os.path.join(res, "LibreOffice", "program", "soffice.exe")
            if os.path.exists(bundled):
                return bundled

    if _IS_WINDOWS:
        for path in (
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ):
            if os.path.exists(path):
                return path
    else:
        system_app = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        if os.path.exists(system_app):
            return system_app

    return shutil.which("soffice")
