# アンカーリンク動作確認

このページのリンクをクリックして、対応するセクションへ移動することを確認します。

## 目次

- [セクション 1: はじめに](#セクション-1-はじめに)
- [セクション 2: 詳細説明](#セクション-2-詳細説明)
- [セクション 3: コード例](#セクション-3-コード例)
- [セクション 4: テーブル](#セクション-4-テーブル)
- [セクション 5: まとめ](#セクション-5-まとめ)
- [先頭へ戻る](#アンカーリンク動作確認)

---

## セクション 1: はじめに

ここはセクション 1 です。上の目次から「セクション 1: はじめに」をクリックするとここへ飛びます。

[▲ 先頭へ](#アンカーリンク動作確認)

---

## セクション 2: 詳細説明

ここはセクション 2 です。長いコンテンツの間にある見出しへのジャンプを確認します。

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

[▲ 先頭へ](#アンカーリンク動作確認)

---

## セクション 3: コード例

ここはセクション 3 です。コードブロックを含むセクションへのジャンプを確認します。

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

for i in range(5):
    print(greet(f"User {i}"))
```

```javascript
function scrollToAnchor(id) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
}
```

[▲ 先頭へ](#アンカーリンク動作確認)

---

## セクション 4: テーブル

ここはセクション 4 です。テーブルを含むセクションへのジャンプを確認します。

| リンク先         | 期待動作                   |
| ---------------- | -------------------------- |
| セクション 1     | 「はじめに」へスクロール   |
| セクション 2     | 「詳細説明」へスクロール   |
| セクション 3     | 「コード例」へスクロール   |
| セクション 4     | 「テーブル」へスクロール   |
| セクション 5     | 「まとめ」へスクロール     |
| 先頭             | ページ最上部へスクロール   |

[▲ 先頭へ](#アンカーリンク動作確認)

---

## セクション 5: まとめ

ここはセクション 5（最下部）です。ページの一番下からでも目次リンクが機能することを確認します。

すべてのリンクが正しく動作すれば、アンカーリンク機能は正常に実装されています。

### 各セクションへの直接リンク

- [セクション 1 へ](#セクション-1-はじめに)
- [セクション 2 へ](#セクション-2-詳細説明)
- [セクション 3 へ](#セクション-3-コード例)
- [セクション 4 へ](#セクション-4-テーブル)
- [▲ 先頭へ戻る](#アンカーリンク動作確認)
