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
def _fix_qt_plugin_path():
    if "QT_QPA_PLATFORM_PLUGIN_PATH" in os.environ:
        return
    # PySide6 uses Qt/plugins; PyQt6 uses Qt6/plugins
    for p in sys.path:
        for sub in ("PySide6/Qt/plugins", "PyQt6/Qt6/plugins"):
            candidate = Path(p) / sub
            if candidate.is_dir():
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(candidate)
                return

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
