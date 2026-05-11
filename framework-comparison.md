# Electron / Tauri / PyWebView 比較

Markdown + Mermaid + PlantUML エディタの実装技術として3つのフレームワークを比較した結果です。

---

## 概要

| | Electron | Tauri | PyWebView |
|--|--|--|--|
| 言語 | JS / TS | Rust + JS | Python + JS |
| WebView | Chromium 内蔵 | OS 標準 | OS 標準 |
| 一言で | 最も実績ある選択肢 | 軽量・高速 | Python で完結 |

---

## 評価スコア（5段階）

| 観点 | Electron | Tauri | PyWebView |
|------|:--------:|:-----:|:---------:|
| 軽量さ | 1 | 5 | 3 |
| ビルドの簡単さ | 5 | 2 | 4 |
| JS 互換性 | 5 | 4 | 4 |
| Python 親和性 | 1 | 1 | 5 |
| エコシステム | 5 | 3 | 4 |
| デバッグ容易さ | 5 | 3 | 3 |
| 長期保守性 | 4 | 5 | 3 |
| セキュリティ | 3 | 5 | 3 |

---

## 詳細比較

| 項目 | Electron | Tauri | PyWebView |
|------|----------|-------|-----------|
| バイナリサイズ | 約 80 MB | 約 5 MB | 約 30 MB |
| メモリ使用量 | 多い (Chromium) | 少ない | 中程度 |
| 起動速度 | やや遅い | 速い | 中程度 |
| ビルド環境 | Node.js のみ | Rust + Node.js | Python のみ |
| クロスコンパイル | 不可 | 不可（公式非対応） | 不可 |
| WebView | Chromium 内蔵 | OS 標準 | OS 標準 |
| Monaco 相性 | ◎ 完璧 | ◎ 問題なし | ◎ 問題なし |
| Mermaid 相性 | ◎ 完璧 | ◎ 問題なし | ◎ 問題なし |
| PlantUML 連携 | Node child_process | Rust Command | Python subprocess |
| 学習コスト | 低い（JS のみ） | 高い（Rust 要） | 低い（Python + JS） |
| エコシステム | 最大・npm 豊富 | 成長中 | PyPI + npm 両方 |
| デバッグしやすさ | ◎ DevTools 完備 | ○ DevTools あり | ○ DevTools あり |
| Python 連携 | △ 別プロセス要 | △ 別プロセス要 | ◎ ネイティブ |
| 本番採用実績 | VS Code / Slack 等 | 増加中 | 中規模ツール向け |

---

## こんな場合におすすめ

### Electron
- Rust を学びたくない
- npm の資産を最大限使いたい
- レンダリングの一貫性が重要
- チームが JS / TS に慣れている
- VS Code プラグインと連携したい

### Tauri
- バイナリサイズを最小にしたい
- メモリ効率を最優先したい
- Rust を使える、またはのびしろが欲しい
- セキュリティを重視する
- 長期的に保守する予定がある

### PyWebView
- Python 資産を活用したい
- データ処理・AI 連携が将来必要
- JS に慣れていない
- pip で依存解決できると嬉しい
- プロトタイプを素早く作りたい

---

## 総評

**今回のアプリ（Monaco + Mermaid + PlantUML + タブ・完全オフライン・Windows/macOS）という用途での評価：**

- **Electron** — 迷ったらこれ。VS Code と同じ環境なので Monaco との親和性が最高。サイズが大きい以外に欠点がほぼない。
- **Tauri** — 軽量重視ならベスト。ただし Rust を書ける人がチームにいることが前提。Rust が書けないと保守が辛くなる。
- **PyWebView** — Python 資産や将来の AI / データ処理連携を考えているならこれ一択。3つの中で最も Python らしく拡張できる。

強いて1つ選ぶなら **PyWebView** がバランスよく、将来の機能追加（AI による図の自動生成など）にも対応しやすい。
