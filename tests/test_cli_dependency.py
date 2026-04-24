"""Tests for envault.cli_dependency."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_dependency import (
    _cmd_dependency_add,
    _cmd_dependency_clear,
    _cmd_dependency_list,
    _cmd_dependency_remove,
    build_parser,
)
from envault.dependency import DependencyError


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"vault": ".env.vault", "dep": "other.vault"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser() -> None:
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_parser_has_subcommands() -> None:
    p = build_parser()
    ns = p.parse_args(["list"])
    assert ns.dep_cmd == "list"


def test_cmd_dependency_list_prints_deps(capsys) -> None:
    with patch("envault.cli_dependency.load_dependencies", return_value=["a.vault", "b.vault"]):
        _cmd_dependency_list(_ns())
    out = capsys.readouterr().out
    assert "a.vault" in out
    assert "b.vault" in out


def test_cmd_dependency_list_empty(capsys) -> None:
    with patch("envault.cli_dependency.load_dependencies", return_value=[]):
        _cmd_dependency_list(_ns())
    assert "No dependencies" in capsys.readouterr().out


def test_cmd_dependency_list_exits_on_error(capsys) -> None:
    with patch("envault.cli_dependency.load_dependencies", side_effect=DependencyError("boom")):
        with pytest.raises(SystemExit) as exc:
            _cmd_dependency_list(_ns())
    assert exc.value.code == 1
    assert "boom" in capsys.readouterr().err


def test_cmd_dependency_add_prints_confirmation(capsys) -> None:
    with patch("envault.cli_dependency.add_dependency", return_value=["other.vault"]):
        _cmd_dependency_add(_ns())
    assert "Added" in capsys.readouterr().out


def test_cmd_dependency_add_exits_on_error(capsys) -> None:
    with patch("envault.cli_dependency.add_dependency", side_effect=DependencyError("bad")):
        with pytest.raises(SystemExit) as exc:
            _cmd_dependency_add(_ns())
    assert exc.value.code == 1


def test_cmd_dependency_remove_prints_confirmation(capsys) -> None:
    with patch("envault.cli_dependency.remove_dependency", return_value=[]):
        _cmd_dependency_remove(_ns())
    assert "Removed" in capsys.readouterr().out


def test_cmd_dependency_remove_exits_on_error(capsys) -> None:
    with patch("envault.cli_dependency.remove_dependency", side_effect=DependencyError("nope")):
        with pytest.raises(SystemExit) as exc:
            _cmd_dependency_remove(_ns())
    assert exc.value.code == 1


def test_cmd_dependency_clear_prints_confirmation(capsys) -> None:
    with patch("envault.cli_dependency.clear_dependencies"):
        _cmd_dependency_clear(_ns())
    assert "cleared" in capsys.readouterr().out


def test_cmd_dependency_clear_exits_on_error(capsys) -> None:
    with patch("envault.cli_dependency.clear_dependencies", side_effect=DependencyError("err")):
        with pytest.raises(SystemExit) as exc:
            _cmd_dependency_clear(_ns())
    assert exc.value.code == 1
