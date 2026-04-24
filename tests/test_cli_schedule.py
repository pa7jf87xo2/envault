"""Tests for envault.cli_schedule."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_schedule import (
    _cmd_schedule_due,
    _cmd_schedule_list,
    _cmd_schedule_remove,
    _cmd_schedule_set,
    build_parser,
)
from envault.schedule import ScheduleError, schedule_path


def _ns(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_parser_has_subcommands():
    p = build_parser()
    # Should not raise when parsing valid sub-command
    args = p.parse_args(["set", "my.vault", "rotate", "7"])
    assert args.action == "rotate"
    assert args.interval_days == 7


# ---------------------------------------------------------------------------
# _cmd_schedule_set
# ---------------------------------------------------------------------------

def test_cmd_schedule_set_prints_confirmation(tmp_path, capsys):
    vault = tmp_path / "t.vault"
    vault.write_bytes(b"x")
    _cmd_schedule_set(_ns(vault=str(vault), action="rotate", interval_days=7, overwrite=False))
    out = capsys.readouterr().out
    assert "rotate" in out
    assert "7" in out


def test_cmd_schedule_set_exits_on_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _cmd_schedule_set(
            _ns(vault=str(tmp_path / "ghost.vault"), action="rotate", interval_days=7, overwrite=False)
        )
    assert exc.value.code == 1
    assert "error" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# _cmd_schedule_list
# ---------------------------------------------------------------------------

def test_cmd_schedule_list_empty(tmp_path, capsys):
    vault = tmp_path / "t.vault"
    vault.write_bytes(b"x")
    _cmd_schedule_list(_ns(vault=str(vault)))
    assert "No schedules" in capsys.readouterr().out


def test_cmd_schedule_list_shows_entries(tmp_path, capsys):
    vault = tmp_path / "t.vault"
    vault.write_bytes(b"x")
    _cmd_schedule_set(_ns(vault=str(vault), action="pack", interval_days=3, overwrite=False))
    capsys.readouterr()  # discard set output
    _cmd_schedule_list(_ns(vault=str(vault)))
    out = capsys.readouterr().out
    assert "pack" in out
    assert "3" in out


# ---------------------------------------------------------------------------
# _cmd_schedule_remove
# ---------------------------------------------------------------------------

def test_cmd_schedule_remove_existing(tmp_path, capsys):
    vault = tmp_path / "t.vault"
    vault.write_bytes(b"x")
    _cmd_schedule_set(_ns(vault=str(vault), action="snapshot", interval_days=1, overwrite=False))
    capsys.readouterr()
    _cmd_schedule_remove(_ns(vault=str(vault), action="snapshot"))
    assert "Removed" in capsys.readouterr().out


def test_cmd_schedule_remove_absent(tmp_path, capsys):
    vault = tmp_path / "t.vault"
    vault.write_bytes(b"x")
    _cmd_schedule_remove(_ns(vault=str(vault), action="rotate"))
    assert "No schedule found" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _cmd_schedule_due
# ---------------------------------------------------------------------------

def test_cmd_schedule_due_none(tmp_path, capsys):
    vault = tmp_path / "t.vault"
    vault.write_bytes(b"x")
    _cmd_schedule_due(_ns(vault=str(vault)))
    assert "No schedules" in capsys.readouterr().out


def test_cmd_schedule_due_shows_overdue(tmp_path, capsys):
    vault = tmp_path / "t.vault"
    vault.write_bytes(b"x")
    past = (datetime.utcnow() - timedelta(days=2)).isoformat()
    data = {"rotate": {"action": "rotate", "interval_days": 7,
                        "created_at": past, "next_run": past}}
    schedule_path(vault).write_text(json.dumps(data))
    _cmd_schedule_due(_ns(vault=str(vault)))
    out = capsys.readouterr().out
    assert "rotate" in out
