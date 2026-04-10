#!/usr/bin/env python3
"""
Simple Markdown Editor - Python/PySide6 implementation

Requirements:
    pip install PySide6

Usage:
    python markdown_editor.py [file.md]
"""

import os
import sys
from pathlib import Path

# Ensure Qt can find its platform plugins (e.g. cocoa on macOS) when running
# inside a virtualenv.  Must be set before any PySide6 import.
#
# macOS 26+ (APFS) re-applies the UF_HIDDEN BSD flag to pip-installed .dylib
# files each time they are accessed, causing Qt's QDir (which filters out
# hidden files by default) to miss the cocoa platform plugin entirely.
# Work around this by copying the platform plugins into a user-cache directory
# that macOS does not manage, so the hidden flag is never set there.
def _fix_qt_plugin_path():
    import shutil
    import subprocess

    if "QT_QPA_PLATFORM_PLUGIN_PATH" in os.environ and os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] != "":
        return

    # Find the PySide6/PyQt6 plugins root.
    plugins_root = None
    for p in sys.path + [os.getcwd()]:
        for sub in ("PySide6/Qt/plugins", "PyQt6/Qt6/plugins"):
            candidate = Path(p) / sub
            if candidate.is_dir():
                plugins_root = candidate
                break
        if plugins_root:
            break

    if not plugins_root:
        return

    platforms_src = plugins_root / "platforms"
    if not platforms_src.is_dir():
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(plugins_root)
        return

    # On macOS, APFS re-marks pip-installed .dylib files with UF_HIDDEN on
    # every access.  Copy them to a user cache dir where that doesn't happen.
    if sys.platform == "darwin":
        cache_dir = Path.home() / "Library" / "Caches" / "SimpleMarkdownEditor" / "Qt" / "plugins" / "platforms"
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            for src in platforms_src.glob("*.dylib"):
                dst = cache_dir / src.name
                shutil.copy2(src, dst)
                # Clear the hidden BSD flag so QDir can enumerate the file.
                subprocess.run(["chflags", "nohidden", str(dst)], check=False)
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(cache_dir)
            return
        except Exception:
            pass  # Fall through to using the original path.

    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(plugins_root)

_fix_qt_plugin_path()

from PySide6.QtWidgets import QApplication

from main_window import MarkdownEditor


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Simple Markdown Editor")

    initial = sys.argv[1] if len(sys.argv) > 1 else None
    win = MarkdownEditor(initial)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
