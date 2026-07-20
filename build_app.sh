#!/usr/bin/env bash
# Builds a fully self-contained GOATconvert.app (ffmpeg, pandoc, and a full
# copy of LibreOffice bundled inside) and packages it into GOATconvert.dmg.
# Run from the project root with the venv activated.
set -euo pipefail

FFMPEG_BIN="$(command -v ffmpeg)"
PANDOC_BIN="$(command -v pandoc)"
LIBREOFFICE_APP="/Applications/LibreOffice.app"

if [[ -z "$FFMPEG_BIN" || -z "$PANDOC_BIN" ]]; then
  echo "ffmpeg/pandoc not found on PATH — run: brew install ffmpeg pandoc" >&2
  exit 1
fi
if [[ ! -d "$LIBREOFFICE_APP" ]]; then
  echo "$LIBREOFFICE_APP not found — run: brew install --cask libreoffice" >&2
  exit 1
fi

echo "==> Generating app icon (.icns) from the goat emoji"
python3 -c "from goatconvert.ui.icon import ensure_icon; print(ensure_icon())"
ICONSET=/tmp/goatconvert_icon.iconset
rm -rf "$ICONSET" && mkdir -p "$ICONSET"
for size in 16 32 64 128 256 512; do
  sips -z $size $size goatconvert/assets/goat_icon.png --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  dbl=$((size * 2))
  sips -z $dbl $dbl goatconvert/assets/goat_icon.png --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o goatconvert/assets/goat_icon.icns

echo "==> Cleaning previous build"
rm -rf build dist

echo "==> Running PyInstaller (this copies ~800MB of LibreOffice, be patient)"
pyinstaller --windowed --name GOATconvert \
  --icon goatconvert/assets/goat_icon.icns \
  --contents-directory "." \
  --add-binary "${FFMPEG_BIN}:." \
  --add-binary "${PANDOC_BIN}:." \
  --add-data "${LIBREOFFICE_APP}:LibreOffice.app" \
  --noconfirm \
  main.py

echo "==> Building DMG"
rm -f dist/GOATconvert.dmg
create-dmg \
  --volname "GOATconvert" \
  --window-size 500 300 \
  --icon-size 100 \
  --icon "GOATconvert.app" 125 120 \
  --app-drop-link 375 120 \
  "dist/GOATconvert.dmg" \
  "dist/GOATconvert.app" || true  # create-dmg exits nonzero on benign AppleScript/Finder warnings

echo "==> Done"
ls -lh dist/GOATconvert.dmg
