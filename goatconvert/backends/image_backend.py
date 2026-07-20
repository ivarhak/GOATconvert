"""Image conversion via Pillow (+ pillow-heif for HEIC).

SVG is intentionally not supported: rasterizing it needs cairo, a native
library with a large transitive dependency tree that's fragile to bundle
into a portable, double-click .app. Pillow alone covers everything else
with zero native-library bundling headaches.
"""

from __future__ import annotations

RASTER_FORMATS = {"png", "jpg", "webp", "bmp", "tiff", "gif", "heic"}
FORMATS = RASTER_FORMATS

_PILLOW_SAVE_FORMAT = {"jpg": "JPEG"}  # Pillow needs "JPEG", not "JPG"


def category_for(fmt: str) -> str:
    return "Images"


def is_available() -> bool:
    try:
        import PIL  # noqa: F401

        return True
    except ImportError:
        return False


def can_handle(fmt: str) -> bool:
    return fmt in FORMATS


def target_formats_for(fmt: str) -> set[str]:
    if fmt in RASTER_FORMATS:
        return RASTER_FORMATS - {fmt}
    return set()


class _FakeResult:
    """Mimics subprocess.CompletedProcess so convert_runner can treat all
    backends uniformly, even though this backend runs in-process rather
    than shelling out."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def convert(input_path: str, output_path: str, target_format: str) -> _FakeResult:
    log_lines = []

    def log(msg: str):
        print(f"[image] {msg}")
        log_lines.append(msg)

    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
    except ImportError:
        log("pillow-heif not installed; HEIC support may be unavailable")

    try:
        from PIL import Image

        img = Image.open(input_path)

        save_format = _PILLOW_SAVE_FORMAT.get(target_format, target_format.upper())
        log(f"converting {input_path} -> {output_path} (format={save_format})")

        if save_format in ("JPEG", "BMP") and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.save(output_path, format=save_format)
        log("done")
        return _FakeResult(0, stdout="\n".join(log_lines))
    except Exception as exc:  # noqa: BLE001 - surface any failure to the UI log
        log(f"ERROR: {exc}")
        return _FakeResult(1, stderr=str(exc))
