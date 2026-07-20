#!/usr/bin/env bash
# Builds GOATconvert.app (ffmpeg + pandoc bundled inside) and packages it
# into GOATconvert.dmg alongside a plain, untouched copy of LibreOffice.app.
#
# LibreOffice is intentionally NOT nested inside GOATconvert.app's own
# Contents/ — PyInstaller's data-file classification for a huge, complex,
# already-signed app like LibreOffice fights with macOS code-signing's
# resource sealing in several distinct ways (renamed nested .appex/.app
# bundles, dangling Resources/ symlinks, stray partial framework copies),
# and any mismatch between the signed manifest and what's actually on disk
# makes Gatekeeper report the *whole* app as "damaged" after download —
# not just "unidentified developer". Shipping LibreOffice.app as a separate
# item in the same DMG keeps GOATconvert.app's own signature simple and
# reliable, and leaves LibreOffice's original Developer ID signature
# completely untouched. The user drags both into Applications.
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
rm -f goatconvert/assets/goat_icon.png goatconvert/assets/goat_icon.icns
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
rm -rf build dist GOATconvert.spec

echo "==> Running PyInstaller (ffmpeg + pandoc only — LibreOffice ships separately, see comment above)"
pyinstaller --windowed --name GOATconvert \
  --icon goatconvert/assets/goat_icon.icns \
  --contents-directory "." \
  --add-binary "${FFMPEG_BIN}:." \
  --add-binary "${PANDOC_BIN}:." \
  --add-data "goatconvert/assets/goat_icon.png:." \
  --noconfirm \
  main.py

echo "==> Fixing code signature"
# ffmpeg/pandoc are already validly (ad-hoc) signed by Homebrew; PyInstaller's
# own automatic --deep re-sign of the whole bundle can still disturb that.
# Strip the outer bundle's own seal and give it a fresh one, non-deep, so
# the already-valid nested signatures on ffmpeg/pandoc are never touched.
codesign --remove-signature dist/GOATconvert.app
codesign --force -s - dist/GOATconvert.app
codesign --verify --deep --strict dist/GOATconvert.app
echo "Signature structurally verified clean."
# spctl will still say "rejected" here — that's expected for any ad-hoc
# signed app without an Apple Developer ID/notarization (the normal
# "unidentified developer" Gatekeeper policy, not a corruption problem;
# users bypass it via right-click > Open). Log it, don't fail the build on it.
spctl -a -vv dist/GOATconvert.app 2>&1 || true

echo "==> Staging DMG contents (GOATconvert.app + a plain untouched copy of LibreOffice.app)"
rm -rf dist/dmg_staging
mkdir -p dist/dmg_staging
ditto dist/GOATconvert.app dist/dmg_staging/GOATconvert.app
ditto "$LIBREOFFICE_APP" dist/dmg_staging/LibreOffice.app
find dist/dmg_staging/LibreOffice.app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "==> Building DMG"
rm -f dist/GOATconvert.dmg
create-dmg \
  --volname "GOATconvert" \
  --window-size 660 320 \
  --icon-size 100 \
  --icon "GOATconvert.app" 150 120 \
  --icon "LibreOffice.app" 330 120 \
  --app-drop-link 500 120 \
  "dist/GOATconvert.dmg" \
  "dist/dmg_staging" || true  # create-dmg exits nonzero on benign AppleScript/Finder warnings

echo "==> Done"
ls -lh dist/GOATconvert.dmg
