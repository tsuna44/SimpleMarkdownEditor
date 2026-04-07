@echo off
REM build_windows.bat -- Build SimpleMarkdownEditor into a Windows executable
REM
REM Usage:
REM   build_windows.bat            -- .exe + folder layout (dist\SimpleMarkdownEditor\)
REM   build_windows.bat --onefile  -- single .exe (dist\SimpleMarkdownEditor.exe)
REM   build_windows.bat --clean    -- delete build\ dist\ before building
REM   Options can be combined: build_windows.bat --clean --onefile

setlocal enabledelayedexpansion

set APP_NAME=SimpleMarkdownEditor
set ENTRY=markdown_editor.py
set ONEFILE=false
set CLEAN=false

REM -- parse args ---------------------------------------------------------------
for %%A in (%*) do (
  if "%%A"=="--onefile" set ONEFILE=true
  if "%%A"=="--clean"   set CLEAN=true
)

REM -- clean --------------------------------------------------------------------
if "%CLEAN%"=="true" (
  echo ^>^>^> Cleaning build\ dist\ ...
  if exist build  rmdir /s /q build
  if exist dist   rmdir /s /q dist
  if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"
)

REM -- check Python -------------------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] python not found. Please install Python 3.10 or later and add it to PATH.
  exit /b 1
)

REM -- check / install PyInstaller ----------------------------------------------
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo ^>^>^> PyInstaller not found -- installing ...
  python -m pip install pyinstaller
)

REM -- build --------------------------------------------------------------------
echo ^>^>^> Building %APP_NAME% ...

set ARGS=--name %APP_NAME% ^
  --noconfirm ^
  --windowed ^
  --collect-all markdown ^
  --collect-all pygments ^
  --hidden-import PySide6.QtWebEngineWidgets ^
  --hidden-import PySide6.QtWebEngineCore ^
  --hidden-import PySide6.QtWebEngineQuick ^
  --add-data "..\vendor\mermaid.min.js;vendor" ^
  --add-data "..\vendor\VERSIONS.json;vendor" ^
  --add-data "..\vendor\plantuml.jar;."

if "%ONEFILE%"=="true" (
  set ARGS=!ARGS! --onefile
) else (
  set ARGS=!ARGS! --onedir
)

python -m PyInstaller %ARGS% %ENTRY%
if errorlevel 1 (
  echo [ERROR] Build failed.
  exit /b 1
)

REM -- result -------------------------------------------------------------------
echo.
echo Build complete.
if "%ONEFILE%"=="true" (
  echo   Binary : dist\%APP_NAME%.exe
) else (
  echo   Dir    : dist\%APP_NAME%\
  echo   Run    : dist\%APP_NAME%\%APP_NAME%.exe
)

endlocal
