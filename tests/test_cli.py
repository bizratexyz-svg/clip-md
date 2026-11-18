"""Unit tests for clip-md CLI and formatting/cleaning logic."""

from __future__ import annotations

import io
import json

import pytest

from clip_md.cli import (
    clean_urls,
    detect_language,
    format_code,
    format_json,
    main,
)


class TestDetectLanguage:
    @pytest.mark.parametrize(
        ("snippet", "expected"),
        [
            ('{"a": 1, "b": [2, 3]}', "json"),
            ("[1, 2, 3]", "json"),
            ("#!/usr/bin/env python3\nprint('hi')", "python"),
            ("#!/bin/bash\necho hello", "bash"),
            ("#!/usr/bin/env node\nconsole.log(1)", "javascript"),
            ("<div class='card'><span>Hello</span></div>", "html"),
            ("SELECT id, name FROM users WHERE active = 1;", "sql"),
            ("interface User { id: number; name: string; }", "typescript"),
            ("const greet = (name) => { console.log(name); };", "javascript"),
            ("def add(a, b):\n    return a + b", "python"),
            ("curl -s https://example.com | jq '.items'", "bash"),
            ("just some plain notes without code", ""),
            ("   ", ""),
        ],
    )
    def test_detect_language(self, snippet: str, expected: str) -> None:
        assert detect_language(snippet) == expected


class TestFormatCode:
    def test_auto_detects_language(self) -> None:
        result = format_code("def hello():\n    return 'world'\n")
        assert result == "```python\ndef hello():\n    return 'world'\n```"

    def test_explicit_lang_override(self) -> None:
        result = format_code("x = 1", lang="ruby")
        assert result == "```ruby\nx = 1\n```"

    def test_nested_triple_backticks_use_four_backticks(self) -> None:
        snippet = "```bash\necho hi\n```"
        result = format_code(snippet, lang="markdown")
        assert result.startswith("````markdown\n")
        assert result.endswith("\n````")


class TestFormatJson:
    def test_pretty_prints_and_preserves_unicode(self) -> None:
        raw = '{"b":1,"a":"こんにちは"}'
        formatted = format_json(raw, indent=2, sort_keys=True)
        assert formatted == '{\n  "a": "こんにちは",\n  "b": 1\n}'
        assert json.loads(formatted) == {"a": "こんにちは", "b": 1}

    def test_invalid_json_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid JSON"):
            format_json("{not valid json")


class TestCleanUrls:
    def test_strips_tracking_params_and_preserves_meaningful_ones(self) -> None:
        url = (
            "https://example.com/post?id=42&utm_source=twitter&utm_medium=social"
            "&fbclid=abc123&gclid=xyz&si=track&ref=homepage#comments"
        )
        assert clean_urls(url) == "https://example.com/post?id=42#comments"

    def test_url_without_query_unchanged(self) -> None:
        url = "https://example.com/docs/getting-started"
        assert clean_urls(url) == url

    def test_cleans_multiple_urls_in_text(self) -> None:
        text = (
            "Check https://a.example/x?utm_campaign=launch&page=2 "
            "and https://b.example/y?fbclid=999"
        )
        assert clean_urls(text) == "Check https://a.example/x?page=2 and https://b.example/y"


class TestCLI:
    def test_cli_code_stdin_stdout(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO("SELECT * FROM events WHERE id = 1;"))
        rc = main(["code", "--stdin", "--stdout"])
        assert rc == 0
        out = capsys.readouterr().out
        assert out == "```sql\nSELECT * FROM events WHERE id = 1;\n```\n"

    def test_cli_json_stdin_stdout(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO('{"b":1,"a":2}'))
        rc = main(["json", "--stdin", "--stdout", "--sort-keys"])
        assert rc == 0
        out = capsys.readouterr().out
        assert out == '{\n  "a": 2,\n  "b": 1\n}\n'

    def test_cli_clean_url_stdin_stdout(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO("https://example.com/watch?v=123&si=share_id&utm_source=x"),
        )
        rc = main(["clean-url", "--stdin", "--stdout"])
        assert rc == 0
        assert capsys.readouterr().out == "https://example.com/watch?v=123\n"

    def test_cli_invalid_json_returns_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO("{broken"))
        rc = main(["json", "--stdin", "--stdout"])
        assert rc == 1
        assert "Error: Invalid JSON" in capsys.readouterr().err
