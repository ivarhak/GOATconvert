"""Detect a file's real format — extension is a hint, magic bytes confirm it.

Extensions lie (a renamed .txt can still be a .docx). We sniff the file's
own header bytes against a small table of signatures for every format this
app actually handles, rather than depending on the system's full libmagic
database — that keeps this pure Python with zero native library
dependencies, which matters a lot for shipping a truly self-contained,
double-click .app/.dmg (no bundled .dylib/rpath fragility, no magic
database file to ship).
"""

from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass

# (format, signature_bytes, offset) — checked in order, first match wins.
_SIGNATURES: list[tuple[str, bytes, int]] = [
    ("png", b"\x89PNG\r\n\x1a\n", 0),
    ("jpg", b"\xff\xd8\xff", 0),
    ("gif", b"GIF87a", 0),
    ("gif", b"GIF89a", 0),
    ("bmp", b"BM", 0),
    ("tiff", b"II*\x00", 0),
    ("tiff", b"MM\x00*", 0),
    ("webp", b"WEBP", 8),  # RIFF....WEBP
    ("heic", b"ftypheic", 4),
    ("heic", b"ftypmif1", 4),
    ("pdf", b"%PDF", 0),
    ("flac", b"fLaC", 0),
    ("ogg", b"OggS", 0),
    ("wav", b"WAVE", 8),  # RIFF....WAVE
    ("mp3", b"ID3", 0),
    ("mp4", b"ftyp", 4),
    ("mov", b"ftypqt", 4),
    ("mkv", b"\x1a\x45\xdf\xa3", 0),  # also matches webm (both EBML)
    ("rtf", b"{\\rtf", 0),
]

# Office Open XML / OpenDocument files are ZIPs — the extension is the only
# reliable signal for which kind of ZIP it is (docx vs xlsx vs odt etc), so
# for these we trust the extension once we've confirmed it really is a ZIP.
_ZIP_BASED_EXTENSIONS = {"docx", "xlsx", "pptx", "odt", "ods", "odp", "epub"}

# Text-based formats with no distinctive byte signature — trust the extension.
_TEXT_EXTENSIONS = {"md", "markdown", "html", "htm", "txt", "csv", "tex", "rst", "textile", "org", "asciidoc", "doc"}


@dataclass
class DetectedFile:
    path: str
    extension: str  # lowercase, no dot, from filename
    format: str  # canonical short format name used by the registry


def _sniff_signature(header: bytes) -> str | None:
    for fmt, sig, offset in _SIGNATURES:
        end = offset + len(sig)
        if len(header) >= end and header[offset:end] == sig:
            return fmt
    return None


def detect_file(path: str) -> DetectedFile:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if ext == "htm":
        ext = "html"

    with open(path, "rb") as f:
        header = f.read(64)

    sniffed = _sniff_signature(header)

    if sniffed:
        print(f"[detect] {path}: sniffed format '{sniffed}' from file header")
        return DetectedFile(path=path, extension=ext, format=sniffed)

    if header[:2] == b"PK" and ext in _ZIP_BASED_EXTENSIONS:
        if zipfile.is_zipfile(path):
            print(f"[detect] {path}: confirmed ZIP container, trusting extension '.{ext}'")
        else:
            print(f"[detect] {path}: WARNING has 'PK' header but isn't a valid zip; trusting extension '.{ext}' anyway")
        return DetectedFile(path=path, extension=ext, format=ext)

    if ext in _TEXT_EXTENSIONS:
        print(f"[detect] {path}: no binary signature (text-based format), trusting extension '.{ext}'")
        return DetectedFile(path=path, extension=ext, format=ext)

    print(f"[detect] {path}: no known signature matched, falling back to extension '.{ext}'")
    return DetectedFile(path=path, extension=ext, format=ext)
