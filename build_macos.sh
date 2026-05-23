#!/usr/bin/env bash
set -euo pipefail

APP_NAME="ScoreCapture"
VENV_DIR=".venv-build-macos"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BUNDLE_ID="com.illboong.scorecapture"
PACKAGE_DIR="dist-package"

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt

rm -rf build dist "${PACKAGE_DIR}" "${APP_NAME}.spec"

python -m PyInstaller \
  --name "${APP_NAME}" \
  --windowed \
  --clean \
  --osx-bundle-identifier "${BUNDLE_ID}" \
  score_capture_gui.py

codesign --force --deep --sign - "dist/${APP_NAME}.app"

mkdir -p "${PACKAGE_DIR}"
cp -R "dist/${APP_NAME}.app" "${PACKAGE_DIR}/"
cp README_FIRST_MAC.txt "${PACKAGE_DIR}/"
cp MAC_USER_GUIDE.txt "${PACKAGE_DIR}/"

(cd "${PACKAGE_DIR}" && ditto -c -k --sequesterRsrc --keepParent "${APP_NAME}.app" "../dist/${APP_NAME}-macOS.zip")
hdiutil create \
  -volname "${APP_NAME}" \
  -srcfolder "${PACKAGE_DIR}" \
  -ov \
  -format UDZO \
  "dist/${APP_NAME}-macOS.dmg"

echo
echo "Build complete:"
echo "  dist/${APP_NAME}-macOS.zip"
echo "  dist/${APP_NAME}-macOS.dmg"
echo "The app writes captures and PDFs to ~/Documents/${APP_NAME}"
