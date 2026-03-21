#!/usr/bin/env python3
"""
Simple Markdown Editor - Python/PyQt6 implementation

Requirements:
    pip install PyQt6 PyQt6-WebEngine

Usage:
    python markdown_editor.py [file.md]
"""

import sys

from PyQt6.QtWidgets import QApplication

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
