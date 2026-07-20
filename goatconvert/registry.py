"""Aggregates every backend's capabilities into one lookup used by the UI.

Each backend module exposes: is_available(), can_handle(fmt),
category_for(fmt), target_formats_for(fmt), convert(input_path,
output_path, target_format). category_for is per-format rather than a
fixed constant because a single backend can span more than one logical
category — ffmpeg alone handles both "Audio" and "Video" targets, and an
mp3 target shouldn't be labeled "Audio & Video" just because the same
binary happens to also do video. Adding a new backend later (e.g. Calibre
for ebooks) means writing one more module and adding it to BACKENDS below
— nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from .backends import ffmpeg_backend, image_backend, libreoffice_backend, pandoc_backend

BACKENDS = [ffmpeg_backend, pandoc_backend, libreoffice_backend, image_backend]


@dataclass
class TargetFormat:
    format: str
    category: str
    backend: object


def available_backends() -> list:
    available = [b for b in BACKENDS if b.is_available()]
    missing = [b for b in BACKENDS if not b.is_available()]
    for b in missing:
        print(f"[registry] backend {b.__name__} unavailable (binary/library not found) — its formats will be hidden")
    return available


def targets_for_file(detected_format: str) -> list[TargetFormat]:
    """All (format, category, backend) triples this file can be converted to,
    across every backend that recognizes the detected input format."""
    results: dict[str, TargetFormat] = {}
    for backend in available_backends():
        if not backend.can_handle(detected_format):
            continue
        for fmt in backend.target_formats_for(detected_format):
            if fmt not in results:
                results[fmt] = TargetFormat(format=fmt, category=backend.category_for(fmt), backend=backend)
    return sorted(results.values(), key=lambda t: (t.category, t.format))


def backend_for_conversion(detected_format: str, target_format: str):
    """Pick whichever available backend can actually do this specific
    conversion. Prefer the first backend in BACKENDS order that supports it."""
    for backend in available_backends():
        if backend.can_handle(detected_format) and target_format in backend.target_formats_for(detected_format):
            return backend
    return None
