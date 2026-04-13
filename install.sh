#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${HOME}/.local/share/usbformat-iso-burner"
DESKTOP_DIR="${HOME}/.local/share/applications"

mkdir -p "$APP_DIR" "$DESKTOP_DIR"

install -m 644 "$SCRIPT_DIR/iso_gui.py" "$APP_DIR/iso_gui.py"
install -m 644 "$SCRIPT_DIR/requirements.txt" "$APP_DIR/requirements.txt"
install -m 755 "$SCRIPT_DIR/run.sh" "$APP_DIR/run.sh"

sed "s|__APP_DIR__|$APP_DIR|g" "$SCRIPT_DIR/usbformat-iso-burner.desktop" > "$DESKTOP_DIR/usbformat-iso-burner.desktop"

cat <<EOF
Installed to:
  $APP_DIR

Desktop entry:
  $DESKTOP_DIR/usbformat-iso-burner.desktop

If PyQt6 is not installed yet, run:
  pip install -r "$APP_DIR/requirements.txt"
EOF
