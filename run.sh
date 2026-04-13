#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

if ! python3 -c "import PyQt6" >/dev/null 2>&1; then
  echo "PyQt6 is not installed. Install it with: pip install -r requirements.txt" >&2
  exit 1
fi

exec python3 "$SCRIPT_DIR/iso_gui.py"
