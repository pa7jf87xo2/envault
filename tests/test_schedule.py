"""Tests for envault.schedule."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from envault.schedule import (
    ScheduleError,
    due_schedules,
    load_schedule,
    remove_schedule,
    schedule_path,
    set_schedule,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"dummy")
    return v


# ---------------------------------------------------------------------------
# schedule_path
# ---------------------------------------------------------------------------

def test_schedule_path_uses_suffix(tmp_path):
    vault = tmp_path / "my.vault"
    assert schedule_path(vault) == tmp_path / "my.schedule.json"


# ---------------------------------------------------------------------------
# set_schedule
# ---------------------------------------------------------------------------

def test_set_schedule_raises_when_vault_missing(tmp_path):
    with pytest.raises(ScheduleError, match="vault not found"):
        set_schedule(tmp_path / "ghost.vault", "rotate", 7)


def test_set_schedule_raises_on_invalid_action(tmp_path):
    vault = _make_vault(tmp_path)
    with pytest.raises(ScheduleError, match="invalid action"):
        set_schedule(vault, "explode", 7)


def test_set_schedule_raises_on_zero_interval(tmp_path):
    vault = _make_vault(tmp_path)
    with pytest.raises(ScheduleError, match="interval_days must be"):
        set_schedule(vault, "rotate", 0)


def test_set_schedule_creates_file(tmp_path):
    vault = _make_vault(tmp_path)
    set_schedule(vault, "rotate", 7)
    assert schedule_path(vault).exists()


def test_set_schedule_returns_entry(tmp_path):
    vault = _make_vault(tmp_path)
    entry = set_schedule(vault, "pack", 3)
    assert entry["action"] == "pack"
    assert entry["interval_days"] == 3
    assert "next_run" in entry
    assert "created_at" in entry


def test_set_schedule_raises_if_exists_no_overwrite(tmp_path):
    vault = _make_vault(tmp_path)
    set_schedule(vault, "rotate", 7)
    with pytest.raises(ScheduleError, match="already exists"):
        set_schedule(vault, "rotate", 14)


def test_set_schedule_overwrites_when_requested(tmp_path):
    vault = _make_vault(tmp_path)
    set_schedule(vault, "rotate", 7)
    entry = set_schedule(vault, "rotate", 14, overwrite=True)
    assert entry["interval_days"] == 14


def test_set_schedule_multiple_actions(tmp_path):
    vault = _make_vault(tmp_path)
    set_schedule(vault, "rotate", 7)
    set_schedule(vault, "snapshot", 1)
    schedules = load_schedule(vault)
    assert set(schedules.keys()) == {"rotate", "snapshot"}


# ---------------------------------------------------------------------------
# load_schedule
# ---------------------------------------------------------------------------

def test_load_schedule_raises_when_vault_missing(tmp_path):
    with pytest.raises(ScheduleError, match="vault not found"):
        load_schedule(tmp_path / "ghost.vault")


def test_load_schedule_returns_empty_when_no_file(tmp_path):
    vault = _make_vault(tmp_path)
    assert load_schedule(vault) == {}


def test_load_schedule_raises_on_corrupt_file(tmp_path):
    vault = _make_vault(tmp_path)
    schedule_path(vault).write_text("not-json")
    with pytest.raises(ScheduleError, match="corrupt"):
        load_schedule(vault)


# ---------------------------------------------------------------------------
# remove_schedule
# ---------------------------------------------------------------------------

def test_remove_schedule_returns_false_when_no_file(tmp_path):
    vault = _make_vault(tmp_path)
    assert remove_schedule(vault, "rotate") is False


def test_remove_schedule_returns_false_when_action_absent(tmp_path):
    vault = _make_vault(tmp_path)
    set_schedule(vault, "pack", 5)
    assert remove_schedule(vault, "rotate") is False


def test_remove_schedule_removes_entry(tmp_path):
    vault = _make_vault(tmp_path)
    set_schedule(vault, "rotate", 7)
    assert remove_schedule(vault, "rotate") is True
    assert "rotate" not in load_schedule(vault)


# ---------------------------------------------------------------------------
# due_schedules
# ---------------------------------------------------------------------------

def test_due_schedules_returns_overdue_entries(tmp_path):
    vault = _make_vault(tmp_path)
    # Write a schedule whose next_run is in the past
    past = (datetime.utcnow() - timedelta(days=1)).isoformat()
    data = {"rotate": {"action": "rotate", "interval_days": 7,
                        "created_at": past, "next_run": past}}
    schedule_path(vault).write_text(json.dumps(data))
    due = due_schedules(vault)
    assert len(due) == 1
    assert due[0]["action"] == "rotate"


def test_due_schedules_excludes_future_entries(tmp_path):
    vault = _make_vault(tmp_path)
    set_schedule(vault, "snapshot", 30)
    assert due_schedules(vault) == []
