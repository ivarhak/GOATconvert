# Builds a fully self-contained GOATconvert app for Windows (ffmpeg, pandoc,
# and a full copy of LibreOffice bundled inside dist\GOATconvert\).
# Run with the venv activated. Meant to be driven by CI (see
# .github/workflows/release.yml) where ffmpeg/pandoc/LibreOffice are
# installed beforehand; pass their locations as params if they're not on PATH.
param(
    [string]$FfmpegPath = $(if (Get-Command ffmpeg -ErrorAction SilentlyContinue) { (Get-Command ffmpeg).Source } else { "" }),
    [string]$PandocPath = $(if (Get-Command pandoc -ErrorAction SilentlyContinue) { (Get-Command pandoc).Source } else { "" }),
    [string]$LibreOfficeDir = "C:\Program Files\LibreOffice"
)
$ErrorActionPreference = "Stop"

if (-not $FfmpegPath) { throw "ffmpeg.exe not found on PATH and no -FfmpegPath given" }
if (-not $PandocPath) { throw "pandoc.exe not found on PATH and no -PandocPath given" }
if (-not (Test-Path $LibreOfficeDir)) { throw "$LibreOfficeDir not found" }

Write-Host "==> Generating app icon (.ico) from the goat emoji"
Remove-Item -Force -ErrorAction SilentlyContinue goatconvert\assets\goat_icon.png, goatconvert\assets\goat_icon.ico
python -c "from goatconvert.ui.icon import ensure_icon; print(ensure_icon())"
python -c "from PIL import Image; img = Image.open('goatconvert/assets/goat_icon.png'); img.save('goatconvert/assets/goat_icon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"

Write-Host "==> Cleaning previous build"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist, GOATconvert.spec

Write-Host "==> Running PyInstaller (this copies LibreOffice, be patient)"
pyinstaller --windowed --name GOATconvert `
  --icon goatconvert\assets\goat_icon.ico `
  --contents-directory "." `
  --add-binary "$FfmpegPath;." `
  --add-binary "$PandocPath;." `
  --add-data "$LibreOfficeDir;LibreOffice" `
  --add-data "goatconvert\assets\goat_icon.png;." `
  --noconfirm `
  main.py

if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

Write-Host "==> Done. Build output in dist\GOATconvert\"
