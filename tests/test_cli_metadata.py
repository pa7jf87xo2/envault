"""Tests for envault.cli_metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_metadata import (
    _cmd_metadata_clear,
    _cmd_metadata_list,
    _cmd_metadata_remove,
    _cmd_metadata_set,
    build_parser,
)
from envault.metadata import MetadataError


def _ns(**kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "x.vault"
    v.write_bytes(b"x")
    return v


def test_build_parser_returns_parser() -> None:
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_parser_has_subcommands() -> None:
    p = build_parser()
    # parsing without args should raise SystemExit (required subcommand)
    with pytest.raises(SystemExit):
        p.parse_args([])


def test_cmd_metadata_list_empty(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    v = _make_vault(tmp_path)
    _cmd_metadata_list(_ns(vault=str(v)))
    out = capsys.readouterr().out
    assert "no metadata" in out


def test_cmd_metadata_list_shows_keys(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    from envault.metadata import set_metadata
    v = _make_vault(tmp_path)
    set_metadata(v, "env", "prod")
    _cmd_metadata_list(_ns(vault=str(v)))
    out = capsys.readouterr().out
    assert "env" in out
    assert "prod" in out


def test_cmd_metadata_list_exits_on_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        _cmd_metadata_list(_ns(vault=str(tmp_path / "ghost.vault")))


def test_cmd_metadata_set_prints_confirmation(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    v = _make_vault(tmp_path)
    _cmd_metadata_set(_ns(vault=str(v), key="team", value="backend"))
    out = capsys.readouterr().out
    assert "team" in out


def test_cmd_metadata_set_parses_json_value(tmp_path: Path) -> None:
    from envault.metadata import load_metadata
    v = _make_vault(tmp_path)
    _cmd_metadata_set(_ns(vault=str(v), key="count", value="42"))
    assert load_metadata(v)["count"] == 42


def test_cmd_metadata_set_falls_back_to_string(tmp_path: Path) -> None:
    from envault.metadata import load_metadata
    v = _make_vault(tmp_path)
    _cmd_metadata_set(_ns(vault=str(v), key="label", value="hello world"))
    assert load_metadata(v)["label"] == "hello world"


def test_cmd_metadata_set_exits_on_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        _cmd_metadata_set(_ns(vault=str(tmp_path / "ghost.vault"), key="k", value="v"))


def test_cmd_metadata_remove_prints_confirmation(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    from envault.metadata import set_metadata
    v = _make_vault(tmp_path)
    set_metadata(v, "x", 1)
    _cmd_metadata_remove(_ns(vault=str(v), key="x"))
    out = capsys.readouterr().out
    assert "removed" in out


def test_cmd_metadata_remove_exits_on_error(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    with pytest.raises(SystemExit):
        _cmd_metadata_remove(_ns(vault=str(v), key="missing"))


def test_cmd_metadata_clear_prints_confirmation(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    v = _make_vault(tmp_path)
    _cmd_metadata_clear(_ns(vault=str(v)))
    out = capsys.readouterr().out
    assert "cleared" in out


def test_cmd_metadata_clear_exits_on_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        _cmd_metadata_clear(_ns(vault=str(tmp_path / "ghost.vault")))
