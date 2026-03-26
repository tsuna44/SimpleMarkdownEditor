# Simple Markdown Editor — Python 版 仕様書

## 概要

Python と PySide6 (Qt6) で実装されたデスクトップ向け Markdown エディタ。
左ペインでテキスト編集、右ペインでリアルタイムプレビューを表示する分割レイアウト。

---

## 動作環境

| 項目 | 要件 |
|---|---|
| Python | 3.10 以上 |
| 主要依存ライブラリ | PySide6 >= 6.6、markdown >= 3.5、pygments >= 2.17 |
| ライセンス | MIT（依存ライブラリは LGPL/BSD） |

インストール:

```bash
pip install PySide6 markdown pygments
```

起動:

```bash
python markdown_editor.py [file.md]
```

---

## 画面構成

```
┌─────────────────────────────────────────────┐
│  [File ▾]  ☀  🔍  A−  14px  A+     file.md │  ← ツールバー 1段目
├─────────────────────────────────────────────┤
│ H1 H2 H3 | B I ~~ ` | • 1. > ``` Mermaid … │  ← ツールバー 2段目
├──────────────────┬──────────────────────────┤
│  EDITOR          │  PREVIEW                 │
│                  │                          │
│  (テキスト編集)   │  (HTML レンダリング)      │
│                  │                          │
├──────────────────┴──────────────────────────┤
│ Ln 1, Col 1 | 0 words | 0 chars  Python/PySide6 │  ← ステータスバー
└─────────────────────────────────────────────┘
```

---

## 機能仕様

### 1. エディタ

#### 1-1. テキスト入力

- プレーンテキスト編集（`QPlainTextEdit` ベース）
- 等幅フォント優先使用: JetBrains Mono → Consolas → Menlo → Courier New
- 折り返しなし（水平スクロール対応）
- タブ幅: スペース 2 文字分

#### 1-2. 行番号ガター

- エディタ左端に行番号を常時表示
- スクロールに追従してリアルタイム更新
- テーマに応じた配色（`surface2` / `gutter` カラー）

#### 1-3. カーソル位置表示

- ステータスバーに `Ln {行}, Col {列}` をリアルタイム表示

---

### 2. Markdown レンダリング

#### 2-1. リアルタイムプレビュー

- テキスト変更から 300 ms のデバウンス後に自動更新
- Python 側の `markdown` ライブラリで HTML 変換し、WebEngine に注入

#### 2-2. サポートする Markdown 構文

| 構文 | 詳細 |
|---|---|
| 見出し | `#` `##` `###` (h1〜h6) |
| 太字 | `**text**` |
| 斜体 | `*text*` |
| 取り消し線 | `~~text~~`（Python 側で前処理して `<del>` 変換） |
| インラインコード | `` `code` `` |
| コードブロック | ```` ```lang ``` ```` (フェンス形式) |
| テーブル | GFM 形式 |
| 引用 | `> text` |
| 箇条書き / 番号付きリスト | `- item` / `1. item` |
| 水平線 | `---` |
| リンク | `[text](url)` |
| 画像 | `![alt](url)` |
| 脚注 | `[^1]` 形式（markdown.extensions.extra） |

#### 2-3. シンタックスハイライト

- Pygments によるコードブロックのハイライト
- ライトテーマ: `github` スタイル
- ダークテーマ: `github-dark` スタイル
- CSS クラス: `.codehilite`

#### 2-4. Mermaid ダイアグラム

- ```` ```mermaid ```` ブロックを検出し `<div class="mermaid">` に変換
- CDN 経由で mermaid.js v10 を読み込みレンダリング（`https://cdn.jsdelivr.net/npm/mermaid@10/`）
- ライト / ダークテーマに対応（`default` / `dark`）
- フォントサイズ変更時に SVG を viewBox ベースでスケール再計算

**ダイアグラムアクションボタン**（ホバーで表示）:

| ボタン | 動作 |
|---|---|
| 📋 Copy PNG | SVG を 2× 解像度（Retina 対応）の PNG に変換しクリップボードにコピー |
| ⬇ SVG | SVG ファイルとしてダウンロード（保存ダイアログ表示） |

---

### 3. ファイル操作

| 操作 | ショートカット | 詳細 |
|---|---|---|
| 新規 | Ctrl+N | 未保存確認ダイアログあり |
| 開く | Ctrl+O | フィルタ: `.md` `.markdown` `.txt` |
| 上書き保存 | Ctrl+S | 未保存時は「名前を付けて保存」にフォールバック |
| 名前を付けて保存 | — | フィルタ: `.md` `.markdown` `.txt` |
| PDF エクスポート | Ctrl+Shift+E | A4 / 縦向き / 余白 15mm、WebEngine の印刷機能を使用 |

**未保存確認ダイアログ**:
新規作成・ファイルを開く・ウィンドウを閉じる際に、未保存の変更がある場合は「保存 / 破棄 / キャンセル」を提示。

**ウィンドウタイトル**:
`Markdown Editor — {ファイル名}` / 未保存変更がある場合は末尾に ` ●` を付加。

---

### 4. テーマ

#### 4-1. ライトテーマ / ダークテーマ

ツールバーの ☀ / 🌙 ボタンで切り替え（再起動不要）。

| 要素 | ライト | ダーク |
|---|---|---|
| 背景 | `#f5f4f0` | `#161512` |
| テキスト | `#1a1814` | `#e8e4df` |
| アクセント | `#c0603a` | `#e07a52` |
| サーフェス | `#ffffff` | `#1e1c1a` |

テーマ切り替え時の更新対象:
- エディタの配色（`QPalette` 経由）
- ツールバー・ステータスバー・ダイアログ（QSS 一括適用）
- プレビュー HTML（テーマ別シェル HTML を再生成してリロード）
- Pygments CSS（ダークは `github-dark`、ライトは `github`）

---

### 5. フォントサイズ変更

ツールバーの `A−` / `A+` で変更（範囲: 8〜32 px）。

| 対象 | 動作 |
|---|---|
| エディタ | `QFont.setPointSize()` で即時反映 |
| プレビュー本文 | `document.body.style.fontSize` を JavaScript で設定 |
| Mermaid SVG | `scaleSvg()` で viewBox × スケール係数を再計算してリサイズ |

現在のサイズはツールバー中央に `{n}px` として表示。

---

### 6. 検索・置換ダイアログ

ショートカット: `Ctrl+F`（モードレスダイアログ）

| 機能 | 詳細 |
|---|---|
| テキスト検索 | 入力と同時にリアルタイム検索・ハイライト |
| 前へ / 次へ | `↑` / `↓` ボタン、件数表示 `{n}/{total}` |
| 大文字小文字区別 | `Aa` チェックボックス |
| 正規表現 | `.*` チェックボックス（`QRegularExpression` 使用） |
| 1件置換 | 現在選択中の一致を置換 |
| 全件置換 | すべての一致を一括置換、完了後に件数表示 |

---

### 7. 編集ツールバー（クイック挿入）

| ボタン | 挿入内容 | ショートカット |
|---|---|---|
| H1 / H2 / H3 | `# ` / `## ` / `### ` を行頭に挿入 | — |
| B | `**選択テキスト**` | Ctrl+B |
| I | `*選択テキスト*` | Ctrl+I |
| ~~ | `~~選択テキスト~~` | — |
| ` | `` `選択テキスト` `` | — |
| • List | `- ` を行頭に挿入 | — |
| 1. List | `1. ` を行頭に挿入 | — |
| > Quote | `> ` を行頭に挿入 | — |
| ``` Code | ```` ```\ncode\n``` ```` | — |
| Mermaid | Mermaid サンプルブロック挿入 | — |
| Table | 3列テーブルのテンプレート挿入 | — |
| Link | `[テキスト](url)` | Ctrl+K |
| --- | `\n---\n` | — |

テキスト選択中は選択範囲をラップ、未選択時はプレースホルダーを挿入してカーソルをプレースホルダー上に配置。

---

### 8. ステータスバー

| 表示項目 | 内容 |
|---|---|
| `Ln {n}, Col {n}` | 現在のカーソル行・列番号 |
| `{n} words` | 単語数（スペース区切り） |
| `{n} chars` | 総文字数 |
| `Python / PySide6` | バッジ表示（右端、固定） |

---

## ファイル構成

```
Python/
├── markdown_editor.py   # エントリポイント、QApplication 起動
├── main_window.py       # メインウィンドウ（MarkdownEditor クラス）
├── editor_widget.py     # 行番号付きエディタ（CodeEditor クラス）
├── search_dialog.py     # 検索・置換ダイアログ（SearchDialog クラス）
├── preview_html.py      # プレビュー用シェル HTML 生成
├── themes.py            # ライト / ダークテーマのカラー定義
├── requirements.txt     # 依存パッケージ一覧
├── build.sh             # macOS / Linux 向け PyInstaller ビルドスクリプト
└── build_windows.bat    # Windows 向け PyInstaller ビルドスクリプト
```

---

## ビルド（スタンドアロン配布）

```bash
# macOS / Linux
bash build.sh             # dist/SimpleMarkdownEditor.app
bash build.sh --onefile   # 単一バイナリ

# Windows
build_windows.bat
build_windows.bat --onefile
```

> **注意:** ビルドには PyInstaller を使用します。PyInstaller は GPL v2 ライセンスであるため、バイナリ配布時のライセンス適合性を事前に確認してください。

---

## 既知の制限・注意事項

| 項目 | 内容 |
|---|---|
| オフライン時の Mermaid | CDN から mermaid.js を読み込むためオフライン環境では図が表示されない |
| XSS | `marked.parse()` 相当の変換結果を `innerHTML` に直接挿入しており、DOMPurify 等のサニタイズは未実装 |
| PDF 出力 | WebEngine の印刷機能を使用するため、Mermaid 図のレンダリング完了前に PDF 生成すると図が欠けることがある |
| LGPL + PyInstaller | `--onefile` ビルドは PySide6 の静的バンドルとみなされる可能性があり、LGPL の再リンク条件を満たすか確認が必要 |
