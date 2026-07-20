# 🐐 GOATconvert

A fully offline, local file conversion desktop app. Drop in a file, search
the list of formats it can become, pick one, convert. No network calls,
ever — everything runs through locally installed conversion engines.

## Get the app (easiest)

Download the latest release from the [Releases](../../releases) page:

- **macOS**: `GOATconvert.dmg` — open it, drag GOATconvert into Applications.
- **Windows**: `GOATconvert-Setup.exe` — run it, follow the installer.

ffmpeg, pandoc, and LibreOffice are bundled inside both — nothing else to
install. Fully offline. Both builds are unsigned (no Apple/Microsoft
developer certificate), so the OS will warn about an unidentified
publisher on first launch — on macOS right-click → Open, on Windows click
"More info" → "Run anyway".

## Run from source (for development)

```bash
brew install ffmpeg pandoc
brew install --cask libreoffice

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Building the standalone app

macOS (produces `dist/GOATconvert.app` and `dist/GOATconvert.dmg`):

```bash
source venv/bin/activate
pip install -r requirements.txt
./build_app.sh
```

Windows (produces `dist/GOATconvert/` and, via Inno Setup,
`installer_output/GOATconvert-Setup.exe`):

```powershell
pip install -r requirements.txt
.\build_app.ps1 -FfmpegPath <path to ffmpeg.exe> -PandocPath <path to pandoc.exe>
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

Both bundle ffmpeg, pandoc, and a full copy of LibreOffice inside the app
(see `goatconvert/bundled_paths.py` for how those are located at runtime,
cross-platform). In practice these are run automatically by
`.github/workflows/release.yml` on a `macos-latest`/`windows-latest`
runner whenever a `vX.Y.Z` tag is pushed, and the results are attached to
a GitHub Release — that's what's on the Releases page.

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
