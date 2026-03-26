"""
CodeEditor widget with line-number gutter for Simple Markdown Editor.
"""

from PySide6.QtWidgets import QWidget, QPlainTextEdit
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QFont, QPainter, QColor, QPalette

from themes import DARK, LIGHT


class _LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self._editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    """Plain-text editor with a line-number gutter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = False
        self._gutter = _LineNumberArea(self)

        font = None
        for family in ("JetBrains Mono", "Consolas", "Menlo", "Courier New"):
            f = QFont(family, 12)
            f.setStyleHint(QFont.StyleHint.Monospace)
            f.setFixedPitch(True)
            if f.exactMatch():
                font = f
                break
        if font is None:
            font = QFont()
            font.setStyleHint(QFont.StyleHint.Monospace)
            font.setFixedPitch(True)
            font.setPointSize(12)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 2)

        self.blockCountChanged.connect(self._updateGutterWidth)
        self.updateRequest.connect(self._updateGutter)
        self._updateGutterWidth(0)

    def lineNumberAreaWidth(self) -> int:
        digits = max(2, len(str(self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _updateGutterWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def _updateGutter(self, rect, dy):
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._updateGutterWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._gutter.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
        )

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self._gutter)
        t = DARK if self._dark else LIGHT
        painter.fillRect(event.rect(), QColor(t["surface2"]))

        painter.setFont(self.font())
        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(t["gutter"]))
                painter.drawText(
                    0, top,
                    self._gutter.width() - 6, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(num + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            num += 1

    def applyTheme(self, dark: bool):
        self._dark = dark
        t = DARK if dark else LIGHT
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor(t["surface"]))
        pal.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
        self.setPalette(pal)
        self._gutter.update()
