"""
Main window (MarkdownEditor) for Simple Markdown Editor.
"""

import os
import re
import json
import tempfile
from pathlib import Path

import markdown

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QVBoxLayout, QFileDialog, QLabel,
    QMessageBox, QSizePolicy, QToolBar,
    QToolButton, QMenu,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage, QWebEngineDownloadRequest
from PyQt6.QtCore import Qt, QTimer, QUrl, QMarginsF
from PyQt6.QtGui import (
    QKeySequence, QTextCursor,
    QAction, QPageLayout, QPageSize,
)

from themes import DARK, LIGHT
from preview_html import _shell_html
from editor_widget import CodeEditor
from search_dialog import SearchDialog


_DEFAULT_MD = """\
# Simple Markdown Editor

Welcome to the **Simple Markdown Editor** — Python/PyQt6 edition.

## Features

- Live **preview** with syntax highlighting
- *Italic*, **bold**, ~~strikethrough~~, `inline code`
- Tables, blockquotes, code blocks, Mermaid diagrams
- Light / Dark theme

## Code Example

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("World"))
```

## Table

| Feature  | Status |
|----------|--------|
| Preview  | ✅     |
| Themes   | ✅     |
| Search   | ✅     |
| Mermaid  | ✅     |

## Mermaid Diagram

```mermaid
graph TD
  A[Open file] --> B{Edit}
  B --> C[Save]
  B --> D[Preview]
```

> Start writing — preview updates automatically.
"""


class MarkdownEditor(QMainWindow):
    def __init__(self, initial_file=None):  # type: (str | None) -> None
        super().__init__()
        self._dark = False
        self._file = None  # Optional[str]
        self._modified = False
        self._search_dlg: SearchDialog | None = None
        self._font_size = 14  # base font size (pt for editor, px for preview)

        self._preview_timer = QTimer(singleShot=True, interval=300)
        self._preview_timer.timeout.connect(self._updatePreview)

        self._initUI()
        self._applyTheme()          # loads preview page

        if initial_file and Path(initial_file).exists():
            self._loadFile(initial_file)
        else:
            self.editor.setPlainText(_DEFAULT_MD)
            self._modified = False
            self._refreshTitle()

    # ── UI construction

    def _initUI(self):
        self.setWindowTitle("Markdown Editor")
        self.resize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        self._buildToolbar()

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Editor pane
        ep = QWidget()
        el = QVBoxLayout(ep)
        el.setContentsMargins(0, 0, 0, 0)
        el.setSpacing(0)
        self._editorLabel = QLabel("EDITOR")
        self._editorLabel.setObjectName("pane-label")
        self._editorLabel.setFixedHeight(18)
        self.editor = CodeEditor()
        self.editor.textChanged.connect(self._onTextChanged)
        self.editor.cursorPositionChanged.connect(self._updateStatus)
        el.addWidget(self._editorLabel)
        el.addWidget(self.editor)

        # Preview pane
        pp = QWidget()
        pl = QVBoxLayout(pp)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)
        self._previewLabel = QLabel("PREVIEW")
        self._previewLabel.setObjectName("pane-label")
        self._previewLabel.setFixedHeight(18)
        self.preview = QWebEngineView()
        # file:// pages need this to load CDN scripts (mermaid.js)
        self.preview.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        # Auto-grant clipboard write permission (needed for Copy PNG)
        self.preview.page().featurePermissionRequested.connect(self._grantPermission)
        # Handle SVG/PNG downloads triggered by <a download> in the page
        self.preview.page().profile().downloadRequested.connect(self._onDownloadRequested)
        pl.addWidget(self._previewLabel)
        pl.addWidget(self.preview)

        self.splitter.addWidget(ep)
        self.splitter.addWidget(pp)
        self.splitter.setSizes([640, 640])
        vbox.addWidget(self.splitter)

        self._buildStatusBar()

    def _buildToolbar(self):
        # ── 1段目: File / フォントサイズ / ファイル名 / テーマ / 検索 ──────────
        tb1 = QToolBar("ファイルツールバー")
        tb1.setMovable(False)
        tb1.setObjectName("main-tb")
        self.addToolBar(tb1)

        def act(tb, label, tip, cb, shortcut=None):
            a = QAction(label, self)
            a.setToolTip(tip)
            a.triggered.connect(cb)
            if shortcut:
                a.setShortcut(QKeySequence(shortcut))
            tb.addAction(a)
            return a

        # File メニュー
        file_menu = QMenu(self)
        file_menu.addAction("📄  New",       self._newFile).setShortcut(QKeySequence("Ctrl+N"))
        file_menu.addAction("📂  Open",      self._openFile).setShortcut(QKeySequence("Ctrl+O"))
        file_menu.addSeparator()
        file_menu.addAction("💾  Save",      self._saveFile).setShortcut(QKeySequence("Ctrl+S"))
        file_menu.addAction("💾  Save As…",  self._saveFileAs)
        file_menu.addSeparator()
        file_menu.addAction("📑  Export PDF…", self._exportPdf).setShortcut(QKeySequence("Ctrl+Shift+E"))

        self._file_btn = QToolButton()
        self._file_btn.setText("File ▾")
        self._file_btn.setObjectName("file-btn")
        self._file_btn.setMenu(file_menu)
        self._file_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        tb1.addWidget(self._file_btn)

        # ☀ 🔍
        tb1.addSeparator()
        self._themeAct = act(tb1, "☀", "テーマ切り替え", self._toggleTheme)
        act(tb1, "🔍", "検索・置換 (Ctrl+F)", self._showSearch, "Ctrl+F")

        # A− 14px A+
        tb1.addSeparator()
        act(tb1, "A−", "文字を小さく", self._fontSizeDown)
        self._fontSizeLabel = QLabel(f"{self._font_size}px")
        self._fontSizeLabel.setObjectName("font-size-label")
        self._fontSizeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fontSizeLabel.setFixedWidth(36)
        tb1.addWidget(self._fontSizeLabel)
        act(tb1, "A+", "文字を大きく", self._fontSizeUp)

        # スペーサー → ファイル名
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb1.addWidget(spacer)

        self._filenameLabel = QLabel("untitled.md")
        self._filenameLabel.setObjectName("filename-label")
        tb1.addWidget(self._filenameLabel)

        # ── 2段目: 編集アイコン ───────────────────────────────────────────────
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        tb2 = QToolBar("編集ツールバー")
        tb2.setMovable(False)
        tb2.setObjectName("edit-tb")
        self.addToolBar(tb2)

        act(tb2, "H1", "見出し 1",              lambda: self._insert("heading1"))
        act(tb2, "H2", "見出し 2",              lambda: self._insert("heading2"))
        act(tb2, "H3", "見出し 3",              lambda: self._insert("heading3"))
        tb2.addSeparator()
        act(tb2, "B",       "太字 (Ctrl+B)",    lambda: self._insert("bold"),      "Ctrl+B")
        act(tb2, "I",       "斜体 (Ctrl+I)",    lambda: self._insert("italic"),    "Ctrl+I")
        act(tb2, "~~",      "打ち消し線",        lambda: self._insert("strikethrough"))
        act(tb2, "`",       "インラインコード",  lambda: self._insert("inlinecode"))
        tb2.addSeparator()
        act(tb2, "• List",  "箇条書き",          lambda: self._insert("ul"))
        act(tb2, "1. List", "番号付きリスト",    lambda: self._insert("ol"))
        act(tb2, "> Quote", "引用",              lambda: self._insert("blockquote"))
        act(tb2, "``` Code","コードブロック",    lambda: self._insert("codeblock"))
        act(tb2, "Mermaid", "Mermaid ダイアグラム", lambda: self._insert("mermaid"))
        act(tb2, "Table",   "テーブル",          lambda: self._insert("table"))
        act(tb2, "Link",    "リンク (Ctrl+K)",   lambda: self._insert("link"),     "Ctrl+K")
        act(tb2, "---",     "水平線",            lambda: self._insert("hr"))

    def _buildStatusBar(self):
        sb = self.statusBar()
        sb.setObjectName("statusbar")
        self._lnColLbl  = QLabel("Ln 1, Col 1")
        self._wordsLbl  = QLabel("0 words")
        self._charsLbl  = QLabel("0 chars")
        badge = QLabel("Python / PyQt6")
        badge.setObjectName("badge")
        sb.addWidget(self._lnColLbl)
        sb.addWidget(QLabel("|"))
        sb.addWidget(self._wordsLbl)
        sb.addWidget(QLabel("|"))
        sb.addWidget(self._charsLbl)
        sb.addPermanentWidget(badge)

    # ── Markdown → HTML (Python-side, no CDN) ─────────────────────────────────

    def _mdToHtml(self, text: str) -> str:
        """Convert Markdown to HTML using the markdown library + Pygments."""
        # Pre-process: ~~strikethrough~~ (not in standard markdown)
        text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
        # Pre-process: ```mermaid blocks → <div class="mermaid"> for mermaid.js
        def mermaid_block(m):
            code = m.group(1).strip()
            import html as _html
            attr = _html.escape(code, quote=True)  # safe for data-src attribute
            return f'\n<div class="mermaid" data-src="{attr}">{code}</div>\n'
        text = re.sub(r'```mermaid\n(.*?)```', mermaid_block, text, flags=re.DOTALL)

        return markdown.markdown(
            text,
            extensions=[
                'markdown.extensions.extra',    # tables, fenced_code, footnotes…
                'markdown.extensions.codehilite',
                'markdown.extensions.nl2br',
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'codehilite',
                    'linenums': False,
                    'guess_lang': False,
                },
            },
        )

    def _reloadPreview(self):
        """Write shell HTML to a temp file and load via file:// so CDN scripts work."""
        t = DARK if self._dark else LIGHT
        html = _shell_html(t, self._dark)
        if not hasattr(self, '_tmp_html'):
            fd, path = tempfile.mkstemp(suffix='.html', prefix='md_preview_')
            os.close(fd)
            self._tmp_html = path
        with open(self._tmp_html, 'w', encoding='utf-8') as f:
            f.write(html)
        try:
            self.preview.loadFinished.disconnect(self._onPageLoaded)
        except Exception:
            pass
        self.preview.loadFinished.connect(self._onPageLoaded)
        self.preview.load(QUrl.fromLocalFile(self._tmp_html))

    def _onPageLoaded(self, ok: bool):
        try:
            self.preview.loadFinished.disconnect(self._onPageLoaded)
        except Exception:
            pass
        if ok:
            self._updatePreview()

    def _updatePreview(self):
        """Re-render content, inject HTML, run mermaid, then attach action buttons."""
        body_html = self._mdToHtml(self.editor.toPlainText())
        js_string = json.dumps(body_html)
        self.preview.page().runJavaScript(f"""\
document.getElementById('content').innerHTML = {js_string};
if (typeof mermaid !== 'undefined') {{
    mermaid.run({{ nodes: document.querySelectorAll('.mermaid') }})
        .then(() => {{
            document.querySelectorAll('.mermaid').forEach((el, idx) => {{
                addDiagramActions(el, idx);
            }});
        }});
}}
""")

    # ── Text / status

    def _onTextChanged(self):
        self._modified = True
        self._refreshTitle()
        self._updateStatus()
        self._preview_timer.start()

    def _updateStatus(self):
        cursor = self.editor.textCursor()
        ln  = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        text  = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        self._lnColLbl.setText(f"Ln {ln}, Col {col}")
        self._wordsLbl.setText(f"{words} words")
        self._charsLbl.setText(f"{len(text)} chars")

    def _refreshTitle(self):
        name = Path(self._file).name if self._file else "untitled.md"
        dot  = " ●" if self._modified else ""
        self.setWindowTitle(f"Markdown Editor — {name}{dot}")
        self._filenameLabel.setText(name + dot)

    # ── Insert helpers

    def _insert(self, kind: str):
        c = self.editor.textCursor()
        sel = c.selectedText()

        def wrap(w: str, placeholder: str):
            text = sel if sel else placeholder
            c.insertText(f"{w}{text}{w}")
            if not sel:
                pos = c.position()
                c.setPosition(pos - len(w) - len(text))
                c.setPosition(pos - len(w), QTextCursor.MoveMode.KeepAnchor)
                self.editor.setTextCursor(c)

        def prefix(p: str):
            c.movePosition(QTextCursor.MoveOperation.StartOfLine)
            c.insertText(p)

        if kind == "heading1":   prefix("# ")
        elif kind == "heading2":   prefix("## ")
        elif kind == "heading3":   prefix("### ")
        elif kind == "bold":       wrap("**", "太字")
        elif kind == "italic":     wrap("*",  "斜体")
        elif kind == "strikethrough": wrap("~~", "テキスト")
        elif kind == "inlinecode": wrap("`",  "code")
        elif kind == "ul":         prefix("- ")
        elif kind == "ol":         prefix("1. ")
        elif kind == "blockquote": prefix("> ")
        elif kind == "hr":         c.insertText("\n---\n")
        elif kind == "link":
            if sel:
                c.insertText(f"[{sel}](https://example.com)")
            else:
                c.insertText("[リンクテキスト](https://example.com)")
        elif kind == "codeblock":
            body = sel if sel else "code"
            c.insertText(f"```\n{body}\n```")
        elif kind == "mermaid":
            c.insertText("```mermaid\ngraph TD\n  A[Start] --> B[End]\n```")
        elif kind == "table":
            c.insertText(
                "| 列1 | 列2 | 列3 |\n"
                "|-----|-----|-----|\n"
                "| セル | セル | セル |\n"
            )

        self.editor.setFocus()

    # ── File operations

    def _loadFile(self, path: str):
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self._file = path
        self._modified = False
        self.editor.setPlainText(content)
        self._modified = False
        self._refreshTitle()

    def _newFile(self):
        if not self._confirmDiscard():
            return
        self._file = None
        self._modified = False
        self.editor.setPlainText("")
        self._refreshTitle()

    def _openFile(self):
        if not self._confirmDiscard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "ファイルを開く", "",
            "Markdown Files (*.md *.markdown);;Text Files (*.txt);;All Files (*)",
        )
        if path:
            self._loadFile(path)

    def _saveFile(self):
        if not self._file:
            self._saveFileAs()
            return
        with open(self._file, "w", encoding="utf-8") as f:
            f.write(self.editor.toPlainText())
        self._modified = False
        self._refreshTitle()

    def _saveFileAs(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "名前を付けて保存", "untitled.md",
            "Markdown Files (*.md *.markdown);;Text Files (*.txt);;All Files (*)",
        )
        if path:
            self._file = path
            self._saveFile()

    def _exportPdf(self):
        stem = Path(self._file).stem if self._file else "document"
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF として保存", f"{stem}.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(15, 15, 15, 15),
        )
        self.preview.page().printToPdf(path, layout)

    def _confirmDiscard(self) -> bool:
        if not self._modified:
            return True
        r = QMessageBox.question(
            self, "確認", "変更を保存しますか？",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
        )
        if r == QMessageBox.StandardButton.Save:
            self._saveFile()
            return True
        return r == QMessageBox.StandardButton.Discard

    # ── Theme / font size

    def _fontSizeUp(self):
        if self._font_size < 32:
            self._font_size += 1
            self._applyFontSize()

    def _fontSizeDown(self):
        if self._font_size > 8:
            self._font_size -= 1
            self._applyFontSize()

    def _applyFontSize(self):
        self._fontSizeLabel.setText(f"{self._font_size}px")
        # Editor
        font = self.editor.font()
        font.setPointSize(self._font_size)
        self.editor.setFont(font)
        self.editor.setTabStopDistance(
            self.editor.fontMetrics().horizontalAdvance(" ") * 2
        )
        # Preview (body text + mermaid re-render with new fontSize)
        self.preview.page().runJavaScript(
            f"applyFontSize({self._font_size});"
        )

    def _toggleTheme(self):
        self._dark = not self._dark
        self._applyTheme()

    def _applyTheme(self):
        t = DARK if self._dark else LIGHT
        self.editor.applyTheme(self._dark)
        self._themeAct.setText("🌙" if self._dark else "☀")

        # QSS for chrome widgets
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {t["bg"]}; color: {t["text"]}; }}
            QToolBar#main-tb, QToolBar#edit-tb {{
                background: {t["toolbar_bg"]};
                border-bottom: 1px solid {t["border"]};
                padding: 4px 6px; spacing: 2px;
            }}
            QToolBar#main-tb QToolButton, QToolBar#edit-tb QToolButton {{
                background: transparent; color: {t["text"]};
                border: none; border-radius: 4px; padding: 4px 9px;
                font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace;
                font-size: 11px; font-weight: 500;
            }}
            QToolBar#main-tb QToolButton:hover, QToolBar#edit-tb QToolButton:hover {{
                background: {t["surface2"]}; color: {t["accent"]};
            }}
            QToolBar#main-tb QToolButton#file-btn {{
                background: {"#1e3550" if self._dark else "#ddeeff"};
                color:      {"#7ab8f5" if self._dark else "#1a5a9a"};
                border: 1px solid {"#3a6090" if self._dark else "#7ab0de"};
                border-radius: 4px;
            }}
            QToolBar#main-tb QToolButton#file-btn:hover,
            QToolBar#main-tb QToolButton#file-btn:pressed,
            QToolBar#main-tb QToolButton#file-btn[popupMode="1"] {{
                background: #2a72c0; color: #ffffff;
                border-color: #2a72c0;
            }}
            QMenu {{
                background: {t["surface"]}; color: {t["text"]};
                border: 1px solid {t["border"]}; border-radius: 4px;
                padding: 4px 0;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background: #2a72c0; color: #ffffff; border-radius: 3px;
            }}
            QMenu::separator {{
                height: 1px; background: {t["border"]}; margin: 3px 8px;
            }}
            QLabel#pane-label {{
                font-size: 10px; font-weight: 600; letter-spacing: 0.08em;
                text-transform: uppercase;
                color: {t["text2"]}; background: {t["surface2"]};
                border-bottom: 1px solid {t["border"]}; padding: 1px 14px;
                max-height: 18px;
            }}
            QLabel#filename-label {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px; color: {t["text2"]}; padding: 0 8px;
            }}
            QLabel#font-size-label {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px; color: {t["text2"]};
            }}
            QLabel#badge {{
                background: #2a5a8a; color: #fff;
                font-size: 10px; padding: 2px 8px; border-radius: 10px;
            }}
            QStatusBar#statusbar {{
                background: {t["status_bg"]}; border-top: 1px solid {t["border"]};
                font-family: 'JetBrains Mono', monospace; font-size: 10px;
                color: {t["text2"]};
            }}
            QStatusBar#statusbar QLabel {{
                color: {t["text2"]}; font-family: 'JetBrains Mono', monospace;
                font-size: 10px; padding: 0 4px;
            }}
            QSplitter::handle {{ background: {t["border"]}; width: 1px; }}
            QDialog {{ background: {t["surface"]}; color: {t["text"]}; }}
            QLineEdit {{
                background: {t["surface2"]}; color: {t["text"]};
                border: 1px solid {t["border"]}; border-radius: 4px; padding: 4px 8px;
            }}
            QLineEdit:focus {{ border-color: {t["accent"]}; }}
            QPushButton {{
                background: {t["surface2"]}; color: {t["text"]};
                border: 1px solid {t["border"]}; border-radius: 4px; padding: 4px 10px;
            }}
            QPushButton:hover {{ background: {t["accent_bg"]}; color: {t["accent"]}; }}
            QCheckBox {{ color: {t["text2"]}; }}
        """)

        self._reloadPreview()

    # ── Search / download

    def _grantPermission(self, url, feature):
        """Auto-grant browser feature permissions (clipboard write, etc.)."""
        self.preview.page().setFeaturePermission(
            url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
        )

    def _onDownloadRequested(self, download: QWebEngineDownloadRequest):
        """Handle file downloads from the preview (SVG download button)."""
        suggested = download.suggestedFileName() or "diagram.svg"
        path, _ = QFileDialog.getSaveFileName(self, "保存", suggested)
        if path:
            download.setDownloadDirectory(str(Path(path).parent))
            download.setDownloadFileName(Path(path).name)
            download.accept()
        else:
            download.cancel()

    def _showSearch(self):
        if self._search_dlg is None:
            self._search_dlg = SearchDialog(self.editor, self)
        self._search_dlg.popup()

    # ── Window events

    def closeEvent(self, event):
        if self._confirmDiscard():
            if hasattr(self, '_tmp_html') and os.path.exists(self._tmp_html):
                os.unlink(self._tmp_html)
            event.accept()
        else:
            event.ignore()
