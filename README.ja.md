# clip-md

[English](README.md) | **日本語**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

コードの Markdown コードブロック化、JSON の整形、URL トラッキングパラメータの除去を行う、外部依存ゼロのスマートな macOS クリップボード CLI ユーティリティです（`pbpaste`/`pbcopy` 対応、Linux や CI 向けに `--stdin` / `--stdout` もサポート）。

## 主な機能

- **`clip-md code`** — クリップボードのテキストを言語自動判定（Python, JavaScript/TypeScript, JSON, SQL, Bash, HTML）付きで Markdown のコードブロックで囲みます。
- **`clip-md json`** — 圧縮されたり崩れたりした JSON を見やすく整形（Pretty-print）します。
- **`clip-md clean-url`** — URL から一般的なトラッキング用クエリパラメータ（`utm_*`, `fbclid`, `gclid`, `si`, `ref` など）を除去します。
- **クリップボード優先・パイプ対応** — デフォルトでは `pbpaste` から読み込み `pbcopy` に書き戻します。パイプ処理や Linux/CI 環境では `--stdin` や `--stdout` を指定できます。

## インストール

[`uv`](https://docs.astral.sh/uv/) を使用する場合:

```bash
uv tool install .
```

インストールせずに直接実行する場合:

```bash
uv run clip-md --help
```

## 使い方

```bash
# クリップボードのコードを Markdown コードブロックで囲んで書き戻す
clip-md code

# 標準入力から JSON を整形して標準出力に表示
echo '{"b":1,"a":[2,3]}' | clip-md json --stdin --stdout

# URL からトラッキングパラメータを除去
echo 'https://example.com/post?id=42&utm_source=twitter&fbclid=abc123' | clip-md clean-url --stdin --stdout
# -> https://example.com/post?id=42
```

## 出力例

```bash
$ printf 'def greet(name: str) -> str:\n    return f"Hello, {name}!"\n' | clip-md code --stdin --stdout
```

````markdown
```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```
````

```bash
$ echo '{"b":1,"a":[2,3]}' | clip-md json --stdin --stdout --sort-keys
{
  "a": [
    2,
    3
  ],
  "b": 1
}

$ echo 'https://example.com/post?id=42&utm_source=twitter&fbclid=abc123' | clip-md clean-url --stdin --stdout
https://example.com/post?id=42
```

## ライセンス

MIT
