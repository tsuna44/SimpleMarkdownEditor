#!/usr/bin/env python3
"""
build.py — Markdown Editor スタンドアロン版ビルドスクリプト

使い方:
    python build.py          # または python3 build.py

必要なもの:
    - Python 3.6 以上（macOS / Linux / Windows 標準搭載）
    - インターネット接続（初回ダウンロード時のみ）

出力:
    standalone_SimpleMarkdownEditor.html  ←  これ1ファイルで完全動作（外部通信ゼロ）
"""

import sys, os, urllib.request, gzip, json, re

# ── ダウンロード対象 ──────────────────────────────────────────────────
LIBS = [
    {
        "name": "marked.js",
        "urls": [
            "https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js",
            "https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js",
        ],
        "tag": "MARKED_JS",
        "wrap": "script",
    },
    {
        "name": "highlight.js",
        "urls": [
            "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js",
            "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js",
        ],
        "tag": "HLJS_JS",
        "wrap": "script",
    },
    {
        "name": "highlight.js (light CSS)",
        "urls": [
            "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css",
            "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github.min.css",
        ],
        "tag": "HLJS_LIGHT_CSS",
        "wrap": "style",
    },
    {
        "name": "highlight.js (dark CSS)",
        "urls": [
            "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css",
            "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github-dark.min.css",
        ],
        "tag": "HLJS_DARK_CSS",
        "wrap": "style",
    },
    {
        "name": "mermaid.js",
        "urls": [
            "https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.6.1/mermaid.min.js",
        ],
        "tag": "MERMAID_JS",
        "wrap": "script",
    },
]

def download(urls, name):
    """複数URLを試してダウンロード。成功したらテキストを返す。"""
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
                if r.info().get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
                text = data.decode("utf-8")
                size_kb = len(data) // 1024
                print(f"  ✓  {name:<28} {size_kb:>5} KB  ({url.split('/')[2]})")
                return text
        except Exception as e:
            print(f"  ⚠  {name} — {url.split('/')[2]} 失敗: {e}")
    raise RuntimeError(f"❌ {name} のダウンロードに失敗しました。インターネット接続を確認してください。")

def build():
    print("\n" + "="*56)
    print("  Markdown Editor — スタンドアロン版ビルド")
    print("="*56)
    print(f"\n  Python {sys.version.split()[0]}  |  {sys.platform}\n")

    # ── ライブラリをダウンロード ────────────────────────────────────
    print("📦 ライブラリをダウンロード中...\n")
    downloaded = {}
    for lib in LIBS:
        downloaded[lib["tag"]] = download(lib["urls"], lib["name"])

    # ── アプリ本体HTML（ライブラリ参照部分を除いた純粋なアプリ） ─────
    # standalone版では動的ロード・CDN参照を全て取り除き、
    # インラインで直接埋め込む
    APP_HTML = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Markdown Editor</title>

<!-- highlight.js CSS (light) — インライン埋め込み -->
<style id="hljs-light-style">
%%HLJS_LIGHT_CSS%%
</style>
<!-- highlight.js CSS (dark) — インライン埋め込み -->
<style id="hljs-dark-style" disabled>
%%HLJS_DARK_CSS%%
</style>

<style>
  :root {
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    --font-sans: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;
    --radius: 6px;
    --toolbar-h: 48px;
    --statusbar-h: 28px;
    --transition: 180ms ease;
  }

  :root, [data-theme="light"] {
    --bg: #f5f4f0; --surface: #ffffff; --surface2: #f0ede8;
    --border: #ddd9d2; --text: #1a1814; --text2: #6b6560;
    --accent: #c0603a; --accent-bg: #fdf1ed;
    --toolbar-bg: #edeae5; --toolbar-btn: #1a1814;
    --toolbar-btn-hover: #c0603a; --toolbar-btn-active-bg: #ddd9d2;
    --gutter: #bbb7b0; --preview-h1: #c0603a;
    --preview-code-bg: #f0ede8; --preview-blockquote: #c0603a;
    --scrollbar: #ddd9d2; --scrollbar-thumb: #b8b4ae;
    --divider: #ddd9d2; --status-bg: #edeae5; --status-text: #6b6560;
  }
  [data-theme="dark"] {
    --bg: #161512; --surface: #1e1c1a; --surface2: #252320;
    --border: #35312e; --text: #e8e4df; --text2: #857f79;
    --accent: #e07a52; --accent-bg: #2a1e18;
    --toolbar-bg: #252320; --toolbar-btn: #c8c4bf;
    --toolbar-btn-hover: #e07a52; --toolbar-btn-active-bg: #35312e;
    --gutter: #4a4642; --preview-h1: #e07a52;
    --preview-code-bg: #252320; --preview-blockquote: #e07a52;
    --scrollbar: #252320; --scrollbar-thumb: #3f3b38;
    --divider: #35312e; --status-bg: #1a1916; --status-text: #6b6560;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    height: 100%; font-family: var(--font-sans);
    background: var(--bg); color: var(--text);
    transition: background var(--transition), color var(--transition);
    overflow: hidden;
  }
  #app { display: flex; flex-direction: column; height: 100vh; }

  /* ── Toolbar ── */
  #toolbar {
    display: flex; align-items: center; gap: 2px;
    height: var(--toolbar-h); padding: 0 10px;
    background: var(--toolbar-bg); border-bottom: 1px solid var(--border);
    flex-shrink: 0; user-select: none; overflow-x: auto;
  }
  .tb-sep { width: 1px; height: 22px; background: var(--border); margin: 0 4px; flex-shrink: 0; }
  .tb-spacer { flex: 1; min-width: 8px; }
  .tb-btn {
    display: flex; align-items: center; justify-content: center; gap: 5px;
    height: 32px; padding: 0 9px; border: none; border-radius: var(--radius);
    background: transparent; color: var(--toolbar-btn);
    font-family: var(--font-mono); font-size: 12px; font-weight: 500;
    cursor: pointer; transition: background var(--transition), color var(--transition);
    white-space: nowrap; flex-shrink: 0;
  }
  .tb-btn:hover { background: var(--toolbar-btn-active-bg); color: var(--toolbar-btn-hover); }
  .tb-btn:active { opacity: .75; }
  .tb-btn svg { width: 15px; height: 15px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; flex-shrink: 0; }
  .tb-btn.icon-only { padding: 0 8px; }
  #filename-display {
    font-family: var(--font-mono); font-size: 12px; color: var(--text2);
    padding: 0 8px; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }

  /* ── Panes ── */
  #panes { display: flex; flex: 1; overflow: hidden; position: relative; }
  #editor-pane, #preview-pane { flex: 1; overflow: hidden; display: flex; flex-direction: column; min-width: 0; }
  #editor-pane { border-right: 1px solid var(--divider); }
  .pane-label {
    font-size: 11px; font-weight: 500; letter-spacing: .08em; text-transform: uppercase;
    color: var(--text2); padding: 5px 14px 4px;
    background: var(--surface2); border-bottom: 1px solid var(--border); flex-shrink: 0;
  }

  /* ── Editor ── */
  #editor-wrap {
    flex: 1; overflow: auto; background: var(--surface); display: flex;
    scrollbar-width: thin; scrollbar-color: var(--scrollbar-thumb) var(--scrollbar);
  }
  #line-numbers {
    flex-shrink: 0; width: 44px; padding: 14px 0;
    text-align: right; font-family: var(--font-mono); font-size: 13px; line-height: 1.65;
    color: var(--gutter); background: var(--surface2); border-right: 1px solid var(--border);
    pointer-events: none; user-select: none;
  }
  #line-numbers span { display: block; padding-right: 8px; }
  #editor {
    flex: 1; padding: 14px 16px; font-family: var(--font-mono); font-size: 13.5px;
    line-height: 1.65; border: none; outline: none; resize: none;
    background: transparent; color: var(--text); tab-size: 2;
    caret-color: var(--accent);
    scrollbar-width: thin; scrollbar-color: var(--scrollbar-thumb) var(--scrollbar);
    white-space: pre; overflow-wrap: normal; overflow-x: auto; overflow-y: visible;
  }
  #editor::selection { background: var(--accent-bg); }

  /* ── Preview ── */
  #preview-pane { background: var(--surface); }
  #preview { flex: 1; padding: 24px 32px; overflow: auto; font-size: 15px; line-height: 1.75; scrollbar-width: thin; scrollbar-color: var(--scrollbar-thumb) var(--scrollbar); }
  #preview h1,#preview h2,#preview h3,#preview h4,#preview h5,#preview h6 { font-weight: 700; margin: 1.4em 0 .5em; color: var(--preview-h1); font-family: var(--font-sans); }
  #preview h1 { font-size: 1.9em; border-bottom: 2px solid var(--accent); padding-bottom: .25em; }
  #preview h2 { font-size: 1.45em; border-bottom: 1px solid var(--border); padding-bottom: .2em; }
  #preview h3 { font-size: 1.2em; }
  #preview p { margin: .75em 0; }
  #preview a { color: var(--accent); text-decoration: underline; }
  #preview strong { font-weight: 700; }
  #preview em { font-style: italic; }
  #preview code { font-family: var(--font-mono); font-size: .88em; background: var(--preview-code-bg); padding: .15em .4em; border-radius: 4px; color: var(--accent); }
  #preview pre { background: var(--preview-code-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; overflow-x: auto; margin: 1em 0; }
  #preview pre code { background: none; padding: 0; color: var(--text); font-size: .85em; }
  #preview blockquote { border-left: 3px solid var(--preview-blockquote); margin: 1em 0; padding: .5em 1em; color: var(--text2); background: var(--accent-bg); border-radius: 0 var(--radius) var(--radius) 0; }
  #preview ul, #preview ol { padding-left: 1.5em; margin: .75em 0; }
  #preview li { margin: .3em 0; }
  #preview table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  #preview th, #preview td { border: 1px solid var(--border); padding: .5em .8em; text-align: left; }
  #preview th { background: var(--surface2); font-weight: 600; }
  #preview tr:nth-child(even) td { background: var(--surface2); }
  #preview img { max-width: 100%; border-radius: var(--radius); }
  #preview hr { border: none; border-top: 1px solid var(--border); margin: 1.5em 0; }
  #preview .mermaid-wrap { position: relative; margin: 1em 0; padding: 16px 16px 44px; background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); text-align: center; overflow-x: auto; }
  #preview .mermaid-wrap:hover .mermaid-actions { opacity: 1; }
  #preview .mermaid-actions { position: absolute; bottom: 8px; right: 8px; display: flex; gap: 6px; opacity: 0; transition: opacity .2s; }
  #preview .mermaid-copy-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border: 1px solid var(--border); border-radius: 4px; background: var(--surface); color: var(--text2); font-family: var(--font-mono); font-size: 11px; cursor: pointer; transition: background .15s, color .15s, border-color .15s; }
  #preview .mermaid-copy-btn:hover { background: var(--accent); color: #fff; border-color: var(--accent); }
  #preview .mermaid-copy-btn.copied { background: #2a7a2a; color: #fff; border-color: #2a7a2a; }
  #preview .mermaid-copy-btn svg { width: 12px; height: 12px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
  #preview .mermaid-error { color: #c0392b; font-family: var(--font-mono); font-size: 12px; padding: 8px; background: #fdf0f0; border-radius: 4px; text-align: left; }

  /* ── Search Panel ── */
  #search-panel { display: none; position: absolute; top: 8px; right: 16px; width: 380px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: 0 4px 20px rgba(0,0,0,.18); z-index: 100; font-family: var(--font-mono); font-size: 12px; overflow: hidden; }
  #search-panel.open { display: block; animation: sp-in .15s ease; }
  @keyframes sp-in { from { opacity:0; transform:translateY(-6px); } to { opacity:1; transform:none; } }
  .sp-row { display: flex; align-items: center; gap: 4px; padding: 6px 8px; border-bottom: 1px solid var(--border); }
  .sp-row:last-child { border-bottom: none; }
  .sp-input { flex: 1; height: 26px; padding: 0 8px; background: var(--surface2); border: 1px solid var(--border); border-radius: 4px; color: var(--text); font-family: var(--font-mono); font-size: 12px; outline: none; transition: border-color .15s; }
  .sp-input:focus { border-color: var(--accent); }
  .sp-input.sp-error { border-color: #c0392b; background: #fdf0f0; }
  .sp-toggle { display: flex; align-items: center; justify-content: center; width: 26px; height: 26px; border: 1px solid transparent; border-radius: 4px; background: transparent; color: var(--text2); font-family: var(--font-mono); font-size: 10px; font-weight: 700; cursor: pointer; transition: background .15s, color .15s, border-color .15s; flex-shrink: 0; user-select: none; }
  .sp-toggle:hover { background: var(--toolbar-btn-active-bg); color: var(--text); }
  .sp-toggle.active { background: var(--accent-bg); color: var(--accent); border-color: var(--accent); }
  .sp-btn { display: flex; align-items: center; justify-content: center; width: 26px; height: 26px; border: 1px solid var(--border); border-radius: 4px; background: transparent; color: var(--text2); cursor: pointer; transition: background .15s, color .15s; flex-shrink: 0; }
  .sp-btn:hover { background: var(--toolbar-btn-active-bg); color: var(--text); }
  .sp-btn:disabled { opacity: .35; cursor: default; }
  .sp-btn svg { width: 13px; height: 13px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
  .sp-btn.sp-replace-one { padding: 0 8px; width: auto; font-size: 11px; white-space: nowrap; }
  .sp-btn.sp-replace-all { padding: 0 8px; width: auto; font-size: 11px; white-space: nowrap; background: var(--accent-bg); color: var(--accent); border-color: var(--accent); }
  .sp-btn.sp-replace-all:hover { background: var(--accent); color: #fff; }
  .sp-count { color: var(--text2); font-size: 11px; white-space: nowrap; min-width: 60px; text-align: right; padding-right: 2px; }
  .sp-count.sp-no-match { color: #c0392b; }
  .sp-close { display: flex; align-items: center; justify-content: center; width: 22px; height: 22px; border: none; border-radius: 4px; background: transparent; color: var(--text2); cursor: pointer; font-size: 16px; line-height: 1; flex-shrink: 0; transition: background .15s, color .15s; }
  .sp-close:hover { background: var(--toolbar-btn-active-bg); color: var(--text); }

  /* ── Resizer ── */
  #resizer { width: 4px; cursor: col-resize; background: var(--divider); flex-shrink: 0; transition: background .1s; z-index: 10; }
  #resizer:hover, #resizer.dragging { background: var(--accent); }

  /* ── Status bar ── */
  #statusbar { display: flex; align-items: center; gap: 16px; height: var(--statusbar-h); padding: 0 14px; background: var(--status-bg); border-top: 1px solid var(--border); font-family: var(--font-mono); font-size: 11px; color: var(--status-text); flex-shrink: 0; }
  #standalone-badge { margin-left: auto; background: #2a5a8a; color: #fff; font-size: 10px; padding: 2px 8px; border-radius: 10px; }

  /* ── Toast ── */
  #toast { position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%) translateY(10px); background: var(--text); color: var(--surface); font-size: 12px; font-family: var(--font-sans); padding: 8px 16px; border-radius: 20px; opacity: 0; pointer-events: none; transition: opacity .25s, transform .25s; z-index: 9999; white-space: nowrap; }
  #toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: var(--scrollbar); }
  ::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 3px; }

  [data-theme="dark"] #hljs-light-style { display: none; }
  [data-theme="dark"] #hljs-dark-style { display: block !important; }
  [data-theme="light"] #hljs-dark-style { display: none; }
</style>
</head>
<body>
<div id="app">
  <div id="toolbar">
    <button class="tb-btn" onclick="insert('heading1')" title="見出し1 (H1)"><svg viewBox="0 0 24 24"><text x="2" y="17" font-size="14" stroke="none" fill="currentColor" font-weight="700" font-family="sans-serif">H1</text></svg></button>
    <button class="tb-btn" onclick="insert('heading2')" title="見出し2 (H2)"><svg viewBox="0 0 24 24"><text x="2" y="17" font-size="14" stroke="none" fill="currentColor" font-weight="700" font-family="sans-serif">H2</text></svg></button>
    <button class="tb-btn" onclick="insert('heading3')" title="見出し3 (H3)"><svg viewBox="0 0 24 24"><text x="2" y="17" font-size="14" stroke="none" fill="currentColor" font-weight="700" font-family="sans-serif">H3</text></svg></button>
    <div class="tb-sep"></div>
    <button class="tb-btn icon-only" onclick="insert('bold')" title="太字 (Ctrl+B)"><svg viewBox="0 0 24 24"><path d="M6 4h8a4 4 0 010 8H6z"/><path d="M6 12h9a4 4 0 010 8H6z"/></svg></button>
    <button class="tb-btn icon-only" onclick="insert('italic')" title="斜体 (Ctrl+I)"><svg viewBox="0 0 24 24"><line x1="19" y1="4" x2="10" y2="4"/><line x1="14" y1="20" x2="5" y2="20"/><line x1="15" y1="4" x2="9" y2="20"/></svg></button>
    <button class="tb-btn icon-only" onclick="insert('strikethrough')" title="打ち消し線"><svg viewBox="0 0 24 24"><path d="M16 4H9a3 3 0 00-2.83 4"/><path d="M14 20H8a3 3 0 01-2.83-4"/><line x1="4" y1="12" x2="20" y2="12"/></svg></button>
    <button class="tb-btn icon-only" onclick="insert('inlinecode')" title="インラインコード"><svg viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg></button>
    <div class="tb-sep"></div>
    <button class="tb-btn" onclick="insert('ul')" title="箇条書き"><svg viewBox="0 0 24 24"><line x1="9" y1="6" x2="20" y2="6"/><line x1="9" y1="12" x2="20" y2="12"/><line x1="9" y1="18" x2="20" y2="18"/><circle cx="4" cy="6" r="1.5" stroke="none" fill="currentColor"/><circle cx="4" cy="12" r="1.5" stroke="none" fill="currentColor"/><circle cx="4" cy="18" r="1.5" stroke="none" fill="currentColor"/></svg></button>
    <button class="tb-btn" onclick="insert('ol')" title="番号付きリスト"><svg viewBox="0 0 24 24"><line x1="10" y1="6" x2="21" y2="6"/><line x1="10" y1="12" x2="21" y2="12"/><line x1="10" y1="18" x2="21" y2="18"/><text x="2" y="9" font-size="7" stroke="none" fill="currentColor" font-family="sans-serif">1.</text><text x="2" y="15" font-size="7" stroke="none" fill="currentColor" font-family="sans-serif">2.</text><text x="2" y="21" font-size="7" stroke="none" fill="currentColor" font-family="sans-serif">3.</text></svg></button>
    <button class="tb-btn" onclick="insert('blockquote')" title="引用"><svg viewBox="0 0 24 24"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"/><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"/></svg></button>
    <button class="tb-btn" onclick="insert('codeblock')" title="コードブロック"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9l-3 3 3 3"/><path d="M15 9l3 3-3 3"/></svg></button>
    <button class="tb-btn" onclick="insert('mermaid')" title="Mermaid ダイアグラム"><svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><line x1="12" y1="7" x2="5" y2="17"/><line x1="12" y1="7" x2="19" y2="17"/></svg></button>
    <button class="tb-btn" onclick="insert('table')" title="テーブル"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="12" y1="3" x2="12" y2="21"/></svg></button>
    <button class="tb-btn" onclick="insert('link')" title="リンク (Ctrl+K)"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg></button>
    <button class="tb-btn" onclick="insert('hr')" title="水平線"><svg viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"/></svg></button>
    <div class="tb-sep"></div>
    <button class="tb-btn" onclick="newFile()" title="新規ファイル"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></button>
    <button class="tb-btn" onclick="openFile()" title="ファイルを開く"><svg viewBox="0 0 24 24"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg></button>
    <button class="tb-btn" onclick="saveFile()" title="保存 (Ctrl+S)"><svg viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg></button>
    <div class="tb-spacer"></div>
    <span id="filename-display">untitled.md</span>
    <div class="tb-sep"></div>
    <button class="tb-btn icon-only" onclick="toggleTheme()" title="テーマ切り替え">
      <svg id="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      <svg id="icon-moon" viewBox="0 0 24 24" style="display:none"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
    </button>
    <button class="tb-btn icon-only" onclick="toggleSearchPanel()" id="search-tb-btn" title="検索・置換 (Ctrl+F)"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></button>
  </div>

  <div id="search-panel">
    <div class="sp-row">
      <input id="sp-search" class="sp-input" type="text" placeholder="検索..." autocomplete="off" spellcheck="false">
      <button class="sp-toggle" id="sp-btn-case" onclick="spToggle('case')" title="大文字小文字を区別 (Alt+C)">Aa</button>
      <button class="sp-toggle" id="sp-btn-regex" onclick="spToggle('regex')" title="正規表現 (Alt+R)">.*</button>
      <button class="sp-btn" id="sp-prev" onclick="spMove(-1)" title="前へ (Shift+Enter)"><svg viewBox="0 0 24 24"><polyline points="18 15 12 9 6 15"/></svg></button>
      <button class="sp-btn" id="sp-next" onclick="spMove(1)" title="次へ (Enter)"><svg viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg></button>
      <span class="sp-count" id="sp-count"></span>
      <button class="sp-close" onclick="closeSearchPanel()" title="閉じる (Esc)">×</button>
    </div>
    <div class="sp-row">
      <input id="sp-replace" class="sp-input" type="text" placeholder="置換..." autocomplete="off" spellcheck="false">
      <button class="sp-btn sp-replace-one" onclick="spReplaceOne()" title="置換">置換</button>
      <button class="sp-btn sp-replace-all" onclick="spReplaceAll()" title="すべて置換">すべて置換</button>
    </div>
  </div>

  <div id="panes">
    <div id="editor-pane" style="position:relative">
      <div class="pane-label">Editor</div>
      <div id="editor-wrap">
        <div id="line-numbers"></div>
        <textarea id="editor" spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"></textarea>
      </div>
    </div>
    <div id="resizer"></div>
    <div id="preview-pane">
      <div class="pane-label">Preview</div>
      <div id="preview"></div>
    </div>
  </div>

  <div id="statusbar">
    <span id="stat-chars">文字数: 0</span>
    <span id="stat-lines">行数: 1</span>
    <span id="stat-words">単語数: 0</span>
    <span id="stat-cursor">行: 1, 列: 1</span>
    <span id="standalone-badge">● スタンドアロン</span>
  </div>
</div>

<div id="toast"></div>
<input type="file" id="file-input" accept=".md,.txt,.markdown" style="display:none">

<!-- marked.js — インライン埋め込み -->
<script>%%MARKED_JS%%</script>
<!-- highlight.js — インライン埋め込み -->
<script>%%HLJS_JS%%</script>
<!-- mermaid.js — インライン埋め込み -->
<script>%%MERMAID_JS%%</script>

<script>
// Polyfill
if (!Array.prototype.findLastIndex) {
  Array.prototype.findLastIndex = function(fn) {
    for (let i = this.length - 1; i >= 0; i--) { if (fn(this[i], i, this)) return i; }
    return -1;
  };
}

// ── Main App ──────────────────────────────────────────────────────
(function() {
  const editor = document.getElementById('editor');
  const preview = document.getElementById('preview');
  const lineNumbers = document.getElementById('line-numbers');
  const filenameDisplay = document.getElementById('filename-display');
  let currentFilename = 'untitled.md';
  let mermaidCounter = 0;
  let renderTimer = null;

  // ── Theme ───────────────────────────────────────────────────────
  function getSystemTheme() { return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; }
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.getElementById('icon-sun').style.display = theme === 'dark' ? 'none' : '';
    document.getElementById('icon-moon').style.display = theme === 'dark' ? '' : 'none';
    document.getElementById('hljs-dark-style').disabled = theme !== 'dark';
    document.getElementById('hljs-light-style').disabled = theme === 'dark';
    localStorage.setItem('md-theme', theme);
    scheduleRender();
  }
  window.toggleTheme = function() { applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'); };
  (function() {
    applyTheme(localStorage.getItem('md-theme') || getSystemTheme());
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => { if (!localStorage.getItem('md-theme')) applyTheme(e.matches ? 'dark' : 'light'); });
  })();

  // ── Mermaid ─────────────────────────────────────────────────────
  function initMermaid() {
    mermaid.initialize({
      startOnLoad: false,
      theme: document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'default',
      securityLevel: 'loose',
      fontFamily: 'trebuchet ms, verdana, arial, sans-serif',
      fontSize: 16,
      flowchart: { useMaxWidth: true, htmlLabels: false, curve: 'basis' },
      sequence: { useMaxWidth: true },
      gantt:    { useMaxWidth: true },
    });
  }
  initMermaid();

  // ── marked ──────────────────────────────────────────────────────
  marked.setOptions({ gfm: true, breaks: true });
  const renderer = new marked.Renderer();
  renderer.code = function(code, lang) {
    if (lang === 'mermaid') {
      return `<div class="mermaid-wrap" data-mermaid-id="mmd-${++mermaidCounter}" data-mermaid-code="${encodeURIComponent(code)}"></div>`;
    }
    let h;
    try { h = lang && hljs.getLanguage(lang) ? hljs.highlight(code,{language:lang}).value : hljs.highlightAuto(code).value; }
    catch(e) { h = code.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
    return `<pre><code class="hljs language-${lang||''}">${h}</code></pre>`;
  };
  marked.use({ renderer });

  // ── Mermaid copy helpers ─────────────────────────────────────────
  async function copySvg(wrap) { const s=wrap.querySelector('svg'); if(!s)return; await navigator.clipboard.writeText(new XMLSerializer().serializeToString(s)); }
  function openSvgInTab(wrap) {
    const svg=wrap.querySelector('svg'); if(!svg)return;
    const clone=svg.cloneNode(true);
    clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
    clone.setAttribute('xmlns:xlink','http://www.w3.org/1999/xlink');
    const bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
    const w=svg.getBoundingClientRect().width||svg.viewBox.baseVal.width||800;
    const h=svg.getBoundingClientRect().height||svg.viewBox.baseVal.height||600;
    bg.setAttribute('width',w);bg.setAttribute('height',h);bg.setAttribute('fill','#ffffff');
    clone.insertBefore(bg,clone.firstChild);
    const blob=new Blob([new XMLSerializer().serializeToString(clone)],{type:'image/svg+xml;charset=utf-8'});
    const url=URL.createObjectURL(blob);
    window.open(url,'_blank');
    setTimeout(()=>URL.revokeObjectURL(url),10000);
  }
  function flashBtn(btn, label) { btn.classList.add('copied'); btn.textContent='✓ 完了'; setTimeout(()=>{ btn.classList.remove('copied'); btn.textContent=label; },1800); }
  function addCopyButtons(wrap) {
    const actions=document.createElement('div'); actions.className='mermaid-actions';
    const tabBtn=document.createElement('button'); tabBtn.className='mermaid-copy-btn';
    tabBtn.innerHTML='<svg viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg> 別タブ(PNG)';
    tabBtn.title='別タブで開いて右クリック→「名前を付けて画像を保存」でPNG保存';
    tabBtn.onclick=()=>{ openSvgInTab(wrap); flashBtn(tabBtn,'別タブ(PNG)'); };
    const svgBtn=document.createElement('button'); svgBtn.className='mermaid-copy-btn';
    svgBtn.innerHTML='<svg viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg> SVGコピー';
    svgBtn.title='SVGテキストをクリップボードにコピー';
    svgBtn.onclick=async()=>{ try{await copySvg(wrap);flashBtn(svgBtn,'SVGコピー');showToast('SVG をコピーしました');}catch(e){showToast('SVG コピー失敗');} };
    const dlBtn=document.createElement('button'); dlBtn.className='mermaid-copy-btn';
    dlBtn.innerHTML='<svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> SVG保存';
    dlBtn.title='SVGファイルとしてダウンロード';
    dlBtn.onclick=()=>{
      const svg=wrap.querySelector('svg'); if(!svg)return;
      const blob=new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml;charset=utf-8'});
      const url=URL.createObjectURL(blob),a=document.createElement('a');
      a.href=url;a.download='diagram.svg';a.click();URL.revokeObjectURL(url);
      flashBtn(dlBtn,'SVG保存');showToast('SVG をダウンロードしました');
    };
    actions.append(tabBtn,svgBtn,dlBtn); wrap.appendChild(actions);
  }

  // ── Render ───────────────────────────────────────────────────────
  async function renderPreview() {
    mermaidCounter = 0;
    preview.innerHTML = marked.parse(editor.value);
    const wraps = preview.querySelectorAll('[data-mermaid-id]');
    if (!wraps.length) return;
    initMermaid();
    for (const wrap of wraps) {
      const code = decodeURIComponent(wrap.dataset.mermaidCode);
      const id = wrap.dataset.mermaidId;
      try { const {svg} = await mermaid.render('m'+id, code); wrap.innerHTML=svg; addCopyButtons(wrap); }
      catch(e) { wrap.innerHTML=`<div class="mermaid-error">⚠ Mermaid エラー: ${e.message||e}</div>`; }
    }
  }
  function scheduleRender() { clearTimeout(renderTimer); renderTimer=setTimeout(renderPreview,200); }

  // ── Line numbers ─────────────────────────────────────────────────
  function updateLineNumbers() {
    lineNumbers.innerHTML = Array.from({length:editor.value.split('\n').length},(_,i)=>`<span>${i+1}</span>`).join('');
    lineNumbers.scrollTop = editor.scrollTop;
  }
  editor.addEventListener('scroll', () => { lineNumbers.scrollTop=editor.scrollTop; });

  // ── Status bar ───────────────────────────────────────────────────
  function updateStatus() {
    const text=editor.value, lines=text.split('\n');
    document.getElementById('stat-chars').textContent=`文字数: ${text.length}`;
    document.getElementById('stat-lines').textContent=`行数: ${lines.length}`;
    document.getElementById('stat-words').textContent=`単語数: ${text.trim()?text.trim().split(/\s+/).length:0}`;
    const before=text.substring(0,editor.selectionStart), ln=before.split('\n').length, col=before.split('\n').pop().length+1;
    document.getElementById('stat-cursor').textContent=`行: ${ln}, 列: ${col}`;
  }
  ['keyup','click','select'].forEach(ev=>editor.addEventListener(ev,updateStatus));

  // ── Editor ───────────────────────────────────────────────────────
  function refresh() { updateLineNumbers(); updateStatus(); scheduleRender(); }
  editor.addEventListener('input', refresh);
  editor.addEventListener('keydown', e => {
    if (e.key==='Tab') { e.preventDefault(); const s=editor.selectionStart,end=editor.selectionEnd; editor.value=editor.value.substring(0,s)+'  '+editor.value.substring(end); editor.selectionStart=editor.selectionEnd=s+2; refresh(); }
    if (e.ctrlKey||e.metaKey) {
      if (e.key==='b'){e.preventDefault();insert('bold');}
      if (e.key==='i'){e.preventDefault();insert('italic');}
      if (e.key==='s'){e.preventDefault();saveFile();}
      if (e.key==='k'){e.preventDefault();insert('link');}
      if (e.key==='f'){e.preventDefault();openSearchPanel(); const sel=editor.value.substring(editor.selectionStart,editor.selectionEnd); if(sel&&sel.length<200)document.getElementById('sp-search').value=sel; spRunSearch();}
      if (e.key==='h'){e.preventDefault();openSearchPanel();document.getElementById('sp-replace').focus();}
    }
  });

  // ── Insert helpers ───────────────────────────────────────────────
  function wrapSelection(b,a,ph) {
    const s=editor.selectionStart,e=editor.selectionEnd,sel=editor.value.substring(s,e)||ph;
    editor.value=editor.value.substring(0,s)+b+sel+a+editor.value.substring(e);
    editor.selectionStart=s+b.length; editor.selectionEnd=s+b.length+sel.length;
    editor.focus(); refresh();
  }
  function insertLine(prefix) {
    const s=editor.selectionStart,val=editor.value,ls=val.lastIndexOf('\n',s-1)+1,le=val.indexOf('\n',s),line=val.substring(ls,le===-1?val.length:le);
    editor.value=val.substring(0,ls)+prefix+line+val.substring(le===-1?val.length:le);
    editor.selectionStart=editor.selectionEnd=ls+prefix.length+line.length;
    editor.focus(); refresh();
  }
  function insertBlock(text, co) {
    const s=editor.selectionStart,val=editor.value,pre=(s>0&&val[s-1]!=='\n')?'\n\n':(s>0&&val[s-2]!=='\n')?'\n':'',full=pre+text;
    editor.value=val.substring(0,s)+full+val.substring(s);
    editor.selectionStart=editor.selectionEnd=s+pre.length+(co!==undefined?co:text.length);
    editor.focus(); refresh();
  }
  window.insert = function(type) {
    switch(type) {
      case 'heading1': insertLine('# '); break;
      case 'heading2': insertLine('## '); break;
      case 'heading3': insertLine('### '); break;
      case 'bold': wrapSelection('**','**','テキスト'); break;
      case 'italic': wrapSelection('*','*','テキスト'); break;
      case 'strikethrough': wrapSelection('~~','~~','テキスト'); break;
      case 'inlinecode': wrapSelection('`','`','code'); break;
      case 'link': wrapSelection('[','](https://)','リンクテキスト'); break;
      case 'ul': insertLine('- '); break;
      case 'ol': insertLine('1. '); break;
      case 'blockquote': insertLine('> '); break;
      case 'hr': insertBlock('\n---\n'); break;
      case 'codeblock': insertBlock('```\nコードを入力\n```\n', 4); break;
      case 'mermaid': insertBlock('```mermaid\ngraph TD\n    A[Start] --> B[Process]\n    B --> C[End]\n```\n', 11); break;
      case 'table': insertBlock('| 列1 | 列2 | 列3 |\n|-----|-----|-----|\n| A   | B   | C   |\n| D   | E   | F   |\n', 2); break;
    }
  };

  // ── File ops ─────────────────────────────────────────────────────
  window.newFile = function() {
    if (editor.value&&!confirm('現在の内容を破棄して新規ファイルを作成しますか？')) return;
    editor.value=''; currentFilename='untitled.md'; filenameDisplay.textContent=currentFilename; refresh(); showToast('新規ファイルを作成しました');
  };
  window.openFile = function() { document.getElementById('file-input').click(); };
  document.getElementById('file-input').addEventListener('change', function(e) {
    const file=e.target.files[0]; if (!file) return;
    const r=new FileReader(); r.onload=ev=>{ editor.value=ev.target.result; currentFilename=file.name; filenameDisplay.textContent=currentFilename; refresh(); showToast(`"${file.name}" を開きました`); }; r.readAsText(file,'UTF-8'); this.value='';
  });
  window.saveFile = function() {
    const blob=new Blob([editor.value],{type:'text/markdown;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url; a.download=currentFilename; a.click(); URL.revokeObjectURL(url); showToast(`"${currentFilename}" を保存しました`);
  };

  // ── Toast ────────────────────────────────────────────────────────
  let toastTimer;
  window.showToast = function(msg) { const t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); clearTimeout(toastTimer); toastTimer=setTimeout(()=>t.classList.remove('show'),2200); };

  // ── Resizer ──────────────────────────────────────────────────────
  const resizer=document.getElementById('resizer'),panes=document.getElementById('panes'),editorPane=document.getElementById('editor-pane'),previewPane=document.getElementById('preview-pane');
  let dragging=false,startX,startFlex;
  resizer.addEventListener('mousedown',e=>{dragging=true;resizer.classList.add('dragging');startX=e.clientX;startFlex=editorPane.offsetWidth/panes.offsetWidth;document.body.style.userSelect='none';document.body.style.cursor='col-resize';});
  document.addEventListener('mousemove',e=>{if(!dragging)return;const f=Math.max(.2,Math.min(.8,startFlex+(e.clientX-startX)/panes.offsetWidth));editorPane.style.flex=`0 0 ${f*100}%`;previewPane.style.flex=`0 0 ${(1-f)*100}%`;});
  document.addEventListener('mouseup',()=>{if(!dragging)return;dragging=false;resizer.classList.remove('dragging');document.body.style.userSelect='';document.body.style.cursor='';});

  // ── Search & Replace ─────────────────────────────────────────────
  const spPanel=document.getElementById('search-panel'),spSearch=document.getElementById('sp-search'),spReplace=document.getElementById('sp-replace'),spCount=document.getElementById('sp-count');
  let spMatches=[],spCurrent=-1,spOpts={case:false,regex:false};
  function spBuildRegex(q){if(!q)return null;try{return new RegExp(spOpts.regex?q:q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),spOpts.case?'g':'gi');}catch(e){return null;}}
  function spRunSearch(){
    const q=spSearch.value; spSearch.classList.remove('sp-error'); spMatches=[]; spCurrent=-1;
    if(!q){spCount.textContent='';spCount.classList.remove('sp-no-match');spHighlight(-1);return;}
    if(spOpts.regex){try{new RegExp(q);}catch(e){spSearch.classList.add('sp-error');spCount.textContent='無効な正規表現';return;}}
    const rx=spBuildRegex(q); if(!rx)return;
    const text=editor.value; let m;
    while((m=rx.exec(text))!==null){spMatches.push({start:m.index,end:m.index+m[0].length});if(m[0].length===0)rx.lastIndex++;}
    if(spMatches.length===0){spCount.textContent='見つかりません';spCount.classList.add('sp-no-match');spHighlight(-1);}
    else{spCurrent=0;spCount.classList.remove('sp-no-match');spJumpTo(0);}
  }
  function spJumpTo(idx){
    if(!spMatches.length)return; spCurrent=(idx+spMatches.length)%spMatches.length;
    const m=spMatches[spCurrent]; editor.focus(); editor.setSelectionRange(m.start,m.end);
    const lineH=parseFloat(getComputedStyle(editor).lineHeight)||22,linesB=editor.value.substring(0,m.start).split('\n').length-1,wrap=document.getElementById('editor-wrap');
    wrap.scrollTop=Math.max(0,linesB*lineH-wrap.clientHeight/2);
    spCount.textContent=`${spCurrent+1} / ${spMatches.length}`; spHighlight(spCurrent);
  }
  function spHighlight(activeIdx){
    let canvas=document.getElementById('search-highlight-canvas'),wrap=document.getElementById('editor-wrap');
    if(activeIdx<0||!spMatches.length){if(canvas)canvas.remove();return;}
    if(!canvas){canvas=document.createElement('canvas');canvas.id='search-highlight-canvas';canvas.style.cssText='position:absolute;top:0;left:0;pointer-events:none;z-index:1;';wrap.appendChild(canvas);}
    canvas.width=wrap.scrollWidth;canvas.height=wrap.scrollHeight;canvas.style.width=canvas.width+'px';canvas.style.height=canvas.height+'px';
    const ctx=canvas.getContext('2d'),style=getComputedStyle(editor),lineH=parseFloat(style.lineHeight)||22,fontSize=parseFloat(style.fontSize)||13.5,pt=parseFloat(style.paddingTop)||14,pl=parseFloat(style.paddingLeft)||16+44;
    ctx.clearRect(0,0,canvas.width,canvas.height);ctx.font=`${fontSize}px ${style.fontFamily}`;
    const text=editor.value,lines=text.split('\n'),lineStarts=[];let off=0;for(const l of lines){lineStarts.push(off);off+=l.length+1;}
    for(let i=0;i<spMatches.length;i++){
      const {start,end}=spMatches[i],li=lineStarts.findLastIndex(s=>s<=start),bm=text.substring(lineStarts[li],start),mt=text.substring(start,end);
      const x=pl+ctx.measureText(bm).width,y=pt+li*lineH,w=ctx.measureText(mt).width;
      ctx.fillStyle=i===activeIdx?'rgba(192,96,58,0.35)':'rgba(192,96,58,0.15)';ctx.fillRect(x,y,Math.max(w,4),lineH-2);
    }
  }
  window.spToggle=function(key){spOpts[key]=!spOpts[key];document.getElementById('sp-btn-'+key).classList.toggle('active',spOpts[key]);spRunSearch();};
  window.spMove=function(dir){if(spMatches.length)spJumpTo(spCurrent+dir);};
  window.spReplaceOne=function(){
    if(!spMatches.length||spCurrent<0)return;const m=spMatches[spCurrent];let rep=spReplace.value;
    if(spOpts.regex){const rx=spBuildRegex(spSearch.value);if(rx){const src=editor.value.substring(m.start,m.end);rep=src.replace(new RegExp(rx.source,rx.flags.replace('g','')),rep);}}
    editor.value=editor.value.substring(0,m.start)+rep+editor.value.substring(m.end);refresh();spRunSearch();showToast('1件置換しました');
  };
  window.spReplaceAll=function(){if(!spMatches.length)return;const rx=spBuildRegex(spSearch.value);if(!rx)return;const count=spMatches.length;editor.value=editor.value.replace(rx,spReplace.value);refresh();spRunSearch();showToast(`${count}件をすべて置換しました`);};
  function openSearchPanel(){spPanel.classList.add('open');document.getElementById('search-tb-btn').classList.add('active');spSearch.focus();spSearch.select();if(spSearch.value)spRunSearch();}
  function closeSearchPanel(){spPanel.classList.remove('open');document.getElementById('search-tb-btn').classList.remove('active');spMatches=[];spCurrent=-1;spHighlight(-1);spCount.textContent='';editor.focus();}
  window.toggleSearchPanel=function(){spPanel.classList.contains('open')?closeSearchPanel():openSearchPanel();};
  window.openSearchPanel=openSearchPanel;window.closeSearchPanel=closeSearchPanel;
  spSearch.addEventListener('input',spRunSearch);
  spSearch.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();spMove(e.shiftKey?-1:1);}if(e.key==='Escape')closeSearchPanel();if(e.altKey&&e.key==='c'){e.preventDefault();window.spToggle('case');}if(e.altKey&&e.key==='r'){e.preventDefault();window.spToggle('regex');}});
  spReplace.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();window.spReplaceOne();}if(e.key==='Escape')closeSearchPanel();});
  editor.addEventListener('input',()=>{if(spPanel.classList.contains('open'))spRunSearch();});
  document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='f'){e.preventDefault();openSearchPanel();const sel=editor.value.substring(editor.selectionStart,editor.selectionEnd);if(sel&&sel.length<200)spSearch.value=sel;spRunSearch();}});

  // ── Initial content ──────────────────────────────────────────────
  editor.value = `# Markdown Editor へようこそ 🎉

このエディタは **外部通信ゼロ** のスタンドアロン版です。

## 特徴

- リアルタイムプレビュー
- Mermaid ダイアグラムレンダリング
- シンタックスハイライト
- 検索・置換（Ctrl+F）
- ファイル保存・読み込み
- スタンドアロン（外部通信なし）

## Mermaid ダイアグラム

\`\`\`mermaid
graph TD
    A[📝 Markdown 入力] --> B{パース}
    B --> C[テキスト/コード]
    B --> D[Mermaid ブロック]
    C --> E[🖥️ プレビュー表示]
    D --> F[📊 ダイアグラム描画]
    F --> E
\`\`\`

## コード例

\`\`\`javascript
function greet(name) {
  return \`Hello, \${name}!\`;
}
console.log(greet("World"));
\`\`\`

---

> **Tip:** \`Ctrl+S\` で保存、\`Ctrl+F\` で検索、図にホバーでコピーボタン表示。
`;
  updateLineNumbers(); updateStatus(); renderPreview();
})();
</script>
</body>
</html>"""

    # ── プレースホルダを埋め込む ────────────────────────────────────
    print("\n🔧 スタンドアロン HTML を生成中...")
    html = APP_HTML
    for lib in LIBS:
        tag = lib["tag"]
        html = html.replace(f"%%{tag}%%", downloaded[tag])

    # ── 出力 ────────────────────────────────────────────────────────
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "standalone_SimpleMarkdownEditor.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"\n{'='*56}")
    print(f"  ✅ 完成: standalone_SimpleMarkdownEditor.html  ({size_mb:.1f} MB)")
    print(f"{'='*56}")
    print(f"\n  このファイル1つをどのPCにコピーしても")
    print(f"  インターネット不要で完全動作します。\n")

if __name__ == "__main__":
    try:
        build()
    except RuntimeError as e:
        print(f"\n{e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n中断されました。\n")
        sys.exit(1)
