#!/usr/bin/env bash
# build.sh — Build SimpleMarkdownEditor into a standalone executable
#
# macOS   : produces dist/SimpleMarkdownEditor.app
# Windows : produces dist/SimpleMarkdownEditor.exe  (Git Bash で実行)
#
# Usage:
#   bash build.sh             — フォルダ形式でビルド
#   bash build.sh --onefile   — 単一バイナリ / .exe にまとめる
#   bash build.sh --clean     — ビルド前に build/ dist/ を削除
#   オプションは組み合わせ可能: bash build.sh --clean --onefile

set -euo pipefail

APP_NAME="SimpleMarkdownEditor"
ENTRY="markdown_editor.py"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── OS 判定 ───────────────────────────────────────────────────────────────────
case "$(uname -s)" in
  Darwin*)  PLATFORM="macos"   ;;
  MINGW*|MSYS*|CYGWIN*) PLATFORM="windows" ;;
  Linux*)   PLATFORM="linux"   ;;
  *)        PLATFORM="unknown" ;;
esac

# Windows では $OS 環境変数でも判定できる（Git Bash 以外の場合の保険）
if [[ "${OS:-}" == "Windows_NT" && "$PLATFORM" == "unknown" ]]; then
  PLATFORM="windows"
fi

echo ">>> Platform : $PLATFORM"

# ── Python コマンドを解決（python3 → python の順で試す）─────────────────────
PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    PYTHON="$cmd"
    break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo "[ERROR] Python が見つかりません。Python 3.10 以降をインストールして PATH を通してください。"
  exit 1
fi
echo ">>> Python   : $($PYTHON --version)"

# ── parse args ────────────────────────────────────────────────────────────────
ONEFILE=false
CLEAN=false
for arg in "$@"; do
  case "$arg" in
    --onefile) ONEFILE=true ;;
    --clean)   CLEAN=true  ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

cd "$SCRIPT_DIR"

# ── clean ─────────────────────────────────────────────────────────────────────
if $CLEAN; then
  echo ">>> Cleaning build/ dist/ ..."
  rm -rf build dist "${APP_NAME}.spec"
fi

# ── check / install PyInstaller ───────────────────────────────────────────────
if ! "$PYTHON" -m PyInstaller --version &>/dev/null; then
  echo ">>> PyInstaller not found — installing ..."
  "$PYTHON" -m pip install pyinstaller
fi

# ── build ─────────────────────────────────────────────────────────────────────
echo ">>> Building ${APP_NAME} ..."

PYINSTALLER_ARGS=(
  --name "$APP_NAME"
  --noconfirm
  --windowed
  --collect-all markdown
  --collect-all pygments
  --hidden-import PySide6.QtWebEngineWidgets
  --hidden-import PySide6.QtWebEngineCore
  --hidden-import PySide6.QtWebEngineQuick
  --add-data "vendor:vendor"
  --add-data "plantuml.jar:."
)

if $ONEFILE; then
  PYINSTALLER_ARGS+=(--onefile)
else
  PYINSTALLER_ARGS+=(--onedir)
fi

"$PYTHON" -m PyInstaller "${PYINSTALLER_ARGS[@]}" "$ENTRY"

# ── result ────────────────────────────────────────────────────────────────────
echo ""
echo "✅ Build complete."

if $ONEFILE; then
  if [[ "$PLATFORM" == "windows" ]]; then
    echo "   Binary : dist/${APP_NAME}.exe"
  else
    echo "   Binary : dist/${APP_NAME}"
  fi
else
  case "$PLATFORM" in
    macos)
      echo "   App    : dist/${APP_NAME}.app"
      echo "   Run    : open dist/${APP_NAME}.app"
      ;;
    windows)
      echo "   Dir    : dist/${APP_NAME}/"
      echo "   Run    : start dist/${APP_NAME}/${APP_NAME}.exe"
      ;;
    *)
      echo "   Dir    : dist/${APP_NAME}/"
      echo "   Run    : dist/${APP_NAME}/${APP_NAME}"
      ;;
  esac
fi
