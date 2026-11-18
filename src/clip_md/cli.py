"""CLI for clip-md: smart clipboard formatting for code, JSON, and URLs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from . import __version__

TRACKING_PARAMS = frozenset(
    {
        "fbclid",
        "gclid",
        "dclid",
        "gbraid",
        "wbraid",
        "msclkid",
        "twclid",
        "yclid",
        "mc_cid",
        "mc_eid",
        "si",
        "ref",
        "ref_src",
        "ref_url",
        "igshid",
        "s",
        "t",
        "feature",
        "spm",
        "mkt_tok",
        "_hsenc",
        "_hsmi",
        "hsctatracking",
        "vero_id",
        "oly_anon_id",
        "oly_enc_id",
    }
)

URL_RE = re.compile(r"https?://[^\s<>\"'()]+")


def read_input(use_stdin: bool) -> str:
    """Read text from stdin or macOS clipboard via pbpaste."""
    if use_stdin:
        return sys.stdin.read()

    if not shutil.which("pbpaste"):
        raise RuntimeError(
            "'pbpaste' not found. Use --stdin on Linux/CI or non-macOS environments."
        )

    proc = subprocess.run(["pbpaste"], capture_output=True, text=True, check=True)
    return proc.stdout


def write_output(text: str, use_stdout: bool) -> None:
    """Write text to stdout or macOS clipboard via pbcopy."""
    if use_stdout:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return

    if not shutil.which("pbcopy"):
        raise RuntimeError(
            "'pbcopy' not found. Use --stdout on Linux/CI or non-macOS environments."
        )

    subprocess.run(["pbcopy"], input=text, text=True, check=True)


def detect_language(text: str) -> str:
    """Heuristically detect the programming language of a code snippet."""
    stripped = text.strip()
    if not stripped:
        return ""

    # 1. JSON
    if (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    ):
        try:
            json.loads(stripped)
            return "json"
        except ValueError:
            pass

    # 2. Shebang
    first_line = stripped.splitlines()[0].strip()
    if first_line.startswith("#!"):
        lower_first = first_line.lower()
        if "python" in lower_first:
            return "python"
        if any(sh in lower_first for sh in ("bash", "zsh", "/sh")):
            return "bash"
        if "node" in lower_first:
            return "javascript"

    # 3. HTML / XML
    if re.search(r"<!DOCTYPE\s+html|<html\b|<div\b|<span\b|<script\b|</[a-zA-Z]+>", stripped, re.I):
        return "html"

    # 4. SQL
    if re.match(
        r"^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH)\b",
        stripped,
        re.IGNORECASE,
    ) and re.search(r"\b(FROM|INTO|TABLE|SET|WHERE|VALUES|JOIN)\b", stripped, re.IGNORECASE):
        return "sql"

    # 5. TypeScript vs JavaScript
    ts_signals = (
        re.search(r"\b(interface|type)\s+[A-Z]\w*\s*[={]", stripped),
        re.search(r":\s*(string|number|boolean|any|unknown|void|never)\b", stripped),
        re.search(r"\bas\s+(const|[A-Z]\w*)\b", stripped),
    )
    js_signals = (
        re.search(r"\b(const|let|var)\s+\w+\s*=", stripped),
        re.search(r"\bfunction\s+\w*\s*\(", stripped),
        re.search(r"=>\s*[{(]", stripped),
        re.search(r"\b(console\.log|export\s+default|import\s+.*from\s+['\"])", stripped),
    )
    if any(ts_signals):
        return "typescript"
    if any(js_signals):
        return "javascript"

    # 6. Python
    py_signals = (
        re.search(r"^\s*def\s+\w+\s*\(", stripped, re.MULTILINE),
        re.search(r"^\s*class\s+\w+(\s*\([^)]*\))?:", stripped, re.MULTILINE),
        re.search(r"^\s*(from\s+\S+\s+import|import\s+\w+)", stripped, re.MULTILINE),
        re.search(r"\bif\s+__name__\s*==\s*['\"]__main__['\"]", stripped),
    )
    if any(py_signals):
        return "python"

    # 7. Bash / Shell
    bash_signals = (
        re.search(r"^\s*(export|echo|curl|grep|awk|sed|chmod|mkdir|cd|git|uv|npm|pip)\s+", stripped, re.MULTILINE),
        re.search(r"\$\(\s*[^)]+\s*\)|\$\{\w+\}", stripped),
        re.search(r"\|\s*(grep|awk|sed|jq|xargs|sort|head|tail)\b", stripped),
    )
    if any(bash_signals):
        return "bash"

    return ""


def format_code(text: str, lang: str | None = None) -> str:
    """Wrap *text* in a fenced Markdown code block."""
    detected = lang if lang is not None else detect_language(text)
    body = text.rstrip("\n")
    fence = "````" if "```" in body else "```"
    return f"{fence}{detected}\n{body}\n{fence}"


def format_json(text: str, indent: int = 2, sort_keys: bool = False) -> str:
    """Parse and pretty-print JSON text."""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"Invalid JSON: {err}") from err
    return json.dumps(parsed, indent=indent, ensure_ascii=False, sort_keys=sort_keys)


def _clean_single_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url

    kept = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS
    ]
    new_query = urlencode(kept, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def clean_urls(text: str) -> str:
    """Strip tracking query parameters from all URLs found in *text*."""
    return URL_RE.sub(lambda m: _clean_single_url(m.group(0)), text.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clip-md",
        description="Smart clipboard utility for Markdown code blocks, JSON formatting, and clean URLs.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--stdin",
        action="store_true",
        help="Read input from stdin instead of the macOS clipboard (pbpaste).",
    )
    common.add_argument(
        "--stdout",
        action="store_true",
        help="Write output to stdout instead of the macOS clipboard (pbcopy).",
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    code_p = subparsers.add_parser(
        "code",
        parents=[common],
        help="Wrap clipboard text in a fenced Markdown code block with auto-detected language.",
    )
    code_p.add_argument(
        "-l",
        "--lang",
        default=None,
        help="Override auto-detected language (e.g. python, ts, bash).",
    )

    json_p = subparsers.add_parser(
        "json",
        parents=[common],
        help="Pretty-print messy JSON from clipboard.",
    )
    json_p.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation spaces (default: 2).",
    )
    json_p.add_argument(
        "--sort-keys",
        action="store_true",
        help="Sort JSON object keys alphabetically.",
    )

    subparsers.add_parser(
        "clean-url",
        parents=[common],
        help="Strip tracking query parameters (utm_*, fbclid, gclid, si, ref, etc.) from URLs.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        raw = read_input(use_stdin=args.stdin)
        if args.mode == "code":
            result = format_code(raw, lang=args.lang)
        elif args.mode == "json":
            result = format_json(raw, indent=args.indent, sort_keys=args.sort_keys)
        elif args.mode == "clean-url":
            result = clean_urls(raw)
        else:
            parser.error(f"Unknown mode: {args.mode}")
            return 2

        write_output(result, use_stdout=args.stdout)
    except (RuntimeError, ValueError, subprocess.CalledProcessError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
