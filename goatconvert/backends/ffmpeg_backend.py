"""Audio & video conversion via ffmpeg."""

from __future__ import annotations

import subprocess

from .. import bundled_paths

AUDIO_FORMATS = {"mp3", "wav", "flac", "ogg", "aac", "m4a", "wma", "opus"}
VIDEO_FORMATS = {"mp4", "mov", "mkv", "webm", "avi", "flv", "wmv", "m4v"}
ALL_FORMATS = AUDIO_FORMATS | VIDEO_FORMATS


def category_for(fmt: str) -> str:
    return "Video" if fmt in VIDEO_FORMATS else "Audio"


def is_available() -> bool:
    return bundled_paths.find_ffmpeg() is not None


def can_handle(fmt: str) -> bool:
    return fmt in ALL_FORMATS


def target_formats_for(fmt: str) -> set[str]:
    if fmt in VIDEO_FORMATS:
        # video -> any other video container, or extract to any audio format
        return (VIDEO_FORMATS - {fmt}) | AUDIO_FORMATS
    if fmt in AUDIO_FORMATS:
        # audio -> any other audio format (no meaningful audio->video)
        return AUDIO_FORMATS - {fmt}
    return set()


def convert(input_path: str, output_path: str, target_format: str) -> subprocess.CompletedProcess:
    cmd = [bundled_paths.find_ffmpeg(), "-y", "-i", input_path, output_path]
    print(f"[ffmpeg] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"[ffmpeg] exit code {result.returncode}")
    return result
