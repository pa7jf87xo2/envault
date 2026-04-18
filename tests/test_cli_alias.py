"""Tests for envault.cli_alias."""
from __future__ import annotations

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch

from envault.cli_alias import (
    _cmd_alias_list,
    _cmd_alias_set,
    _cmd_alias_remove,
    _cmd_alias_resolve,
    build_parser,
)
from envault.alias import AliasError


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"vault": ".envault", "name": "prod", "target": "/envs/prod.vault"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_parser_has_subcommands():
    p = build_parser()
    assert p._subparsers is not None


def test_cmd_alias_list_prints_aliases(capsys):
    with patch("envault.cli_alias.load_aliases", return_value={"prod": "/envs/prod.vault"}):
        _cmd_alias_list(_ns())
    out = capsys.readouterr().out
    assert "prod" in out
    assert "/envs/prod.vault" in out


def test_cmd_alias_list_empty(capsys):
    with patch("envault.cli_alias.load_aliases", return_value={}):
        _cmd_alias_list(_ns())
    assert "no aliases" in capsys.readouterr().out


def test_cmd_alias_list_exits_on_error():
    with patch("envault.cli_alias.load_aliases", side_effect=AliasError("boom")):
        with pytest.raises(SystemExit) as exc:
            _cmd_alias_list(_ns())
    assert exc.value.code == 1


def test_cmd_alias_set_prints_confirmation(capsys):
    with patch("envault.cli_alias.set_alias", return_value={"prod": "/envs/prod.vault"}):
        _cmd_alias_set(_ns())
    assert "prod" in capsys.readouterr().out


def test_cmd_alias_set_exits_on_error():
    with patch("envault.cli_alias.set_alias", side_effect=AliasError("bad")):
        with pytest.raises(SystemExit) as exc:
            _cmd_alias_set(_ns())
    assert exc.value.code == 1


def test_cmd_alias_remove_prints_confirmation(capsys):
    with patch("envault.cli_alias.remove_alias", return_value={}):
        _cmd_alias_remove(_ns())
    assert "removed" in capsys.readouterr().out


def test_cmd_alias_remove_exits_on_error():
    with patch("envault.cli_alias.remove_alias", side_effect=AliasError("nope")):
        with pytest.raises(SystemExit) as exc:
            _cmd_alias_remove(_ns())
    assert exc.value.code == 1


def test_cmd_alias_resolve_prints_target(capsys):
    with patch("envault.cli_alias.resolve_alias", return_value="/envs/prod.vault"):
        _cmd_alias_resolve(_ns())
    assert "/envs/prod.vault" in capsys.readouterr().out


def test_cmd_alias_resolve_exits_on_error():
    with patch("envault.cli_alias.resolve_alias", side_effect=AliasError("gone")):
        with pytest.raises(SystemExit) as exc:
            _cmd_alias_resolve(_ns())
    assert exc.value.code == 1
