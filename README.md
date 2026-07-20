# 🐐 GOATconvert

A fully offline, local file conversion desktop app. Drop in a file, search
the list of formats it can become, pick one, convert. No network calls,
ever — everything runs through locally installed conversion engines.

## Get the app (easiest)

Download the latest `GOATconvert.dmg` from the [Releases](../../releases)
page, open it, drag GOATconvert into Applications. ffmpeg, pandoc, and
LibreOffice are bundled inside — nothing else to install. Fully offline.

## Run from source (for development)

```bash
brew install ffmpeg pandoc
brew install --cask libreoffice

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Building the standalone .app / .dmg

```bash
source venv/bin/activate
pip install pyinstaller
./build_app.sh
```

Produces `dist/GOATconvert.app` and `dist/GOATconvert.dmg`, with ffmpeg,
pandoc, and a full copy of LibreOffice bundled inside the app bundle (see
`goatconvert/bundled_paths.py` for how those are located at runtime). This
is what gets attached to GitHub Releases.

## What it can convert

- **Documents**: md, html, docx, odt, rtf, txt, tex, epub, rst and more via
  [Pandoc](https://pandoc.org/); office formats ↔ PDF (docx/xlsx/pptx/odt/...)
  via headless LibreOffice.
- **Images**: png, jpg, webp, bmp, tiff, gif, heic via Pillow. (SVG input
  isn't supported — rasterizing it needs cairo, a native library with a
  large dependency tree that's fragile to bundle into a portable .app.)
- **Audio & video**: mp3, wav, flac, ogg, aac, mp4, mov, mkv, webm, avi and
  more via ffmpeg, including audio extraction from video.

## Architecture

- `goatconvert/detect.py` — figures out a file's real format from its
  own header bytes (a small built-in signature table), not just its
  extension — pure Python, no native libmagic dependency to bundle.
- `goatconvert/registry.py` — aggregates every backend's supported
  conversions into one searchable list per input file.
- `goatconvert/backends/` — one module per conversion engine
  (ffmpeg / pandoc / libreoffice / Pillow), each exposing a common
  `can_handle` / `target_formats_for` / `convert` interface. Adding a new
  engine (e.g. Calibre for ebooks) is just one more module.
- `goatconvert/convert_runner.py` — runs conversions on a background
  `QThread` so the UI never freezes, streaming output to the log pane.
- `goatconvert/ui/` — the PySide6 window: drag-and-drop, searchable format
  list, live log pane.

Every conversion prints (and logs in the UI) the exact backend and command
used, so failures are diagnosable from the log alone.
