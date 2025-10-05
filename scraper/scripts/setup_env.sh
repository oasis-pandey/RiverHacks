#!/usr/bin/env bash
# Simple environment setup for the scraper project
# Creates a `.venv` in the `scraper/` folder and installs requirements

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

echo "Setting up Python virtualenv in: $VENV_DIR"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
if [ -f "$ROOT_DIR/requirements.txt" ]; then
  pip install -r "$ROOT_DIR/requirements.txt"
else
  echo "requirements.txt not found in project root. Install requests and bs4 at minimum."
  pip install requests beautifulsoup4 lxml
fi

echo "Setup complete. Activate with: source $VENV_DIR/bin/activate"
