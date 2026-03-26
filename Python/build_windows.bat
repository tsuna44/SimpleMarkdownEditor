@echo off
REM build_windows.bat — Build SimpleMarkdownEditor into a Windows executable
REM
REM Usage:
REM   build_windows.bat            — .exe + フォルダ形式 (dist\SimpleMarkdownEditor\)
REM   build_windows.bat --onefile  — 単一 .exe (dist\SimpleMarkdownEditor.exe)
REM   build_windows.bat --clean    — ビルド前に build\ dist\ を削除
REM   オプションは組み合わせ可能: build_windows.bat --clean --onefile

setlocal enabledelayedexpansion

set APP_NAME=SimpleMarkdownEditor
set ENTRY=markdown_editor.py
set ONEFILE=false
set CLEAN=false

REM ── parse args ──────────────────────────────────────────────────────────────
for %%A in (%*) do (
  if "%%A"=="--onefile" set ONEFILE=true
  if "%%A"=="--clean"   set CLEAN=true
)

REM ── clean ───────────────────────────────────────────────────────────────────
if "%CLEAN%"=="true" (
  echo ^>^>^> Cleaning build\ dist\ ...
  if exist build  rmdir /s /q build
  if exist dist   rmdir /s /q dist
  if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"
)

REM ── check Python ────────────────────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] python が見つかりません。Python 3.10 以降をインストールして PATH を通してください。
  exit /b 1
)

REM ── check / install PyInstaller ─────────────────────────────────────────────
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo ^>^>^> PyInstaller not found — installing ...
  python -m pip install pyinstaller
)

REM ── build ───────────────────────────────────────────────────────────────────
echo ^>^>^> Building %APP_NAME% ...

set ARGS=--name %APP_NAME% ^
  --noconfirm ^
  --windowed ^
  --collect-all markdown ^
  --collect-all pygments ^
  --hidden-import PySide6.QtWebEngineWidgets ^
  --hidden-import PySide6.QtWebEngineCore ^
  --hidden-import PySide6.QtWebEngineQuick

if "%ONEFILE%"=="true" (
  set ARGS=!ARGS! --onefile
) else (
  set ARGS=!ARGS! --onedir
)

python -m PyInstaller %ARGS% %ENTRY%
if errorlevel 1 (
  echo [ERROR] ビルドに失敗しました。
  exit /b 1
)

REM ── result ──────────────────────────────────────────────────────────────────
echo.
echo Build complete.
if "%ONEFILE%"=="true" (
  echo   Binary : dist\%APP_NAME%.exe
) else (
  echo   Dir    : dist\%APP_NAME%\
  echo   Run    : dist\%APP_NAME%\%APP_NAME%.exe
)

endlocal
