# Vendor Libraries

外部提供モジュールのバージョン管理ファイルです。
HTML版・Python版で共有して使用します。

## mermaid.min.js

| 項目 | 値 |
|---|---|
| バージョン | 11.13.0 |
| 取得元 | https://cdn.jsdelivr.net/npm/mermaid@11.13.0/dist/mermaid.min.js |
| 最新版確認 | https://www.npmjs.com/package/mermaid |

**更新手順:**
```bash
# 最新バージョンを確認
curl -s https://registry.npmjs.org/mermaid/latest | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])"

# バージョンを指定してダウンロード（例: 11.14.0）
curl -fsSL "https://cdn.jsdelivr.net/npm/mermaid@11.14.0/dist/mermaid.min.js" \
  -o vendor/mermaid.min.js

# VERSIONS.json と VERSIONS.md のバージョン番号を更新する
```

## plantuml.jar

| 項目 | 値 |
|---|---|
| バージョン | 1.2026.2 |
| 取得元 | https://github.com/plantuml/plantuml/releases |
| 最新版確認 | https://plantuml.com/download |

> `plantuml.jar` は `.gitignore` で除外されています（大容量バイナリのため）。
> 各自が公式サイトからダウンロードして `vendor/plantuml.jar` に配置してください。

**更新手順:**
```bash
# 公式リリースページからダウンロード
curl -fsSL "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" \
  -o vendor/plantuml.jar

# jar のバージョンを確認
unzip -p vendor/plantuml.jar META-INF/MANIFEST.MF | grep Implementation-Version

# VERSIONS.json と VERSIONS.md のバージョン番号を更新する
```
