"""Tests for envault.audit."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.audit import record, read_log, tail_log


# ---------------------------------------------------------------------------
# record
# ---------------------------------------------------------------------------

def test_record_creates_log_file(tmp_path):
    log = tmp_path / "audit.log"
    record("init", log_path=log)
    assert log.exists()


def test_record_returns_entry_dict(tmp_path):
    log = tmp_path / "audit.log"
    entry = record("pack", vault=".envault", source=".env", log_path=log)
    assert entry["op"] == "pack"
    assert entry["vault"] == ".envault"
    assert entry["source"] == ".env"
    assert "ts" in entry


def test_record_omits_none_fields(tmp_path):
    log = tmp_path / "audit.log"
    entry = record("init", log_path=log)
    assert "vault" not in entry
    assert "source" not in entry
    assert "destination" not in entry


def test_record_includes_extra_fields(tmp_path):
    log = tmp_path / "audit.log"
    entry = record("push", extra={"remote": "user@host"}, log_path=log)
    assert entry["remote"] == "user@host"


def test_record_appends_multiple_entries(tmp_path):
    log = tmp_path / "audit.log"
    for op in ("pack", "push", "pull"):
        record(op, log_path=log)  # type: ignore[arg-type]
    lines = [l for l in log.read_text().splitlines() if l.strip()]
    assert len(lines) == 3


def test_record_creates_parent_dirs(tmp_path):
    log = tmp_path / "deep" / "nested" / "audit.log"
    record("init", log_path=log)
    assert log.exists()


# ---------------------------------------------------------------------------
# read_log
# ---------------------------------------------------------------------------

def test_read_log_returns_empty_when_missing(tmp_path):
    log = tmp_path / "audit.log"
    assert read_log(log) == []


def test_read_log_returns_all_entries(tmp_path):
    log = tmp_path / "audit.log"
    for op in ("pack", "unpack"):
        record(op, log_path=log)  # type: ignore[arg-type]
    entries = read_log(log)
    assert len(entries) == 2
    assert entries[0]["op"] == "pack"
    assert entries[1]["op"] == "unpack"


def test_read_log_skips_corrupted_lines(tmp_path):
    log = tmp_path / "audit.log"
    log.write_text('{"op": "pack", "ts": "x"}\nnot-json\n{"op": "pull", "ts": "y"}\n')
    entries = read_log(log)
    assert len(entries) == 2


# ---------------------------------------------------------------------------
# tail_log
# ---------------------------------------------------------------------------

def test_tail_log_returns_last_n(tmp_path):
    log = tmp_path / "audit.log"
    for i in range(10):
        record("pack", extra={"i": i}, log_path=log)
    tail = tail_log(n=3, log_path=log)
    assert len(tail) == 3
    assert tail[-1]["i"] == 9


def test_tail_log_returns_all_when_fewer_than_n(tmp_path):
    log = tmp_path / "audit.log"
    record("init", log_path=log)
    assert len(tail_log(n=50, log_path=log)) == 1
