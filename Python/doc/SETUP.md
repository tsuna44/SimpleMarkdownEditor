# SimpleMarkdownEditor — セットアップ手順書

## 動作環境

| 項目 | 要件 |
|---|---|
| Python | 3.10 以上（推奨: 3.14） |
| OS | macOS 13+、Windows 10/11、Ubuntu 22.04+ |
| Java | 17 以上（PlantUML 機能を使う場合のみ） |

---

## 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd SimpleMarkdownEditor/Python
```

---

## 2. 仮想環境の作成と有効化

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bat
python -m venv .venv
.venv\Scripts\activate
```

> 以降のコマンドはすべて仮想環境が有効な状態で実行してください。

---

## 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

インストールされるパッケージ:

| パッケージ | バージョン | 用途 |
|---|---|---|
| PySide6 | >=6.10, <6.12 | GUI フレームワーク (Qt6) |
| markdown | >=3.5 | Markdown → HTML 変換 |
| pygments | >=2.17 | コードブロックのシンタックスハイライト |

---

## 4. PlantUML のセットアップ（オプション）

PlantUML ダイアグラム（` ```plantuml ` ブロック）を使う場合のみ必要です。

### 方法 A: 同梱の `plantuml.jar` を使う

リポジトリの `vendor/` ディレクトリに `plantuml.jar` が含まれている場合は、Java をインストールするだけで自動的に検出されます。

```
vendor/
└── plantuml.jar   ← 同梱済み（git 管理対象）
```

### 方法 B: パッケージマネージャでインストール

#### macOS (Homebrew)

```bash
brew install plantuml
```

#### Ubuntu / Debian

```bash
sudo apt install plantuml
```

#### Windows

```bat
winget install PlantUML.PlantUML
```

いずれの方法でも Java (17 以上) が必要です。

#### Java のインストール

**macOS:**
```bash
brew install openjdk
```

**Ubuntu:**
```bash
sudo apt install default-jdk
```

**Windows:**
OpenJDK 公式サイト（https://adoptium.net）からインストーラをダウンロード。

---

## 5. 起動

```bash
# Python/ディレクトリで実行
python markdown_editor.py

# ファイルを指定して起動
python markdown_editor.py path/to/file.md
```

---

## 6. スタンドアロン配布物のビルド

依存パッケージに加えて PyInstaller が必要です。

```bash
pip install pyinstaller
```

### macOS / Linux

```bash
bash build.sh          # dist/SimpleMarkdownEditor.app (macOS) または dist/SimpleMarkdownEditor/ (Linux)
bash build.sh --clean  # build/ dist/ を削除してから再ビルド
```

### Windows

```bat
build_windows.bat
build_windows.bat --clean
```

> `--onefile` は PySide6 の LGPL ライセンス要件を満たせない可能性があります。
> 詳細は [DISTRIBUTION.md](DISTRIBUTION.md) を参照してください。

---

## トラブルシューティング

### `qt.qpa.plugin: Could not find the Qt platform plugin "cocoa"` (macOS)

PySide6 のバージョンが 6.12.x 以降の場合に発生する可能性があります。

```bash
pip install "PySide6>=6.10,<6.12"
```

macOS 26+ では APFS が pip インストール済みの `.dylib` に `UF_HIDDEN` フラグを付与する問題があります。
アプリ起動時に自動で `~/Library/Caches/SimpleMarkdownEditor/` へコピーして対処しています。

### `ModuleNotFoundError: No module named 'PySide6'`

仮想環境が有効になっていない可能性があります。

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### PlantUML ダイアグラムが表示されない

- Java がインストールされているか確認: `java -version`
- `vendor/plantuml.jar` が存在するか確認
- Homebrew でインストールした場合: `brew install plantuml` 後に再起動
- File > Settings から JVM ヒープメモリ・図サイズ上限を調整

### PDF エクスポートで Mermaid / PlantUML の図が欠ける

図のレンダリング完了前に印刷処理が走る場合があります。
プレビューで図が表示されたことを確認してから PDF エクスポートしてください。
