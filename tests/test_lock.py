"""Tests for envault.lock."""

from __future__ import annotations

import os
import time
import threading
from pathlib import Path

import pytest

from envault.lock import (
    LockError,
    acquire,
    is_locked,
    lock_path,
    release,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"data")
    return v


def test_lock_path_uses_suffix(tmp_path: Path):
    v = tmp_path / "my.vault"
    assert lock_path(v) == tmp_path / "my.vault.lock"


def test_acquire_raises_when_vault_missing(tmp_path: Path):
    v = tmp_path / "missing.vault"
    with pytest.raises(LockError, match="vault not found"):
        acquire(v)


def test_acquire_creates_lock_file(tmp_path: Path):
    v = _make_vault(tmp_path)
    lp = acquire(v)
    assert lp.exists()
    lp.unlink()


def test_acquire_lock_file_contains_pid(tmp_path: Path):
    v = _make_vault(tmp_path)
    lp = acquire(v)
    assert lp.read_text().strip() == str(os.getpid())
    lp.unlink()


def test_is_locked_false_when_no_lock(tmp_path: Path):
    v = _make_vault(tmp_path)
    assert is_locked(v) is False


def test_is_locked_true_after_acquire(tmp_path: Path):
    v = _make_vault(tmp_path)
    lp = acquire(v)
    assert is_locked(v) is True
    lp.unlink()


def test_release_removes_lock(tmp_path: Path):
    v = _make_vault(tmp_path)
    acquire(v)
    release(v)
    assert not is_locked(v)


def test_release_raises_when_no_lock(tmp_path: Path):
    v = _make_vault(tmp_path)
    with pytest.raises(LockError, match="no lock file"):
        release(v)


def test_acquire_times_out_when_already_locked(tmp_path: Path):
    v = _make_vault(tmp_path)
    lp = acquire(v)
    try:
        with pytest.raises(LockError, match="could not acquire lock"):
            acquire(v, timeout=0.2, poll=0.05)
    finally:
        lp.unlink()


def test_acquire_succeeds_after_lock_released(tmp_path: Path):
    v = _make_vault(tmp_path)
    results: list[bool] = []

    def _hold_then_release():
        lp = acquire(v)
        time.sleep(0.15)
        lp.unlink()

    t = threading.Thread(target=_hold_then_release)
    t.start()
    time.sleep(0.02)
    lp2 = acquire(v, timeout=1.0, poll=0.05)
    results.append(lp2.exists())
    lp2.unlink()
    t.join()
    assert results == [True]


def test_release_raises_when_lock_owned_by_other_pid(tmp_path: Path):
    """release() should raise LockError when the lock file contains a foreign PID."""
    v = _make_vault(tmp_path)
    lp = lock_path(v)
    # Write a PID that is guaranteed not to be ours.
    foreign_pid = os.getpid() + 1
    lp.write_text(str(foreign_pid))
    try:
        with pytest.raises(LockError, match="not owner"):
            release(v)
    finally:
        if lp.exists():
            lp.unlink()
