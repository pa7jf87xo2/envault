"""Tests for envault.redact."""

import pytest

from envault.redact import redact_line, redact_lines, redact_text, _is_sensitive


def test_is_sensitive_matches_password():
    assert _is_sensitive("DB_PASSWORD")


def test_is_sensitive_matches_token():
    assert _is_sensitive("GITHUB_TOKEN")


def test_is_sensitive_ignores_plain_key():
    assert not _is_sensitive("APP_NAME")


def test_redact_line_masks_sensitive_value():
    result = redact_line("API_KEY=supersecret\n")
    assert result == "API_KEY=***\n"


def test_redact_line_leaves_non_sensitive_unchanged():
    line = "APP_ENV=production\n"
    assert redact_line(line) == line


def test_redact_line_leaves_comment_unchanged():
    line = "# this is a comment\n"
    assert redact_line(line) == line


def test_redact_line_leaves_blank_unchanged():
    assert redact_line("\n") == "\n"


def test_redact_line_leaves_no_equals_unchanged():
    line = "JUST_A_WORD\n"
    assert redact_line(line) == line


def test_redact_line_show_partial():
    result = redact_line("SECRET_KEY=abcdefgh\n", show_partial=True)
    assert result == "SECRET_KEY=ab***gh\n"


def test_redact_line_show_partial_short_value():
    result = redact_line("SECRET_KEY=ab\n", show_partial=True)
    assert result == "SECRET_KEY=***\n"


def test_redact_lines_processes_multiple():
    lines = ["API_KEY=secret\n", "APP_NAME=myapp\n", "DB_PASSWORD=pass\n"]
    result = redact_lines(lines)
    assert result[0] == "API_KEY=***\n"
    assert result[1] == "APP_NAME=myapp\n"
    assert result[2] == "DB_PASSWORD=***\n"


def test_redact_text_full():
    text = "APP_ENV=prod\nAUTH_TOKEN=tok123\n"
    result = redact_text(text)
    assert "tok123" not in result
    assert "prod" in result


def test_redact_text_empty():
    assert redact_text("") == ""
