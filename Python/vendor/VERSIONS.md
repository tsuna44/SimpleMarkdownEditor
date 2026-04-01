# Vendor Libraries

ここに配置したファイルを更新することでライブラリのバージョンアップが可能です。

## mermaid.min.js

| 項目 | 値 |
|---|---|
| バージョン | 11.13.0 |
| 取得元 | https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js |
| 最新版確認 | https://www.npmjs.com/package/mermaid |

**更新手順:**
```bash
# 最新の 10.x 系に更新
curl -fsSL "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js" \
  -o Python/vendor/mermaid.min.js

# バージョンを確認してこのファイルを更新
curl -s https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js -I \
  | grep x-jsd-version
```
