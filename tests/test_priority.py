"""Tests for envault.priority."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.priority import (
    PriorityError,
    clear_priority,
    load_priority,
    priority_path,
    set_priority,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "secrets.vault"
    v.write_bytes(b"dummy")
    return v


# ---------------------------------------------------------------------------
# priority_path
# ---------------------------------------------------------------------------

def test_priority_path_uses_suffix(tmp_path):
    vault = tmp_path / "my.vault"
    assert priority_path(vault) == tmp_path / "my.priority.json"


# ---------------------------------------------------------------------------
# set_priority
# ---------------------------------------------------------------------------

def test_set_priority_raises_when_vault_missing(tmp_path):
    with pytest.raises(PriorityError, match="vault not found"):
        set_priority(tmp_path / "ghost.vault", "high")


def test_set_priority_raises_on_invalid_level(tmp_path):
    vault = _make_vault(tmp_path)
    with pytest.raises(PriorityError, match="invalid priority level"):
        set_priority(vault, "urgent")


def test_set_priority_creates_sidecar(tmp_path):
    vault = _make_vault(tmp_path)
    set_priority(vault, "high")
    assert priority_path(vault).exists()


def test_set_priority_returns_entry(tmp_path):
    vault = _make_vault(tmp_path)
    entry = set_priority(vault, "critical")
    assert entry["level"] == "critical"
    assert entry["vault"] == str(vault)


def test_set_priority_persists_level(tmp_path):
    vault = _make_vault(tmp_path)
    set_priority(vault, "low")
    data = json.loads(priority_path(vault).read_text())
    assert data["level"] == "low"


# ---------------------------------------------------------------------------
# load_priority
# ---------------------------------------------------------------------------

def test_load_priority_raises_when_vault_missing(tmp_path):
    with pytest.raises(PriorityError, match="vault not found"):
        load_priority(tmp_path / "ghost.vault")


def test_load_priority_returns_none_when_unset(tmp_path):
    vault = _make_vault(tmp_path)
    assert load_priority(vault) is None


def test_load_priority_returns_set_value(tmp_path):
    vault = _make_vault(tmp_path)
    set_priority(vault, "normal")
    assert load_priority(vault) == "normal"


def test_load_priority_raises_on_corrupt_file(tmp_path):
    vault = _make_vault(tmp_path)
    priority_path(vault).write_text("not json")
    with pytest.raises(PriorityError, match="corrupt"):
        load_priority(vault)


# ---------------------------------------------------------------------------
# clear_priority
# ---------------------------------------------------------------------------

def test_clear_priority_raises_when_vault_missing(tmp_path):
    with pytest.raises(PriorityError, match="vault not found"):
        clear_priority(tmp_path / "ghost.vault")


def test_clear_priority_returns_false_when_nothing_to_remove(tmp_path):
    vault = _make_vault(tmp_path)
    assert clear_priority(vault) is False


def test_clear_priority_removes_sidecar(tmp_path):
    vault = _make_vault(tmp_path)
    set_priority(vault, "high")
    result = clear_priority(vault)
    assert result is True
    assert not priority_path(vault).exists()
