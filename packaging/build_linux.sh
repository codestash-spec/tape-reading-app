#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade pip pyinstaller
pyinstaller --clean --noconfirm --specpath specs --workpath build --distpath dist specs/tape_reading_app.spec
echo "Artifacts in dist/"
