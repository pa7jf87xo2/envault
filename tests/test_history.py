"""Tests for envault/history.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.history import (
    HistoryError,
    clear_history,
    history_path,
    load_history,
    record_event,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"dummy")
    return v


def test_history_path_uses_suffix(tmp_path: Path) -> None:
    v = tmp_path / "my.vault"
    hp = history_path(v)
    assert hp.name == "my.vault.history.jsonl"


def test_record_event_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(HistoryError, match="vault not found"):
        record_event(tmp_path / "missing.vault", "pack")


def test_record_event_creates_history_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    record_event(v, "pack")
    assert history_path(v).exists()


def test_record_event_returns_entry(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    entry = record_event(v, "push", user="alice", note="deploy")
    assert entry["action"] == "push"
    assert entry["user"] == "alice"
    assert entry["note"] == "deploy"
    assert "ts" in entry


def test_record_event_omits_none_fields(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    entry = record_event(v, "unpack")
    assert "user" not in entry
    assert "note" not in entry


def test_record_event_appends_multiple(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    record_event(v, "pack")
    record_event(v, "push")
    lines = history_path(v).read_text().splitlines()
    assert len(lines) == 2


def test_load_history_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(HistoryError, match="vault not found"):
        load_history(tmp_path / "no.vault")


def test_load_history_returns_empty_when_no_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    assert load_history(v) == []


def test_load_history_returns_entries(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    record_event(v, "pack")
    record_event(v, "push", user="bob")
    entries = load_history(v)
    assert len(entries) == 2
    assert entries[0]["action"] == "pack"
    assert entries[1]["user"] == "bob"


def test_load_history_raises_on_corrupt_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    history_path(v).write_text("not-json\n")
    with pytest.raises(HistoryError, match="corrupt"):
        load_history(v)


def test_clear_history_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(HistoryError, match="vault not found"):
        clear_history(tmp_path / "no.vault")


def test_clear_history_removes_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    record_event(v, "pack")
    assert history_path(v).exists()
    clear_history(v)
    assert not history_path(v).exists()


def test_clear_history_noop_when_no_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    clear_history(v)  # should not raise
