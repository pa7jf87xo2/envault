"""Tests for envault.cli_notify."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_notify import (
    _cmd_notify_status,
    _cmd_notify_webhook,
    _cmd_notify_desktop,
    build_parser,
)
from envault.notify import NotifyError


def _ns(**kw) -> argparse.Namespace:
    return argparse.Namespace(**kw)


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_parser_has_subcommands():
    p = build_parser()
    # parsing without args should fail (required subcommand)
    with pytest.raises(SystemExit):
        p.parse_args(["some.vault"])


def test_cmd_notify_status_no_config(tmp_path, capsys):
    v = tmp_path / "t.vault"
    v.write_bytes(b"x")
    _cmd_notify_status(_ns(vault=str(v)))
    out = capsys.readouterr().out
    assert "no notification" in out


def test_cmd_notify_status_shows_webhook(tmp_path, capsys):
    v = tmp_path / "t.vault"
    v.write_bytes(b"x")
    with patch("envault.cli_notify.load_config", return_value={"webhook": "https://ex.com"}):
        _cmd_notify_status(_ns(vault=str(v)))
    out = capsys.readouterr().out
    assert "https://ex.com" in out


def test_cmd_notify_status_exits_on_error(tmp_path):
    with pytest.raises(SystemExit):
        _cmd_notify_status(_ns(vault=str(tmp_path / "missing.vault")))


def test_cmd_notify_webhook_sets_url(tmp_path, capsys):
    v = tmp_path / "t.vault"
    v.write_bytes(b"x")
    with patch("envault.cli_notify.set_webhook") as mock_sw:
        _cmd_notify_webhook(_ns(vault=str(v), url="https://hooks.example.com/1"))
    mock_sw.assert_called_once()
    assert "webhook set" in capsys.readouterr().out


def test_cmd_notify_webhook_clears_url(tmp_path, capsys):
    v = tmp_path / "t.vault"
    v.write_bytes(b"x")
    with patch("envault.cli_notify.load_config", return_value={"webhook": "https://x.com"}), \
         patch("envault.cli_notify.save_config") as mock_save:
        _cmd_notify_webhook(_ns(vault=str(v), url=""))
    mock_save.assert_called_once()
    assert "cleared" in capsys.readouterr().out


def test_cmd_notify_webhook_exits_on_error(tmp_path):
    with pytest.raises(SystemExit):
        _cmd_notify_webhook(_ns(vault=str(tmp_path / "missing.vault"), url="https://x.com"))


def test_cmd_notify_desktop_enable(tmp_path, capsys):
    v = tmp_path / "t.vault"
    v.write_bytes(b"x")
    with patch("envault.cli_notify.load_config", return_value={}), \
         patch("envault.cli_notify.save_config") as mock_save:
        _cmd_notify_desktop(_ns(vault=str(v), action="enable"))
    saved_cfg = mock_save.call_args[0][1]
    assert saved_cfg.get("desktop") is True
    assert "enabled" in capsys.readouterr().out


def test_cmd_notify_desktop_disable(tmp_path, capsys):
    v = tmp_path / "t.vault"
    v.write_bytes(b"x")
    with patch("envault.cli_notify.load_config", return_value={"desktop": True}), \
         patch("envault.cli_notify.save_config") as mock_save:
        _cmd_notify_desktop(_ns(vault=str(v), action="disable"))
    saved_cfg = mock_save.call_args[0][1]
    assert "desktop" not in saved_cfg
    assert "disabled" in capsys.readouterr().out
