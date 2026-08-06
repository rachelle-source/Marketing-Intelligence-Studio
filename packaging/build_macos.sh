#!/usr/bin/env bash
# Build the macOS .app. Run this ON macOS with Python 3.12+ installed
# (get it from python.org, or `brew install python@3.12`).
#
# Usage:
#   chmod +x packaging/build_macos.sh
#   ./packaging/build_macos.sh

set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller packaging/pyinstaller.spec --noconfirm --distpath dist --workpath build

echo
echo "Build complete:"
echo "  dist/Marketing Intelligence Studio.app"
echo
