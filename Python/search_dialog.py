"""
Search & Replace dialog for Simple Markdown Editor.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QCheckBox, QLabel,
)
from PySide6.QtGui import QTextCursor, QTextDocument

from editor_widget import CodeEditor


class SearchDialog(QDialog):
    def __init__(self, editor: CodeEditor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("検索・置換")
        self.setModal(False)
        self.resize(420, 120)

        lay = QVBoxLayout(self)
        lay.setSpacing(6)

        # ── search row
        row1 = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("検索...")
        self.case_cb = QCheckBox("Aa")
        self.case_cb.setToolTip("大文字小文字を区別")
        self.regex_cb = QCheckBox(".*")
        self.regex_cb.setToolTip("正規表現")
        self.prev_btn = QPushButton("↑")
        self.prev_btn.setFixedWidth(30)
        self.next_btn = QPushButton("↓")
        self.next_btn.setFixedWidth(30)
        self.count_lbl = QLabel("")
        self.count_lbl.setMinimumWidth(60)
        row1.addWidget(self.search_edit)
        row1.addWidget(self.case_cb)
        row1.addWidget(self.regex_cb)
        row1.addWidget(self.prev_btn)
        row1.addWidget(self.next_btn)
        row1.addWidget(self.count_lbl)
        lay.addLayout(row1)

        # ── replace row
        row2 = QHBoxLayout()
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("置換...")
        self.rep_one_btn = QPushButton("置換")
        self.rep_all_btn = QPushButton("すべて置換")
        row2.addWidget(self.replace_edit)
        row2.addWidget(self.rep_one_btn)
        row2.addWidget(self.rep_all_btn)
        lay.addLayout(row2)

        self._matches: list[QTextCursor] = []
        self._cur = -1

        self.search_edit.textChanged.connect(self._search)
        self.case_cb.toggled.connect(self._search)
        self.regex_cb.toggled.connect(self._search)
        self.next_btn.clicked.connect(self._next)
        self.prev_btn.clicked.connect(self._prev)
        self.rep_one_btn.clicked.connect(self._replace_one)
        self.rep_all_btn.clicked.connect(self._replace_all)

    # ── internals

    def _find_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.case_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def _search(self):
        from PySide6.QtCore import QRegularExpression
        pattern = self.search_edit.text()
        self._matches = []
        self._cur = -1
        if not pattern:
            self.count_lbl.setText("")
            return

        doc = self.editor.document()
        flags = self._find_flags()
        cursor = QTextCursor(doc)

        while True:
            if self.regex_cb.isChecked():
                re_flags = QRegularExpression.PatternOption(0)
                if not self.case_cb.isChecked():
                    re_flags = QRegularExpression.PatternOption.CaseInsensitiveOption
                cursor = doc.find(QRegularExpression(pattern, re_flags), cursor)
            else:
                cursor = doc.find(pattern, cursor, flags)
            if cursor.isNull():
                break
            self._matches.append(QTextCursor(cursor))

        total = len(self._matches)
        if total:
            self._cur = 0
            self._highlight()
        else:
            self.count_lbl.setText("0件")

    def _highlight(self):
        if self._matches and 0 <= self._cur < len(self._matches):
            self.editor.setTextCursor(self._matches[self._cur])
            self.count_lbl.setText(f"{self._cur + 1}/{len(self._matches)}")

    def _next(self):
        if not self._matches:
            self._search()
            return
        self._cur = (self._cur + 1) % len(self._matches)
        self._highlight()

    def _prev(self):
        if not self._matches:
            self._search()
            return
        self._cur = (self._cur - 1) % len(self._matches)
        self._highlight()

    def _replace_one(self):
        if self._matches and 0 <= self._cur < len(self._matches):
            self._matches[self._cur].insertText(self.replace_edit.text())
            self._search()

    def _replace_all(self):
        self._search()
        n = len(self._matches)
        c = self.editor.textCursor()
        c.beginEditBlock()
        for m in reversed(self._matches):
            m.insertText(self.replace_edit.text())
        c.endEditBlock()
        self._search()
        self.count_lbl.setText(f"{n}件置換")

    def popup(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_edit.setFocus()
        self.search_edit.selectAll()
