"""Tests for envault.lint."""

from pathlib import Path

import pytest

from envault.lint import LintError, LintIssue, LintResult, lint_file


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(content, encoding="utf-8")
    return p


def test_lint_raises_when_file_missing(tmp_path):
    with pytest.raises(LintError, match="not found"):
        lint_file(tmp_path / "missing.env")


def test_lint_clean_file_returns_ok(tmp_path):
    p = _write(tmp_path, "DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\n")
    result = lint_file(p)
    assert result.ok
    assert result.error_count == 0
    assert result.warning_count == 0


def test_lint_skips_comments_and_blanks(tmp_path):
    p = _write(tmp_path, "# comment\n\nFOO=bar\n")
    result = lint_file(p)
    assert result.ok
    assert not result.issues


def test_lint_detects_invalid_line(tmp_path):
    p = _write(tmp_path, "NOTAVALIDLINE\n")
    result = lint_file(p)
    assert not result.ok
    assert result.error_count == 1
    assert "not a valid" in result.issues[0].message.lower()


def test_lint_detects_duplicate_key(tmp_path):
    p = _write(tmp_path, "FOO=bar\nFOO=baz\n")
    result = lint_file(p)
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("Duplicate" in e.message for e in errors)


def test_lint_warns_on_lowercase_key(tmp_path):
    p = _write(tmp_path, "foo=bar\n")
    result = lint_file(p)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert warnings
    assert "lowercase" in warnings[0].message or "invalid" in warnings[0].message


def test_lint_warns_on_empty_value(tmp_path):
    p = _write(tmp_path, "EMPTY_VAR=\n")
    result = lint_file(p)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("empty" in w.message.lower() for w in warnings)


def test_lint_result_counts(tmp_path):
    p = _write(tmp_path, "foo=bar\nFOO=\nFOO=dup\n")
    result = lint_file(p)
    assert result.warning_count >= 1
    assert result.error_count >= 1
    assert not result.ok


def test_lint_result_path(tmp_path):
    p = _write(tmp_path, "KEY=value\n")
    result = lint_file(p)
    assert result.path == p
