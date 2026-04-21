#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
DIST_NAME="usbformat-iso-burner-linux-x86_64"
BIN_NAME="usbformat-iso-burner"
PORTABLE_NAME="usbformat-iso-burner-portable"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -U pip
"$VENV_DIR/bin/pip" install pyinstaller PyQt6

rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist" "$SCRIPT_DIR/release" "$SCRIPT_DIR/$DIST_NAME.tar.gz" "$SCRIPT_DIR/$PORTABLE_NAME.tar.gz"

"$VENV_DIR/bin/pyinstaller" \
  --noconfirm \
  --clean \
  --onefile \
  --windowed \
  --name "$BIN_NAME" \
  "$SCRIPT_DIR/iso_gui.py"

mkdir -p "$SCRIPT_DIR/release/$DIST_NAME"
cp "$SCRIPT_DIR/dist/$BIN_NAME" "$SCRIPT_DIR/release/$DIST_NAME/$BIN_NAME"
cp "$SCRIPT_DIR/LICENSE" "$SCRIPT_DIR/README.md" "$SCRIPT_DIR/usbformat-iso-burner.desktop" "$SCRIPT_DIR/release-notes.md" "$SCRIPT_DIR/release/$DIST_NAME/"

mkdir -p "$SCRIPT_DIR/release/$PORTABLE_NAME"
cp \
  "$SCRIPT_DIR/iso_gui.py" \
  "$SCRIPT_DIR/README.md" \
  "$SCRIPT_DIR/LICENSE" \
  "$SCRIPT_DIR/CONTRIBUTING.md" \
  "$SCRIPT_DIR/CODE_OF_CONDUCT.md" \
  "$SCRIPT_DIR/SECURITY.md" \
  "$SCRIPT_DIR/CHANGELOG.md" \
  "$SCRIPT_DIR/requirements.txt" \
  "$SCRIPT_DIR/run.sh" \
  "$SCRIPT_DIR/install.sh" \
  "$SCRIPT_DIR/usbformat-iso-burner.desktop" \
  "$SCRIPT_DIR/release-notes.md" \
  "$SCRIPT_DIR/release/$PORTABLE_NAME/"

tar -czf "$SCRIPT_DIR/$DIST_NAME.tar.gz" -C "$SCRIPT_DIR/release" "$DIST_NAME"
tar -czf "$SCRIPT_DIR/$PORTABLE_NAME.tar.gz" -C "$SCRIPT_DIR/release" "$PORTABLE_NAME"
(cd "$SCRIPT_DIR" && sha256sum "$DIST_NAME.tar.gz" usbformat-iso-burner-portable.tar.gz > SHA256SUMS)

echo "Built:"
echo "  $SCRIPT_DIR/$DIST_NAME.tar.gz"
echo "  $SCRIPT_DIR/$PORTABLE_NAME.tar.gz"
