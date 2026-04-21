# SimpleMarkdownEditor

Python/PySide6 製のMarkdownエディタ。Mermaid・PlantUMLのインラインレンダリングに対応。

## 機能

- **リアルタイムプレビュー** — 編集と同時にHTML変換・表示
- **Mermaid ダイアグラム** — コードブロック ` ```mermaid ` をSVGレンダリング（elkjsレイアウトエンジン対応）
- **PlantUML ダイアグラム** — コードブロック ` ```plantuml ` をSVGレンダリング（ローカルJava/jarで実行）
- **構文ハイライト** — Pygmentsによるコードブロックのハイライト
- **アンカーリンク** — 見出しへのTOCリンクに対応
- **同時スクロール** — エディタとプレビューのスクロール位置を連動
- **ライト / ダークテーマ** — ワンクリックで切り替え
- **多タブ編集** — 複数ファイルをタブで管理（Ctrl+T / Ctrl+W）
- **アウトラインパネル** — H1〜H3の見出しリスト表示・クリックでジャンプ（Ctrl+Shift+O）
- **ファイルツリーパネル** — 現在ファイルのディレクトリを .md/.markdown/.txt でフィルタ表示（Ctrl+Shift+F）
- **検索・置換** — 大文字小文字区別・正規表現対応（Ctrl+F）
- **テーブル整形** — カーソル位置のMarkdownテーブルを自動整列（Ctrl+Shift+T）
- **挿入ツールバー** — 見出し・太字・斜体・リスト・コードブロック・Mermaid・PlantUML・テーブル・リンク・水平線を1クリックで挿入
- **PDF エクスポート** — プレビューをA4 PDFで保存（Ctrl+Shift+E）
- **印刷** — システムプリンタへ直接印刷（Ctrl+P）
- **Drag & Drop** — ファイルをウィンドウにドロップして開く
- **最近使ったファイル** — 最大10件を記録、File メニューから再オープン
- **外部ファイル変更の自動リロード** — 他のエディタで保存されたときにコンテンツを自動更新
- **行番号ガター** — エディタ左端に行番号を表示
- **フォントサイズ変更** — ツールバーのA−/A+ボタンでリアルタイム調整

## 必要環境

| 依存ライブラリ | バージョン |
|---|---|
| Python | 3.10 以上 |
| PySide6 | 6.10 以上 6.12 未満 |
| markdown | 3.5 以上 |
| pygments | 2.17 以上 |

PlantUMLを使う場合は別途 Java と PlantUML が必要です。

```bash
brew install plantuml   # macOS
sudo apt install plantuml  # Ubuntu
```

## インストールと起動

```bash
cd Python
pip install -r requirements.txt
python markdown_editor.py [file.md]
```

## キーボードショートカット

| 操作 | ショートカット |
|---|---|
| 新規タブ | Ctrl+T |
| ファイルを開く | Ctrl+O |
| 保存 | Ctrl+S |
| PDF エクスポート | Ctrl+Shift+E |
| 印刷 | Ctrl+P |
| タブを閉じる | Ctrl+W |
| 検索・置換 | Ctrl+F |
| アウトライン表示切り替え | Ctrl+Shift+O |
| ファイルツリー表示切り替え | Ctrl+Shift+F |
| テーブル整形 | Ctrl+Shift+T |
| 太字 | Ctrl+B |
| 斜体 | Ctrl+I |
| リンク挿入 | Ctrl+K |

## ディレクトリ構成

```
Python/
  markdown_editor.py   # エントリポイント・Qt plugin パス修正
  main_window.py       # MarkdownEditor (QMainWindow) / EditorTab
  editor_widget.py     # CodeEditor（行番号ガター付き QPlainTextEdit）
  search_dialog.py     # 検索・置換ダイアログ
  themes.py            # ライト/ダークテーマの色定義
  preview_html.py      # プレビュー用シェルHTML生成
  requirements.txt
vendor/
  mermaid.min.js       # Mermaid ライブラリ
  elkjs/               # elkjs レイアウトエンジン
  plantuml.jar         # PlantUML JAR（バンドル版）
  VERSIONS.json        # バンドルライブラリのバージョン情報
```
