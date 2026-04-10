"""
Main window (MarkdownEditor) for Simple Markdown Editor.
"""

import os
import re
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import markdown

# ── PlantUML command detection ───────────────────────────────────────────────

def _vendor_dir() -> Path:
    """Shared vendor directory — works both in dev and PyInstaller (sys._MEIPASS) builds."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "vendor"  # type: ignore[attr-defined]
    return Path(__file__).parent.parent / "vendor"


def _puml_jar_path() -> Path:
    """Return path to bundled plantuml.jar (works in dev and PyInstaller builds)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "plantuml.jar"  # type: ignore[attr-defined]
    return _vendor_dir() / "plantuml.jar"


def _load_versions() -> dict:
    """Load vendor library versions from vendor/VERSIONS.json."""
    try:
        versions_path = _vendor_dir() / "VERSIONS.json"
        import json as _json
        with open(versions_path, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return {}


def _make_puml_candidates() -> list[list[str]]:
    jar = str(_puml_jar_path())
    return [
        ["plantuml"],
        ["plantuml.sh"],
        ["java", "-jar", jar],
        ["/opt/homebrew/opt/openjdk/bin/java", "-jar", jar],
        ["/usr/local/opt/openjdk/bin/java",    "-jar", jar],
        ["java", "-jar", "/usr/local/opt/plantuml/libexec/plantuml.jar"],
        ["java", "-jar", "/opt/homebrew/opt/plantuml/libexec/plantuml.jar"],
        ["java", "-jar", "/usr/share/plantuml/plantuml.jar"],
        ["java", "-jar", "/usr/share/java/plantuml.jar"],
        ["java", "-jar", "/usr/local/share/plantuml/plantuml.jar"],
    ]


_PUML_CANDIDATES: list[list[str]] = _make_puml_candidates()
_PUML_CMD = None      # type: list[str] | None
_PUML_CHECKED = False
_PUML_CACHE = {}      # {normalized_src: svg_or_error_html}
_PUML_CACHE_MAX = 50


def _normalize_puml(code: str) -> str:
    src = code.strip()
    if not src.startswith("@start"):
        src = f"@startuml\n{src}\n@enduml"
    return src


def _detect_plantuml():
    global _PUML_CMD, _PUML_CHECKED
    if _PUML_CHECKED:
        return _PUML_CMD
    _PUML_CHECKED = True
    for cmd in _PUML_CANDIDATES:
        exe = cmd[0]
        if shutil.which(exe) is None and not Path(exe).is_file():
            if len(cmd) >= 3 and cmd[1] == "-jar":
                if not Path(cmd[2]).is_file():
                    continue
            elif exe not in ("java",):
                continue
        try:
            probe = b"@startuml\nA -> B\n@enduml\n"
            r = subprocess.run(
                cmd + ["-tsvg", "-pipe", "-charset", "UTF-8"],
                input=probe, capture_output=True, timeout=10,
            )
            if r.returncode == 0 and b"<svg" in r.stdout:
                _PUML_CMD = cmd
                return _PUML_CMD
        except Exception:
            continue
    return None


def _render_plantuml_svg(code: str) -> str:
    src = _normalize_puml(code)
    if src in _PUML_CACHE:
        return _PUML_CACHE[src]
    result = _do_render_plantuml(src)
    if len(_PUML_CACHE) >= _PUML_CACHE_MAX:
        _PUML_CACHE.pop(next(iter(_PUML_CACHE)))
    _PUML_CACHE[src] = result
    return result


def _do_render_plantuml(src: str) -> str:
    cmd = _detect_plantuml()
    if cmd is None:
        return (
            '<div class="plantuml-error">'
            "⚠ PlantUML が見つかりません。インストールしてください。<br>"
            "<code>brew install plantuml</code>  (macOS) / "
            "<code>sudo apt install plantuml</code>  (Ubuntu)"
            "</div>"
        )
    try:
        r = subprocess.run(
            cmd + ["-tsvg", "-pipe", "-charset", "UTF-8"],
            input=src.encode("utf-8"), capture_output=True, timeout=20,
        )
        if r.returncode != 0:
            err = r.stderr.decode("utf-8", errors="replace")[:300]
            return f'<div class="plantuml-error">⚠ PlantUML エラー:<br><pre>{err}</pre></div>'
        svg = r.stdout.decode("utf-8", errors="replace")
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)
        return svg.strip()
    except subprocess.TimeoutExpired:
        return '<div class="plantuml-error">⚠ PlantUML タイムアウトしました。</div>'
    except Exception as e:
        return f'<div class="plantuml-error">⚠ PlantUML 実行エラー: {e}</div>'


# ── Qt imports ────────────────────────────────────────────────────────────────

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QTabWidget,
    QVBoxLayout, QFileDialog, QLabel,
    QMessageBox, QSizePolicy, QToolBar,
    QToolButton, QMenu, QListWidget, QListWidgetItem, QDockWidget,
    QTreeView, QFileSystemModel,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage, QWebEngineDownloadRequest
from PySide6.QtCore import Qt, QTimer, QUrl, QMarginsF, Signal, QSettings, QStandardPaths
from PySide6.QtGui import (
    QKeySequence, QTextCursor,
    QAction, QPageLayout, QPageSize,
)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from themes import DARK, LIGHT
from preview_html import _shell_html
from editor_widget import CodeEditor
from search_dialog import SearchDialog


# ── Preview page (intercepts link navigation) ─────────────────────────────────

class _PreviewPage(QWebEnginePage):
    """QWebEnginePage that intercepts link clicks in the markdown preview.

    * http/https links  → open in the system browser
    * file:// .md links → ask the main window to open the file in a tab
    * file:// other     → allow (images, etc.)
    * file not found    → recover the preview instead of showing an error page
    """

    def __init__(self, tab: 'EditorTab', parent=None):
        super().__init__(parent)
        self._tab = tab

    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool) -> bool:
        NT = QWebEnginePage.NavigationType
        # Always allow our programmatic loads and reloads
        if nav_type in (NT.NavigationTypeTyped, NT.NavigationTypeReload,
                        NT.NavigationTypeBackForward):
            return True
        # Let sub-frame navigations (iframes, etc.) through unchanged
        if not is_main_frame:
            return True

        scheme = url.scheme()

        # ── External links ──────────────────────────────────────────────────
        if scheme in ('http', 'https'):
            import webbrowser
            webbrowser.open(url.toString())
            return False

        # ── Local file links ────────────────────────────────────────────────
        if scheme == 'file':
            local_path = url.toLocalFile()
            p = Path(local_path)

            # Anchor links within the same temp file → allow scroll.
            # Use resolve() because /tmp may be a symlink (e.g. macOS /private/tmp).
            if self._tab._tmp_html and p.resolve() == Path(self._tab._tmp_html).resolve():
                return True

            # If the resolved path doesn't exist, try re-resolving the
            # relative portion against the current editor file's directory.
            if not p.exists() and self._tab._file and self._tab._tmp_html:
                tmp_dir = Path(self._tab._tmp_html).parent
                try:
                    rel = p.relative_to(tmp_dir)
                    candidate = Path(self._tab._file).parent / rel
                    if candidate.exists():
                        p = candidate
                except ValueError:
                    pass

            if p.exists():
                if p.suffix.lower() in ('.md', '.markdown', '.txt'):
                    # Open the linked file in the editor
                    win = self._tab.window()
                    if hasattr(win, '_openOrSwitchToFile'):
                        path_str = str(p)
                        QTimer.singleShot(0, lambda: win._openOrSwitchToFile(path_str))
                    return False
                # Other local files (images, etc.) → let the browser handle
                return True

            # File not found — recover by re-rendering current content
            QTimer.singleShot(0, self._tab._updatePreview)
            return False

        # Block any other unknown schemes
        return False


# ── Outline panel ─────────────────────────────────────────────────────────────

class OutlinePanel(QWidget):
    """Heading outline panel — shows H1/H2/H3 as a clickable list."""

    jumpTo = Signal(int)  # 0-based line number

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lbl = QLabel("OUTLINE")
        lbl.setObjectName("pane-label")
        lbl.setFixedHeight(18)
        lay.addWidget(lbl)

        self._list = QListWidget()
        self._list.setObjectName("outline-list")
        self._list.setFrameShape(QListWidget.Shape.NoFrame)
        self._list.itemClicked.connect(self._onItemClicked)
        lay.addWidget(self._list)

    def refresh(self, text: str):
        self._list.clear()
        for lineno, line in enumerate(text.splitlines()):
            m = re.match(r'^(#{1,3})\s+(.+)$', line)
            if not m:
                continue
            level = len(m.group(1))
            title = m.group(2).strip()
            item = QListWidgetItem("  " * (level - 1) + title)
            item.setData(Qt.ItemDataRole.UserRole, lineno)
            f = item.font()
            f.setBold(level == 1)
            item.setFont(f)
            self._list.addItem(item)

    def _onItemClicked(self, item: QListWidgetItem):
        self.jumpTo.emit(item.data(Qt.ItemDataRole.UserRole))


# ── File tree panel ───────────────────────────────────────────────────────────

class FileTreePanel(QWidget):
    """File tree panel — shows .md/.markdown/.txt files in a directory."""

    openFile = Signal(str)  # emitted with absolute path when a file is double-clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lbl = QLabel("FILES")
        lbl.setObjectName("pane-label")
        lbl.setFixedHeight(18)
        lay.addWidget(lbl)

        self._model = QFileSystemModel()
        self._model.setNameFilters(["*.md", "*.markdown", "*.txt"])
        self._model.setNameFilterDisables(False)  # hide non-matching files

        self._tree = QTreeView()
        self._tree.setObjectName("file-tree")
        self._tree.setModel(self._model)
        self._tree.setFrameShape(QTreeView.Shape.NoFrame)
        self._tree.setHeaderHidden(True)
        for col in range(1, 4):  # hide size / type / date columns
            self._tree.hideColumn(col)
        self._tree.setAnimated(False)
        self._tree.setIndentation(16)
        self._tree.doubleClicked.connect(self._onDoubleClicked)
        lay.addWidget(self._tree)

        self._root_path = ""
        self.setRootPath(str(Path.home()))

    def setRootPath(self, path: str):
        """Change the root directory shown in the tree."""
        p = Path(path)
        if not p.is_dir() or str(p) == self._root_path:
            return
        self._root_path = str(p)
        self._model.setRootPath(self._root_path)
        self._tree.setRootIndex(self._model.index(self._root_path))

    def _onDoubleClicked(self, index):
        path = self._model.filePath(index)
        if Path(path).is_file():
            self.openFile.emit(path)


_RECENT_MAX = 10

_DEFAULT_MD = """\
# Simple Markdown Editor

Welcome to the **Simple Markdown Editor** — Python/PySide6 edition.

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

| Feature   | Status |
|-----------|--------|
| Preview   | ✅     |
| Themes    | ✅     |
| Search    | ✅     |
| Mermaid   | ✅     |
| PlantUML  | ✅     |

## Mermaid Diagram

```mermaid
graph TD
  A[Open file] --> B{Edit}
  B --> C[Save]
  B --> D[Preview]
```

## PlantUML Diagram

```plantuml
@startuml
actor User
User -> Editor : Open file
Editor -> Preview : Render Markdown
Preview --> User : Show result
@enduml
```

> Start writing — preview updates automatically.
"""


# ── EditorTab ─────────────────────────────────────────────────────────────────

class EditorTab(QWidget):
    """A single editor + preview pane that lives inside a QTabWidget tab."""

    titleChanged = Signal(str)  # emitted when filename or modified-flag changes

    def __init__(self, dark=False, font_size=14, parent=None):
        super().__init__(parent)
        self._dark = dark
        self._file = None         # str | None
        self._modified = False
        self._font_size = font_size
        self._tmp_html = None     # str | None  (temp file for preview)
        self._search_dlg = None   # SearchDialog | None

        self._preview_timer = QTimer(singleShot=True, interval=300)
        self._preview_timer.timeout.connect(self._updatePreview)

        self._buildUI()

    # ── UI

    def _buildUI(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Editor side
        ep = QWidget()
        el = QVBoxLayout(ep)
        el.setContentsMargins(0, 0, 0, 0)
        el.setSpacing(0)
        lbl_e = QLabel("EDITOR")
        lbl_e.setObjectName("pane-label")
        lbl_e.setFixedHeight(18)
        self.editor = CodeEditor()
        self.editor.textChanged.connect(self._onTextChanged)
        el.addWidget(lbl_e)
        el.addWidget(self.editor)

        # Preview side
        pp = QWidget()
        pl = QVBoxLayout(pp)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)
        lbl_p = QLabel("PREVIEW")
        lbl_p.setObjectName("pane-label")
        lbl_p.setFixedHeight(18)
        self.preview = QWebEngineView()
        page = _PreviewPage(self, self.preview)
        self.preview.setPage(page)
        self.preview.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        self.preview.page().featurePermissionRequested.connect(self._grantPermission)
        self.preview.page().profile().downloadRequested.connect(self._onDownloadRequested)
        pl.addWidget(lbl_p)
        pl.addWidget(self.preview)

        self.splitter.addWidget(ep)
        self.splitter.addWidget(pp)
        self.splitter.setSizes([640, 640])
        lay.addWidget(self.splitter)

        # Scroll sync: editor → preview (one-directional)
        self.editor.verticalScrollBar().valueChanged.connect(self._syncScroll)

    # ── title

    def tabTitle(self) -> str:
        name = Path(self._file).name if self._file else "untitled.md"
        return name + (" ●" if self._modified else "")

    def _refreshTitle(self):
        self.titleChanged.emit(self.tabTitle())

    # ── text change

    def _onTextChanged(self):
        self._modified = True
        self._refreshTitle()
        text = self.editor.toPlainText()
        has_uncached_puml = bool(re.search(r'```plantuml\n', text)) and any(
            _normalize_puml(m.group(1)) not in _PUML_CACHE
            for m in re.finditer(r'```plantuml\n(.*?)```', text, re.DOTALL)
        )
        self._preview_timer.start(800 if has_uncached_puml else 300)

    # ── Markdown → HTML

    def _mdToHtml(self, text: str) -> str:
        text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)

        # Auto-inject markdown="1" on <details> so the md_in_html extension
        # (bundled in markdown.extensions.extra) processes Markdown inside,
        # e.g. tables, lists, code blocks.
        text = re.sub(
            r'<details(?![^>]*\bmarkdown=)([^>]*)>',
            r'<details\1 markdown="1">',
            text,
        )

        def mermaid_block(m):
            code = m.group(1).strip()
            import html as _html
            attr = _html.escape(code, quote=True)
            return f'\n<div class="mermaid" data-src="{attr}">{code}</div>\n'
        text = re.sub(r'```mermaid\n(.*?)```', mermaid_block, text, flags=re.DOTALL)

        def plantuml_block(m):
            svg_or_err = _render_plantuml_svg(m.group(1))
            return f'\n<div class="plantuml">{svg_or_err}</div>\n'
        text = re.sub(r'```plantuml\n(.*?)```', plantuml_block, text, flags=re.DOTALL)

        return markdown.markdown(
            text,
            extensions=[
                'markdown.extensions.extra',
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

    # ── preview

    def reloadPreview(self):
        """Write shell HTML to a temp file and load via file://."""
        t = DARK if self._dark else LIGHT
        html = _shell_html(t, self._dark)
        if self._tmp_html is None:
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
        else:
            # Navigation error — reload the shell and re-render current content
            QTimer.singleShot(0, self.reloadPreview)

    def _updatePreview(self):
        body_html = self._mdToHtml(self.editor.toPlainText())
        js_string = json.dumps(body_html)
        self.preview.page().runJavaScript(f"""\
document.getElementById('content').innerHTML = {js_string};
document.querySelectorAll('.plantuml').forEach((el, idx) => {{
    addDiagramActions(el, idx);
}});
if (typeof mermaid !== 'undefined') {{
    mermaid.run({{ nodes: document.querySelectorAll('.mermaid') }})
        .then(() => {{
            document.querySelectorAll('.mermaid').forEach((el, idx) => {{
                addDiagramActions(el, idx);
            }});
        }});
}}
""")
        # Re-sync scroll after content renders (allow 150 ms for layout)
        QTimer.singleShot(150, self._syncScroll)

    # ── scroll sync

    def _syncScroll(self, _value=None):
        """Sync preview scroll position to match the editor (proportional)."""
        sb = self.editor.verticalScrollBar()
        maximum = sb.maximum()
        ratio = (sb.value() / maximum) if maximum > 0 else 0.0
        self.preview.page().runJavaScript(
            f"(function(){{var h=document.body.scrollHeight-window.innerHeight;"
            f"if(h>0)window.scrollTo(0,{ratio:.6f}*h);}})();"
        )

    # ── theme / font size

    def applyTheme(self, dark: bool):
        self._dark = dark
        self.editor.applyTheme(dark)
        self.reloadPreview()

    def applyFontSize(self, size: int):
        self._font_size = size
        font = self.editor.font()
        font.setPointSize(size)
        self.editor.setFont(font)
        self.editor.setTabStopDistance(
            self.editor.fontMetrics().horizontalAdvance(" ") * 2
        )
        self.preview.page().runJavaScript(f"applyFontSize({size});")

    # ── file operations

    def loadFile(self, path: str):
        with open(path, encoding='utf-8') as f:
            content = f.read()
        self._file = path
        self._modified = False
        self.editor.setPlainText(content)
        self._modified = False
        self._refreshTitle()

    def saveFile(self) -> bool:
        """Save to current path. Returns False if no path is set."""
        if not self._file:
            return False
        with open(self._file, 'w', encoding='utf-8') as f:
            f.write(self.editor.toPlainText())
        self._modified = False
        self._refreshTitle()
        return True

    # ── insert

    def insert(self, kind: str):
        c = self.editor.textCursor()
        sel = c.selectedText()

        def wrap(w, placeholder):
            text = sel if sel else placeholder
            c.insertText(f"{w}{text}{w}")
            if not sel:
                pos = c.position()
                c.setPosition(pos - len(w) - len(text))
                c.setPosition(pos - len(w), QTextCursor.MoveMode.KeepAnchor)
                self.editor.setTextCursor(c)

        def prefix(p):
            c.movePosition(QTextCursor.MoveOperation.StartOfLine)
            c.insertText(p)

        if kind == "heading1":      prefix("# ")
        elif kind == "heading2":    prefix("## ")
        elif kind == "heading3":    prefix("### ")
        elif kind == "bold":        wrap("**", "太字")
        elif kind == "italic":      wrap("*",  "斜体")
        elif kind == "strikethrough": wrap("~~", "テキスト")
        elif kind == "inlinecode":  wrap("`",  "code")
        elif kind == "ul":          prefix("- ")
        elif kind == "ol":          prefix("1. ")
        elif kind == "blockquote":  prefix("> ")
        elif kind == "hr":          c.insertText("\n---\n")
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
        elif kind == "plantuml":
            c.insertText("```plantuml\nA -> B : Hello\nB --> A : World\n```")
        elif kind == "table":
            c.insertText(
                "| 列1 | 列2 | 列3 |\n"
                "|-----|-----|-----|\n"
                "| セル | セル | セル |\n"
            )
        self.editor.setFocus()

    # ── table format

    def formatTable(self):
        """Align the Markdown table that contains the cursor."""
        doc = self.editor.document()
        cursor = self.editor.textCursor()

        # Walk backward to the first row of the table
        b = cursor.block()
        while b.isValid() and re.match(r'^\s*\|', b.text()):
            b = b.previous()
        start_block = b.next() if b.isValid() and not re.match(r'^\s*\|', b.text()) else b

        if not start_block.isValid() or not re.match(r'^\s*\|', start_block.text()):
            return  # cursor is not inside a table

        # Walk forward to the last row of the table
        b = start_block
        while b.isValid() and re.match(r'^\s*\|', b.text()):
            b = b.next()
        end_block = b.previous()

        if start_block.blockNumber() > end_block.blockNumber():
            return

        # Collect raw rows
        rows, b = [], start_block
        while b.isValid() and b.blockNumber() <= end_block.blockNumber():
            rows.append(b.text())
            b = b.next()

        def parse_row(line: str):
            line = line.strip()
            if line.startswith('|'):
                line = line[1:]
            if line.endswith('|'):
                line = line[:-1]
            return [cell.strip() for cell in line.split('|')]

        parsed = [parse_row(r) for r in rows]
        num_cols = max(len(r) for r in parsed)
        for r in parsed:
            while len(r) < num_cols:
                r.append('')

        # Detect separator row (index 1) and compute column widths
        def is_sep_cell(s: str) -> bool:
            return bool(re.match(r'^:?-+:?$', s)) or s == ''

        sep_idx = 1 if len(parsed) > 1 and all(is_sep_cell(c) for c in parsed[1]) else -1

        col_widths = [3] * num_cols  # minimum 3 chars
        for ri, r in enumerate(parsed):
            for ci, cell in enumerate(r):
                if ri == sep_idx:
                    continue
                col_widths[ci] = max(col_widths[ci], len(cell))

        # Rebuild rows with padding
        new_rows = []
        for ri, r in enumerate(parsed):
            cells = []
            for ci, cell in enumerate(r):
                w = col_widths[ci]
                if ri == sep_idx:
                    c_str = cell if cell else '-' * w
                    if c_str.startswith(':') and c_str.endswith(':'):
                        cells.append(':' + '-' * (w - 2) + ':')
                    elif c_str.startswith(':'):
                        cells.append(':' + '-' * (w - 1))
                    elif c_str.endswith(':'):
                        cells.append('-' * (w - 1) + ':')
                    else:
                        cells.append('-' * w)
                else:
                    cells.append(cell.ljust(w))
            new_rows.append('| ' + ' | '.join(cells) + ' |')

        # Replace the table text in the document
        tc = self.editor.textCursor()
        tc.setPosition(start_block.position())
        tc.setPosition(
            end_block.position() + end_block.length() - 1,
            QTextCursor.MoveMode.KeepAnchor,
        )
        tc.insertText('\n'.join(new_rows))
        self.editor.setTextCursor(tc)
        self.editor.setFocus()

    # ── search

    def showSearch(self):
        if self._search_dlg is None:
            self._search_dlg = SearchDialog(self.editor, self)
        self._search_dlg.popup()

    # ── permissions / downloads

    def _grantPermission(self, url, feature):
        self.preview.page().setFeaturePermission(
            url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
        )

    def _onDownloadRequested(self, download: QWebEngineDownloadRequest):
        suggested = download.suggestedFileName() or "diagram.svg"
        path, _ = QFileDialog.getSaveFileName(self.window(), "保存", suggested)
        if path:
            download.setDownloadDirectory(str(Path(path).parent))
            download.setDownloadFileName(Path(path).name)
            download.accept()
        else:
            download.cancel()

    # ── cleanup

    def cleanup(self):
        self._preview_timer.stop()
        if self._tmp_html and os.path.exists(self._tmp_html):
            os.unlink(self._tmp_html)
        self._tmp_html = None


# ── MarkdownEditor ────────────────────────────────────────────────────────────

class MarkdownEditor(QMainWindow):
    def __init__(self, initial_file=None):  # type: (str | None) -> None
        super().__init__()
        self._dark = False
        self._font_size = 14
        config_dir = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation))
        config_dir.mkdir(parents=True, exist_ok=True)
        self._settings = QSettings(
            str(config_dir / "settings.ini"), QSettings.Format.IniFormat)
        self._last_dir = self._settings.value("last_dir", str(Path.home()))
        self._recent_files: list[str] = json.loads(
            self._settings.value("recent_files", "[]")
        )

        self._outline_timer = QTimer(singleShot=True, interval=300)

        self._initUI()
        self._applyTheme()  # also calls reloadPreview on the first tab
        self.setAcceptDrops(True)

        if initial_file and Path(initial_file).exists():
            self._curTab().loadFile(initial_file)
        # else the first tab already has _DEFAULT_MD

    # ── Drag & Drop

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.isLocalFile() for u in urls):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                p = Path(path)
                if p.is_file():
                    self._setLastDir(str(p.parent))
                    self._openOrSwitchToFile(path)
        event.acceptProposedAction()

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

        # Outline dock (left side, hidden by default)
        self._outline = OutlinePanel()
        self._outline.jumpTo.connect(self._jumpToLine)
        self._outline_dock = QDockWidget(self)
        self._outline_dock.setObjectName("outline-dock")
        self._outline_dock.setTitleBarWidget(QWidget(self._outline_dock))  # hide title bar
        self._outline_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._outline_dock.setWidget(self._outline)
        self._outline_dock.setMinimumWidth(180)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._outline_dock)
        self._outline_dock.hide()
        self._outline_timer.timeout.connect(self._updateOutline)

        # File tree dock (left side, hidden by default)
        self._file_tree = FileTreePanel()
        self._file_tree.openFile.connect(self._openOrSwitchToFile)
        self._file_tree_dock = QDockWidget(self)
        self._file_tree_dock.setObjectName("filetree-dock")
        self._file_tree_dock.setTitleBarWidget(QWidget(self._file_tree_dock))
        self._file_tree_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._file_tree_dock.setWidget(self._file_tree)
        self._file_tree_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._file_tree_dock)
        self._file_tree_dock.hide()

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setObjectName("editor-tabs")
        self.tabs.tabCloseRequested.connect(self._closeTab)
        self.tabs.currentChanged.connect(self._onTabChanged)

        # "+" new-tab button at the right corner of the tab bar
        new_tab_btn = QToolButton()
        new_tab_btn.setText("+")
        new_tab_btn.setToolTip("新しいタブ (Ctrl+T)")
        new_tab_btn.clicked.connect(self._newTab)
        new_tab_btn.setObjectName("new-tab-btn")
        self.tabs.setCornerWidget(new_tab_btn, Qt.Corner.TopRightCorner)

        vbox.addWidget(self.tabs)
        self._buildStatusBar()

        # Add the first tab (with welcome text)
        self._addTab(initial_content=_DEFAULT_MD)

    def _buildToolbar(self):
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

        # File menu
        file_menu = QMenu(self)
        file_menu.addAction("📄  New Tab",   self._newTab).setShortcut(QKeySequence("Ctrl+T"))
        file_menu.addAction("📂  Open",      self._openFile).setShortcut(QKeySequence("Ctrl+O"))
        # Recent files submenu — populated dynamically when the menu opens
        self._recent_menu = QMenu("🕐  最近使ったファイル", file_menu)
        file_menu.addMenu(self._recent_menu)
        self._recent_menu.aboutToShow.connect(self._buildRecentMenu)
        file_menu.addSeparator()
        file_menu.addAction("💾  Save",      self._saveFile).setShortcut(QKeySequence("Ctrl+S"))
        file_menu.addAction("💾  Save As…",  self._saveFileAs)
        file_menu.addSeparator()
        file_menu.addAction("📑  Export PDF…", self._exportPdf).setShortcut(QKeySequence("Ctrl+Shift+E"))
        file_menu.addAction("🖨  Print…",      self._printDoc).setShortcut(QKeySequence("Ctrl+P"))
        file_menu.addSeparator()
        file_menu.addAction("✖  Close Tab",  self._closeCurrentTab).setShortcut(QKeySequence("Ctrl+W"))

        self._file_btn = QToolButton()
        self._file_btn.setText("File ▾")
        self._file_btn.setObjectName("file-btn")
        self._file_btn.setMenu(file_menu)
        self._file_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        tb1.addWidget(self._file_btn)

        tb1.addSeparator()
        self._themeAct = act(tb1, "☀", "テーマ切り替え", self._toggleTheme)
        act(tb1, "🔍", "検索・置換 (Ctrl+F)", self._showSearch, "Ctrl+F")
        self._outlineAct = act(tb1, "≡", "アウトライン (Ctrl+Shift+O)", self._toggleOutline, "Ctrl+Shift+O")
        self._filetreeAct = act(tb1, "📁", "ファイルツリー (Ctrl+Shift+F)", self._toggleFileTree, "Ctrl+Shift+F")

        tb1.addSeparator()
        act(tb1, "A−", "文字を小さく", self._fontSizeDown)
        self._fontSizeLabel = QLabel(f"{self._font_size}px")
        self._fontSizeLabel.setObjectName("font-size-label")
        self._fontSizeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fontSizeLabel.setFixedWidth(36)
        tb1.addWidget(self._fontSizeLabel)
        act(tb1, "A+", "文字を大きく", self._fontSizeUp)

        # ── 2nd row: edit actions
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        tb2 = QToolBar("編集ツールバー")
        tb2.setMovable(False)
        tb2.setObjectName("edit-tb")
        self.addToolBar(tb2)

        act(tb2, "H1", "見出し 1",              lambda: self._insert("heading1"))
        act(tb2, "H2", "見出し 2",              lambda: self._insert("heading2"))
        act(tb2, "H3", "見出し 3",              lambda: self._insert("heading3"))
        tb2.addSeparator()
        act(tb2, "B",        "太字 (Ctrl+B)",   lambda: self._insert("bold"),      "Ctrl+B")
        act(tb2, "I",        "斜体 (Ctrl+I)",   lambda: self._insert("italic"),    "Ctrl+I")
        act(tb2, "~~",       "打ち消し線",       lambda: self._insert("strikethrough"))
        act(tb2, "`",        "インラインコード", lambda: self._insert("inlinecode"))
        tb2.addSeparator()
        act(tb2, "• List",   "箇条書き",         lambda: self._insert("ul"))
        act(tb2, "1. List",  "番号付きリスト",   lambda: self._insert("ol"))
        act(tb2, "> Quote",  "引用",             lambda: self._insert("blockquote"))
        act(tb2, "``` Code", "コードブロック",   lambda: self._insert("codeblock"))
        act(tb2, "Mermaid",  "Mermaid ダイアグラム",  lambda: self._insert("mermaid"))
        act(tb2, "PlantUML", "PlantUML ダイアグラム", lambda: self._insert("plantuml"))
        act(tb2, "Table",    "テーブル",                    lambda: self._insert("table"))
        act(tb2, "≡T",      "テーブル整形 (Ctrl+Shift+T)", self._formatTable, "Ctrl+Shift+T")
        act(tb2, "Link",     "リンク (Ctrl+K)",             lambda: self._insert("link"), "Ctrl+K")
        act(tb2, "---",      "水平線",                      lambda: self._insert("hr"))

    def _buildStatusBar(self):
        sb = self.statusBar()
        sb.setObjectName("statusbar")
        self._lnColLbl = QLabel("Ln 1, Col 1")
        self._wordsLbl = QLabel("0 words")
        self._charsLbl = QLabel("0 chars")
        versions = _load_versions()
        mermaid_ver = versions.get("mermaid", "?")
        plantuml_ver = versions.get("plantuml", "?")
        import PySide6
        py_ver = ".".join(str(v) for v in sys.version_info[:3])
        ps6_ver = PySide6.__version__
        badge = QLabel(f"mermaid v{mermaid_ver}  |  plantuml v{plantuml_ver}")
        badge.setObjectName("badge")
        badge.setToolTip(
            f"Python {py_ver}  |  PySide6 {ps6_ver}\n"
            f"mermaid {mermaid_ver}  |  plantuml {plantuml_ver}"
        )
        sb.addWidget(self._lnColLbl)
        sb.addWidget(QLabel("|"))
        sb.addWidget(self._wordsLbl)
        sb.addWidget(QLabel("|"))
        sb.addWidget(self._charsLbl)
        sb.addPermanentWidget(badge)

    # ── Tab management

    def _curTab(self):
        return self.tabs.currentWidget()  # type: EditorTab

    def _addTab(self, file_path=None, initial_content=None):
        """Create a new EditorTab, add it to the tab widget, and return it."""
        tab = EditorTab(dark=self._dark, font_size=self._font_size)
        tab.titleChanged.connect(lambda title, t=tab: self._onTabTitleChanged(t, title))
        tab.editor.cursorPositionChanged.connect(self._updateStatus)
        tab.editor.textChanged.connect(self._updateStatus)
        tab.editor.textChanged.connect(lambda t=tab: self._onTabTextChanged(t))

        if file_path:
            idx = self.tabs.addTab(tab, Path(file_path).name)
            self.tabs.setCurrentIndex(idx)
            tab.applyTheme(self._dark)
            tab.loadFile(file_path)
        else:
            idx = self.tabs.addTab(tab, "untitled.md")
            self.tabs.setCurrentIndex(idx)
            tab.applyTheme(self._dark)
            if initial_content:
                tab.editor.setPlainText(initial_content)
                tab._modified = False

        return tab

    def _onTabTitleChanged(self, tab, title):
        idx = self.tabs.indexOf(tab)
        if idx >= 0:
            self.tabs.setTabText(idx, title)
        if tab is self._curTab():
            self.setWindowTitle(f"Markdown Editor — {title}")

    def _onTabChanged(self, idx):
        tab = self.tabs.widget(idx)
        if tab:
            self.setWindowTitle(f"Markdown Editor — {tab.tabTitle()}")
            self._updateStatus()
            self._updateOutline()
            self._updateFileTreeRoot()

    def _newTab(self):
        self._addTab()

    def _closeTab(self, idx):
        tab = self.tabs.widget(idx)
        if not self._confirmDiscard(tab):
            return
        tab.cleanup()
        self.tabs.removeTab(idx)
        if self.tabs.count() == 0:
            self._addTab()  # always keep at least one tab

    def _closeCurrentTab(self):
        self._closeTab(self.tabs.currentIndex())

    # ── File operations

    def _openOrSwitchToFile(self, path: str):
        """Open *path* in the editor, reusing an existing tab if already open."""
        abs_path = str(Path(path).resolve())
        # Check if any tab already has this file open
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and tab._file and str(Path(tab._file).resolve()) == abs_path:
                self.tabs.setCurrentIndex(i)
                self._addRecentFile(abs_path)
                return
        # Reuse current tab if empty and unmodified
        cur = self._curTab()
        if cur and cur._file is None and not cur._modified \
                and not cur.editor.toPlainText().strip():
            cur.loadFile(abs_path)
            cur.applyTheme(self._dark)
        else:
            self._addTab(file_path=abs_path)
        self._addRecentFile(abs_path)

    def _setLastDir(self, path: str):
        self._last_dir = path
        self._settings.setValue("last_dir", path)

    def _openFile(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "ファイルを開く", self._last_dir,
            "Markdown Files (*.md *.markdown);;Text Files (*.txt);;All Files (*)",
        )
        for path in paths:
            self._setLastDir(str(Path(path).parent))
            self._addRecentFile(path)
            # Reuse current tab if it is empty and unmodified
            tab = self._curTab()
            if tab and tab._file is None and not tab._modified \
                    and not tab.editor.toPlainText().strip():
                tab.loadFile(path)
                tab.applyTheme(self._dark)
            else:
                self._addTab(file_path=path)

    def _saveFile(self):
        tab = self._curTab()
        if not tab:
            return
        if not tab._file:
            self._saveFileAs()
            return
        tab.saveFile()
        self.setWindowTitle(f"Markdown Editor — {tab.tabTitle()}")

    def _saveFileAs(self):
        tab = self._curTab()
        if not tab:
            return
        default = tab._file or str(Path(self._last_dir) / "untitled.md")
        path, _ = QFileDialog.getSaveFileName(
            self, "名前を付けて保存", default,
            "Markdown Files (*.md *.markdown);;Text Files (*.txt);;All Files (*)",
        )
        if path:
            self._setLastDir(str(Path(path).parent))
            self._addRecentFile(path)
            tab._file = path
            tab.saveFile()
            self.setWindowTitle(f"Markdown Editor — {tab.tabTitle()}")

    def _exportPdf(self):
        tab = self._curTab()
        if not tab:
            return
        stem = Path(tab._file).stem if tab._file else "document"
        default = str(Path(self._last_dir) / f"{stem}.pdf")
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF として保存", default, "PDF Files (*.pdf)"
        )
        if not path:
            return
        self._setLastDir(str(Path(path).parent))
        layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(15, 15, 15, 15),
        )

        # JS: scaleSvg() が SVG 要素に付けた width/height 属性を一時的に除去。
        # @media print の max-width: 100% が確実に効くようにする。
        _JS_STRIP = (
            "document.querySelectorAll('.mermaid svg, .plantuml svg').forEach(svg => {"
            "  svg.dataset.pw = svg.getAttribute('width') || '';"
            "  svg.dataset.ph = svg.getAttribute('height') || '';"
            "  svg.removeAttribute('width');"
            "  svg.removeAttribute('height');"
            "});"
        )
        _JS_RESTORE = (
            "document.querySelectorAll('.mermaid svg, .plantuml svg').forEach(svg => {"
            "  if (svg.dataset.pw) svg.setAttribute('width',  svg.dataset.pw);"
            "  if (svg.dataset.ph) svg.setAttribute('height', svg.dataset.ph);"
            "});"
        )

        page = tab.preview.page()

        def _do_print(_=None):
            def _on_pdf(data: bytes):
                with open(path, "wb") as f:
                    f.write(data)
                page.runJavaScript(_JS_RESTORE)
            page.printToPdf(_on_pdf, layout)

        page.runJavaScript(_JS_STRIP, _do_print)

    def _printDoc(self):
        tab = self._curTab()
        if not tab:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        _JS_STRIP = (
            "document.querySelectorAll('.mermaid svg, .plantuml svg').forEach(svg => {"
            "  svg.dataset.pw = svg.getAttribute('width') || '';"
            "  svg.dataset.ph = svg.getAttribute('height') || '';"
            "  svg.removeAttribute('width');"
            "  svg.removeAttribute('height');"
            "});"
        )
        _JS_RESTORE = (
            "document.querySelectorAll('.mermaid svg, .plantuml svg').forEach(svg => {"
            "  if (svg.dataset.pw) svg.setAttribute('width',  svg.dataset.pw);"
            "  if (svg.dataset.ph) svg.setAttribute('height', svg.dataset.ph);"
            "});"
        )

        page = tab.preview.page()

        def _do_print(_=None):
            def _on_done(success: bool):
                page.runJavaScript(_JS_RESTORE)
                if not success:
                    QMessageBox.warning(self, "印刷エラー", "印刷中にエラーが発生しました。")
            page.print(printer, _on_done)

        page.runJavaScript(_JS_STRIP, _do_print)

    def _confirmDiscard(self, tab) -> bool:
        if not tab._modified:
            return True
        name = Path(tab._file).name if tab._file else "untitled.md"
        r = QMessageBox.question(
            self, "確認", f"「{name}」の変更を保存しますか？",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
        )
        if r == QMessageBox.StandardButton.Save:
            if tab._file:
                tab.saveFile()
            else:
                path, _ = QFileDialog.getSaveFileName(
                    self, "名前を付けて保存", "untitled.md",
                    "Markdown Files (*.md *.markdown);;All Files (*)",
                )
                if path:
                    tab._file = path
                    tab.saveFile()
            return True
        return r == QMessageBox.StandardButton.Discard

    # ── Status bar

    def _updateStatus(self):
        tab = self._curTab()
        if not tab:
            return
        cursor = tab.editor.textCursor()
        ln  = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        text = tab.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        self._lnColLbl.setText(f"Ln {ln}, Col {col}")
        self._wordsLbl.setText(f"{words} words")
        self._charsLbl.setText(f"{len(text)} chars")

    # ── Outline

    def _toggleOutline(self):
        if self._outline_dock.isVisible():
            self._outline_dock.hide()
        else:
            self._outline_dock.show()
            self._updateOutline()

    def _updateOutline(self):
        if not self._outline_dock.isVisible():
            return
        tab = self._curTab()
        if tab:
            self._outline.refresh(tab.editor.toPlainText())

    def _onTabTextChanged(self, tab):
        if tab is self._curTab() and self._outline_dock.isVisible():
            self._outline_timer.start()

    def _jumpToLine(self, lineno: int):
        tab = self._curTab()
        if not tab:
            return
        block = tab.editor.document().findBlockByLineNumber(lineno)
        cursor = tab.editor.textCursor()
        cursor.setPosition(block.position())
        tab.editor.setTextCursor(cursor)
        tab.editor.setFocus()

    # ── Insert / search

    def _insert(self, kind: str):
        tab = self._curTab()
        if tab:
            tab.insert(kind)

    def _showSearch(self):
        tab = self._curTab()
        if tab:
            tab.showSearch()

    def _formatTable(self):
        tab = self._curTab()
        if tab:
            tab.formatTable()

    # ── Recent files

    def _addRecentFile(self, path: str):
        path = str(Path(path).resolve())
        if path in self._recent_files:
            self._recent_files.remove(path)
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:_RECENT_MAX]
        self._settings.setValue("recent_files", json.dumps(self._recent_files))

    def _clearRecentFiles(self):
        self._recent_files.clear()
        self._settings.setValue("recent_files", "[]")

    def _buildRecentMenu(self):
        self._recent_menu.clear()
        valid = [p for p in self._recent_files if Path(p).exists()]
        if not valid:
            a = self._recent_menu.addAction("(なし)")
            a.setEnabled(False)
            return
        for path in valid:
            name = Path(path).name
            a = self._recent_menu.addAction(name)
            a.setToolTip(path)
            a.triggered.connect(lambda checked, p=path: self._openOrSwitchToFile(p))
        self._recent_menu.addSeparator()
        self._recent_menu.addAction("履歴をクリア", self._clearRecentFiles)

    # ── File tree

    def _toggleFileTree(self):
        if self._file_tree_dock.isVisible():
            self._file_tree_dock.hide()
        else:
            self._file_tree_dock.show()
            self._updateFileTreeRoot()

    def _updateFileTreeRoot(self):
        if not self._file_tree_dock.isVisible():
            return
        tab = self._curTab()
        if tab and tab._file:
            self._file_tree.setRootPath(str(Path(tab._file).parent))

    # ── Theme / font size

    def _toggleTheme(self):
        self._dark = not self._dark
        self._applyTheme()

    def _applyTheme(self):
        t = DARK if self._dark else LIGHT
        self._themeAct.setText("🌙" if self._dark else "☀")

        # Apply to all tabs
        for i in range(self.tabs.count()):
            self.tabs.widget(i).applyTheme(self._dark)

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
            QToolBar#main-tb QToolButton#file-btn:pressed {{
                background: #2a72c0; color: #ffffff; border-color: #2a72c0;
            }}
            QMenu {{
                background: {t["surface"]}; color: {t["text"]};
                border: 1px solid {t["border"]}; border-radius: 4px; padding: 4px 0;
            }}
            QMenu::item {{ padding: 6px 24px 6px 12px; font-size: 12px; }}
            QMenu::item:selected {{ background: #2a72c0; color: #fff; border-radius: 3px; }}
            QMenu::separator {{ height: 1px; background: {t["border"]}; margin: 3px 8px; }}
            QTabWidget#editor-tabs::pane {{ border: none; }}
            QTabWidget#editor-tabs > QTabBar {{
                background: {t["surface2"]};
                border-bottom: 1px solid {t["border"]};
            }}
            QTabWidget#editor-tabs > QTabBar::tab {{
                background: {t["surface2"]}; color: {t["text2"]};
                border: 1px solid {t["border"]}; border-bottom: none;
                padding: 5px 14px; margin-right: 1px;
                font-family: 'JetBrains Mono', monospace; font-size: 11px;
            }}
            QTabWidget#editor-tabs > QTabBar::tab:selected {{
                background: {t["surface"]}; color: {t["text"]};
                border-bottom: 1px solid {t["surface"]};
            }}
            QTabWidget#editor-tabs > QTabBar::tab:hover:!selected {{
                color: {t["accent"]};
            }}
            QToolButton#new-tab-btn {{
                background: transparent; color: {t["text2"]};
                border: none; padding: 4px 8px; font-size: 14px;
            }}
            QToolButton#new-tab-btn:hover {{ color: {t["accent"]}; }}
            QLabel#pane-label {{
                font-size: 10px; font-weight: 600; letter-spacing: 0.08em;
                text-transform: uppercase;
                color: {t["text2"]}; background: {t["surface2"]};
                border-bottom: 1px solid {t["border"]}; padding: 1px 14px;
                max-height: 18px;
            }}
            QLabel#font-size-label {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px; color: {t["text2"]};
            }}
            QStatusBar#statusbar QLabel#badge {{
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
            QDockWidget#outline-dock, QDockWidget#filetree-dock {{ border: none; }}
            QTreeView#file-tree {{
                background: {t["surface"]}; color: {t["text"]};
                border: none; outline: none;
                font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace;
                font-size: 11px;
            }}
            QTreeView#file-tree::item {{
                padding: 2px 4px; border-radius: 3px;
            }}
            QTreeView#file-tree::item:selected {{
                background: {t["accent"]}; color: #fff;
            }}
            QTreeView#file-tree::item:hover:!selected {{
                background: {t["surface2"]}; color: {t["accent"]};
            }}
            QListWidget#outline-list {{
                background: {t["surface"]}; color: {t["text"]};
                border: none; outline: none;
                font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace;
                font-size: 11px;
            }}
            QListWidget#outline-list::item {{
                padding: 3px 10px; border-radius: 3px;
            }}
            QListWidget#outline-list::item:selected {{
                background: {t["accent"]}; color: #fff;
            }}
            QListWidget#outline-list::item:hover:!selected {{
                background: {t["surface2"]}; color: {t["accent"]};
            }}
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
        for i in range(self.tabs.count()):
            self.tabs.widget(i).applyFontSize(self._font_size)

    # ── Window close

    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            if not self._confirmDiscard(self.tabs.widget(i)):
                event.ignore()
                return
        for i in range(self.tabs.count()):
            self.tabs.widget(i).cleanup()
        event.accept()
