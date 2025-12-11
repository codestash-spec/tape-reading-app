$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip pyinstaller
pyinstaller --clean --noconfirm --specpath specs --workpath build --distpath dist specs/tape_reading_app.spec
Write-Host "Artifacts in dist/"
