"""Tests for envault.cli_lint."""

import argparse
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.cli_lint import _cmd_lint, build_parser
from envault.lint import LintError, LintResult, LintIssue


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"env_file": ".env"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_default_env_file():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.env_file == ".env"


def test_cmd_lint_exits_on_lint_error(capsys):
    with patch("envault.cli_lint.lint_file", side_effect=LintError("not found")):
        with pytest.raises(SystemExit) as exc:
            _cmd_lint(_ns(env_file="missing.env"))
    assert exc.value.code == 1


def test_cmd_lint_prints_ok_when_no_issues(capsys):
    clean = LintResult(path=Path(".env"))
    with patch("envault.cli_lint.lint_file", return_value=clean):
        _cmd_lint(_ns())
    out = capsys.readouterr().out
    assert "no issues" in out


def test_cmd_lint_exits_2_on_errors(capsys):
    result = LintResult(
        path=Path(".env"),
        issues=[LintIssue(1, "bad line", "error")],
    )
    with patch("envault.cli_lint.lint_file", return_value=result):
        with pytest.raises(SystemExit) as exc:
            _cmd_lint(_ns())
    assert exc.value.code == 2


def test_cmd_lint_no_exit_on_warnings_only(capsys):
    result = LintResult(
        path=Path(".env"),
        issues=[LintIssue(1, "empty value", "warning")],
    )
    with patch("envault.cli_lint.lint_file", return_value=result):
        _cmd_lint(_ns())  # should not raise
    out = capsys.readouterr().out
    assert "warning" in out


def test_cmd_lint_prints_issue_details(capsys):
    result = LintResult(
        path=Path(".env"),
        issues=[LintIssue(3, "Duplicate key 'FOO'", "error")],
    )
    with patch("envault.cli_lint.lint_file", return_value=result):
        with pytest.raises(SystemExit):
            _cmd_lint(_ns())
    out = capsys.readouterr().out
    assert "line 3" in out
    assert "Duplicate" in out
