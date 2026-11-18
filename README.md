# clip-md

A smart, zero-dependency macOS clipboard CLI utility (`pbpaste`/`pbcopy`, with `--stdin` / `--stdout` support for Linux & CI) for wrapping code in Markdown fences, pretty-printing JSON, and stripping URL tracking parameters.

## Features

- **`clip-md code`** — Wraps clipboard text in a fenced Markdown code block with automatic language detection (Python, JavaScript/TypeScript, JSON, SQL, Bash, HTML).
- **`clip-md json`** — Pretty-prints minified or messy JSON.
- **`clip-md clean-url`** — Strips common tracking query parameters (`utm_*`, `fbclid`, `gclid`, `si`, `ref`, etc.) from URLs.
- **Clipboard-first, pipe-friendly** — Reads from `pbpaste` and writes back to `pbcopy` by default; pass `--stdin` and/or `--stdout` for piping or Linux/CI usage.

## Installation

Using [`uv`](https://docs.astral.sh/uv/):

```bash
uv tool install .
```

Or run directly without installing:

```bash
uv run clip-md --help
```

## Usage

```bash
# Wrap clipboard code in a Markdown code block and copy it back
clip-md code

# Pretty-print JSON from stdin and print to stdout
echo '{"b":1,"a":[2,3]}' | clip-md json --stdin --stdout

# Strip tracking params from a URL
echo 'https://example.com/post?id=42&utm_source=twitter&fbclid=abc123' | clip-md clean-url --stdin --stdout
# -> https://example.com/post?id=42
```

## License

MIT
