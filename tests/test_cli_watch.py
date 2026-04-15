"""Tests for envault.cli_watch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.cli_watch import build_parser, _cmd_watch


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(
        env_file=".env",
        vault=None,
        public_key=None,
        interval=1.0,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_parser_default_interval():
    p = build_parser()
    ns = p.parse_args([".env"])
    assert ns.interval == 1.0


def test_build_parser_custom_interval():
    p = build_parser()
    ns = p.parse_args([".env", "--interval", "5"])
    assert ns.interval == 5.0


def test_cmd_watch_uses_public_key_from_flag(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("K=V\n")
    ns = _ns(env_file=str(env_file), public_key="age1explicit")

    with patch("envault.cli_watch.watch") as mock_watch:
        mock_watch.side_effect = KeyboardInterrupt
        _cmd_watch(ns)

    mock_watch.assert_called_once()
    _, _, key = mock_watch.call_args.args
    assert key == "age1explicit"


def test_cmd_watch_defaults_vault_path(tmp_path):
    env_file = tmp_path / "app.env"
    env_file.write_text("K=V\n")
    ns = _ns(env_file=str(env_file), public_key="age1key")

    captured_vault: list[Path] = []

    def fake_watch(ef, vf, key, **kw):
        captured_vault.append(vf)
        raise KeyboardInterrupt

    with patch("envault.cli_watch.watch", side_effect=fake_watch):
        _cmd_watch(ns)

    assert captured_vault[0] == env_file.with_suffix(".vault")


def test_cmd_watch_exits_on_watch_error(tmp_path, capsys):
    from envault.watch import WatchError
    env_file = tmp_path / ".env"
    env_file.write_text("K=V\n")
    ns = _ns(env_file=str(env_file), public_key="age1key")

    with patch("envault.cli_watch.watch", side_effect=WatchError("bad")), \
         pytest.raises(SystemExit) as exc_info:
        _cmd_watch(ns)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "bad" in captured.err


def test_cmd_watch_loads_key_from_identity_when_no_flag(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("K=V\n")
    ns = _ns(env_file=str(env_file), public_key=None)

    with patch("envault.cli_watch.load_config", side_effect=Exception), \
         patch("envault.cli_watch.load_public_key", return_value="age1fromidentity") as mock_lpk, \
         patch("envault.cli_watch.watch", side_effect=KeyboardInterrupt):
        _cmd_watch(ns)

    mock_lpk.assert_called_once()
