"""Tests for envault.cli_watermark."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.cli_watermark import (
    _cmd_watermark_set,
    _cmd_watermark_show,
    _cmd_watermark_clear,
    build_parser,
)
from envault.watermark import WatermarkError


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"vault": "secrets.vault", "author": "alice", "machine": None, "note": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_parser_has_subcommands():
    p = build_parser()
    ns = p.parse_args(["set", "my.vault", "--author", "alice"])
    assert ns.watermark_cmd == "set"
    assert ns.author == "alice"


# ---------------------------------------------------------------------------
# _cmd_watermark_set
# ---------------------------------------------------------------------------

def test_cmd_watermark_set_prints_confirmation(capsys):
    entry = {"author": "alice", "stamped_at": "2024-01-01T00:00:00+00:00"}
    with patch("envault.cli_watermark.set_watermark", return_value=entry):
        _cmd_watermark_set(_ns())
    out = capsys.readouterr().out
    assert "Watermark set" in out
    assert "alice" in out


def test_cmd_watermark_set_exits_on_error(capsys):
    with patch("envault.cli_watermark.set_watermark", side_effect=WatermarkError("boom")):
        with pytest.raises(SystemExit) as exc_info:
            _cmd_watermark_set(_ns())
    assert exc_info.value.code == 1
    assert "boom" in capsys.readouterr().err


def test_cmd_watermark_set_uses_hostname_when_no_machine(capsys):
    entry = {"author": "bob", "stamped_at": "2024-01-01T00:00:00+00:00", "machine": "myhost"}
    with patch("envault.cli_watermark.set_watermark", return_value=entry) as mock_sw:
        with patch("envault.cli_watermark._hostname", return_value="myhost"):
            _cmd_watermark_set(_ns(machine=None))
    _, kwargs = mock_sw.call_args
    assert kwargs["machine"] == "myhost"


# ---------------------------------------------------------------------------
# _cmd_watermark_show
# ---------------------------------------------------------------------------

def test_cmd_watermark_show_prints_fields(capsys):
    wm = {"author": "carol", "stamped_at": "2024-06-01T12:00:00+00:00", "machine": "srv1"}
    with patch("envault.cli_watermark.load_watermark", return_value=wm):
        _cmd_watermark_show(_ns())
    out = capsys.readouterr().out
    assert "carol" in out
    assert "srv1" in out


def test_cmd_watermark_show_no_watermark(capsys):
    with patch("envault.cli_watermark.load_watermark", return_value=None):
        _cmd_watermark_show(_ns())
    assert "No watermark" in capsys.readouterr().out


def test_cmd_watermark_show_exits_on_error(capsys):
    with patch("envault.cli_watermark.load_watermark", side_effect=WatermarkError("missing")):
        with pytest.raises(SystemExit) as exc_info:
            _cmd_watermark_show(_ns())
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# _cmd_watermark_clear
# ---------------------------------------------------------------------------

def test_cmd_watermark_clear_prints_cleared(capsys):
    with patch("envault.cli_watermark.clear_watermark", return_value=True):
        _cmd_watermark_clear(_ns())
    assert "cleared" in capsys.readouterr().out.lower()


def test_cmd_watermark_clear_prints_nothing_to_clear(capsys):
    with patch("envault.cli_watermark.clear_watermark", return_value=False):
        _cmd_watermark_clear(_ns())
    assert "No watermark" in capsys.readouterr().out


def test_cmd_watermark_clear_exits_on_error(capsys):
    with patch("envault.cli_watermark.clear_watermark", side_effect=WatermarkError("err")):
        with pytest.raises(SystemExit) as exc_info:
            _cmd_watermark_clear(_ns())
    assert exc_info.value.code == 1
