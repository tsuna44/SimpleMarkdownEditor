# SimpleMarkdownEditor — 配布ガイド (PyInstaller --onedir)

## なぜ `--onedir` か

PySide6 は **LGPL v3** でライセンスされています。LGPL が配布バイナリに課す主な義務は次の 2 つです。

| 義務 | 内容 |
|---|---|
| ライブラリのソース開示 | PySide6 / Qt のソースコードへのアクセス手段を提供する |
| **ユーザーによるリンク先変更の保証** | エンドユーザーが PySide6 / Qt ライブラリを自分でビルドしたものに差し替えられる構造にする |

`--onefile` は全ファイルを 1 つの圧縮バイナリに埋め込むため、ユーザーが Qt ライブラリを差し替えることができません。これは「リンク先変更の保証」に違反する可能性があります。

`--onedir` はディレクトリ内に `.so` / `.dylib` / `.dll` を個別ファイルとして展開するため、ユーザーがライブラリを差し替え可能な構造になります。

> **結論:** PySide6 を含む GUI アプリを LGPL 準拠で配布するには `--onedir` を使用してください。

---

## ビルド手順

### 前提条件

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### macOS / Linux

```bash
cd Python/
bash build.sh          # --onedir ビルド（デフォルト）
```

出力: `dist/SimpleMarkdownEditor.app` (macOS) または `dist/SimpleMarkdownEditor/` (Linux)

### Windows

```bat
cd Python\
build_windows.bat
```

出力: `dist\SimpleMarkdownEditor\`

### 直接 PyInstaller を実行する場合

```bash
cd Python/
python -m PyInstaller \
  --name SimpleMarkdownEditor \
  --noconfirm \
  --windowed \
  --onedir \
  --collect-all markdown \
  --collect-all pygments \
  --hidden-import PySide6.QtWebEngineWidgets \
  --hidden-import PySide6.QtWebEngineCore \
  --hidden-import PySide6.QtWebEngineQuick \
  markdown_editor.py
```

> `--onefile` は使用しないでください（LGPL 違反リスクあり）。

---

## 配布物の構成

```
dist/SimpleMarkdownEditor/          ← このフォルダごとzip等で配布
├── SimpleMarkdownEditor            ← 実行ファイル (macOS/Linux)
│                                   ← SimpleMarkdownEditor.exe (Windows)
├── PySide6/
│   ├── Qt/lib/                     ← Qt フレームワーク (.dylib / .so / .dll)
│   │   ├── QtCore.framework/       ← ← ユーザーが差し替え可能なファイル群
│   │   ├── QtGui.framework/
│   │   └── ...
│   └── plugins/
├── markdown/
├── pygments/
└── _internal/                      ← PyInstaller ランタイム
```

Qt / PySide6 のライブラリが個別ファイルとして存在するため、エンドユーザーは互換バージョンのライブラリを差し替えることができます。

---

## 配布時に必要なライセンス表記

配布パッケージに以下を同梱してください。

### 1. LGPL 通知 (`NOTICE.txt` を作成して同梱)

```
This application uses PySide6 (Qt for Python), which is licensed under
the GNU Lesser General Public License version 3 (LGPLv3).

Source code for PySide6 and Qt is available at:
  https://www.qt.io/download-open-source
  https://code.qt.io/cgit/pyside/pyside-setup.git/

Under the terms of the LGPLv3, you may replace the PySide6/Qt libraries
in this distribution with your own compatible build.
The shared library files are located in the PySide6/ directory.
```

### 2. ライセンスファイルの同梱

以下を `dist/SimpleMarkdownEditor/licenses/` ディレクトリに配置することを推奨します。

| ファイル | 取得元 |
|---|---|
| `LGPLv3.txt` | https://www.gnu.org/licenses/lgpl-3.0.txt |
| `pyside6-license.txt` | `pip show PySide6` で表示される Location のライセンスファイル |

---

## ライセンス早見表

| コンポーネント | ライセンス | 配布時の主な義務 |
|---|---|---|
| アプリ本体 | MIT | — |
| PySide6 / Qt | LGPL v3 | ソース開示・差し替え可能な配布構造 |
| markdown | BSD | 著作権表示の同梱 |
| pygments | BSD | 著作権表示の同梱 |
| PyInstaller (ビルドツール) | GPL v2 + Bootloader Exception | 配布物には含まれない（ビルド時のみ使用）|

> **PyInstaller Bootloader Exception について**
> PyInstaller のブートローダーは GPL ですが、公式の "Bootloader Exception" により、
> ブートローダーを使ってパッケージングされたアプリはそのライセンスに感染しません。
> ただし、ブートローダー自体を改変した場合は GPL が適用されます。

---

## よくある質問

**Q. `--onefile` を使ってはいけないのか？**

A. LGPL の「ユーザーによるリンク先変更の保証」を満たせない可能性があります。
法的リスクを避けるため `--onedir` を推奨します。どうしても単一ファイル配布が必要な場合は、
Qt をスタティックリンクして商用ライセンスを取得するか、法律の専門家に相談してください。

**Q. macOS の `.app` バンドルは `--onedir` か？**

A. はい。`build.sh` が生成する `SimpleMarkdownEditor.app` は内部にすべての `.dylib` を
個別ファイルとして持つ `--onedir` 相当の構造です。

**Q. ソースコードはどこで公開すればよいか？**

A. PySide6 / Qt 自体のソースは Qt Project が公開しています。
アプリ側で改変していない限り、改変版ソースの公開義務はありません。
Qt のソースへのリンクを `NOTICE.txt` に記載するだけで十分です。
