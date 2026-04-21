# SimpleMarkdownEditor — メンテナンス手順書

## 1. ベンダーライブラリの更新

### 1-1. Mermaid の更新

`update_mermaid.py` スクリプトで自動更新できます。リポジトリルートで実行してください。

```bash
# 現在バージョンと最新バージョンを確認するだけ（更新しない）
python update_mermaid.py --check

# 最新バージョンに更新
python update_mermaid.py

# バージョンを指定して更新
python update_mermaid.py 11.14.0
```

スクリプトは以下を自動で行います。

| 処理 | 対象ファイル |
|------|-------------|
| mermaid.min.js を CDN からダウンロード | `vendor/mermaid.min.js` |
| HTML 版のインライン JS を置換 | `HTML/standalone_SimpleMarkdownEditor.html` |
| バージョン情報を更新 | `vendor/VERSIONS.json` |

> ネットワーク接続が必要です。

---

### 1-2. elkjs の更新

`update_elk.py` スクリプトで自動更新できます。リポジトリルートで実行してください。

```bash
# 現在バージョンと最新バージョンを確認するだけ（更新しない）
python update_elk.py --check

# 最新バージョンに更新
python update_elk.py

# バージョンを指定して更新
python update_elk.py 0.11.1
```

スクリプトは以下を自動で行います。

| 処理 | 対象ファイル |
|------|-------------|
| elk.bundled.js を CDN からダウンロード | `vendor/elk.bundled.js` |
| HTML 版のインライン JS を置換 | `HTML/standalone_SimpleMarkdownEditor.html` |
| バージョン情報を更新 | `vendor/VERSIONS.json` |

> ネットワーク接続が必要です。

---

### 1-3. PlantUML の更新

`plantuml.jar` はバイナリサイズが大きいため `.gitignore` で除外されており、手動更新が必要です。

#### 手順

```bash
# リポジトリルートで実行
# 最新バージョンをダウンロード
curl -fsSL "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" \
  -o vendor/plantuml.jar

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" `
  -OutFile "vendor\plantuml.jar"
```

#### バージョン確認

```bash
java -jar vendor/plantuml.jar -version

# Windows (PowerShell)
java -jar vendor\plantuml.jar -version
```

#### VERSIONS.json を更新

`vendor/VERSIONS.json` の `plantuml` フィールドを実際のバージョン番号に更新してください。

```json
{
  "mermaid": "11.13.0",
  "elkjs":   "0.11.1",
  "plantuml": "1.2026.3"   ← ここを更新
}
```

---

## 2. Python 依存パッケージの更新

```bash
cd Python/
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 更新可能なパッケージを確認
pip list --outdated

# requirements.txt の範囲内で更新
pip install -r requirements.txt --upgrade

# requirements.txt のバージョン範囲を変更する場合は編集後に再インストール
pip install -r requirements.txt
```

---

## 3. アプリの設定ファイル

ユーザー設定は INI 形式のファイルに保存されます。レジストリは使用しません。

### 保存場所

| OS | パス |
|----|------|
| Windows | `%APPDATA%\SimpleMarkdownEditor\SimpleMarkdownEditor\settings.ini` |
| macOS | `~/Library/Preferences/SimpleMarkdownEditor/SimpleMarkdownEditor/settings.ini` |
| Linux | `~/.config/SimpleMarkdownEditor/SimpleMarkdownEditor/settings.ini` |

### 保存される設定

| キー | 型 | 内容 | デフォルト |
|------|----|------|-----------|
| `last_dir` | 文字列 | ファイルダイアログで最後に使用したフォルダパス | ホームディレクトリ |
| `recent_files` | JSON 配列 | 最近使ったファイルのパス一覧（最大 10 件） | `[]` |
| `puml_jvm_mem` | 文字列 | PlantUML JVM ヒープメモリ (`-Xmx`) | `1g` |
| `puml_limit_size` | 整数 | PlantUML 図サイズ上限 (px) | `32768` |

### 設定のリセット

設定をリセットしたい場合は、上記の `settings.ini` ファイルを削除してください。
アプリの次回起動時にホームディレクトリを初期値として再作成されます。

### アンインストール時の後始末

アプリ本体の削除に加えて、上記の設定ファイルが残る場合があります。
必要に応じて手動で削除してください。

---

## 4. Qt platform plugin キャッシュのクリア（macOS）

macOS 26+ では APFS が PySide6 の `.dylib` に `UF_HIDDEN` フラグを付与することがあります。
アプリ起動時に自動で以下のキャッシュディレクトリへコピーして対処しています。

```
~/Library/Caches/SimpleMarkdownEditor/Qt/plugins/platforms/
```

プラグインの問題が疑われる場合は、このディレクトリを削除すると次回起動時に再生成されます。

```bash
rm -rf ~/Library/Caches/SimpleMarkdownEditor/
```
