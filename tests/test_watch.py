"""Tests for envault.watch."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from envault.watch import watch, WatchError


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str = "KEY=value\n") -> None:
    path.write_text(content)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_watch_raises_when_env_file_missing(tmp_path):
    with pytest.raises(WatchError, match="env file not found"):
        watch(tmp_path / "missing.env", tmp_path / "out.vault", "age1abc", max_events=1)


def test_watch_repacks_on_change(tmp_path):
    env_file = tmp_path / ".env"
    vault_file = tmp_path / "out.vault"
    _write(env_file)

    packed_calls = []

    def fake_pack(src, dst, key):
        packed_calls.append((src, dst, key))
        dst.write_bytes(b"vault")

    # Simulate mtime change on second poll by patching _mtime
    mtimes = [1.0, 1.0, 2.0]  # first call (init), first poll (no change), second poll (change)
    mtime_iter = iter(mtimes)

    with patch("envault.watch.pack", side_effect=fake_pack), \
         patch("envault.watch._mtime", side_effect=lambda p: next(mtime_iter)), \
         patch("envault.watch.time.sleep"), \
         patch("envault.watch.record"):
        watch(env_file, vault_file, "age1pub", max_events=1)

    assert len(packed_calls) == 1
    assert packed_calls[0][2] == "age1pub"


def test_watch_calls_on_change_callback(tmp_path):
    env_file = tmp_path / ".env"
    vault_file = tmp_path / "out.vault"
    _write(env_file)

    callback = MagicMock()
    mtimes = [1.0, 2.0]
    mtime_iter = iter(mtimes)

    with patch("envault.watch.pack"), \
         patch("envault.watch._mtime", side_effect=lambda p: next(mtime_iter)), \
         patch("envault.watch.time.sleep"), \
         patch("envault.watch.record"):
        watch(env_file, vault_file, "age1pub", max_events=1, on_change=callback)

    callback.assert_called_once_with(vault_file)


def test_watch_raises_on_pack_failure(tmp_path):
    env_file = tmp_path / ".env"
    vault_file = tmp_path / "out.vault"
    _write(env_file)

    from envault.vault import VaultError
    mtimes = [1.0, 2.0]
    mtime_iter = iter(mtimes)

    with patch("envault.watch.pack", side_effect=VaultError("boom")), \
         patch("envault.watch._mtime", side_effect=lambda p: next(mtime_iter)), \
         patch("envault.watch.time.sleep"), \
         patch("envault.watch.record"):
        with pytest.raises(WatchError, match="repack failed"):
            watch(env_file, vault_file, "age1pub", max_events=1)


def test_watch_skips_unchanged_mtime(tmp_path):
    env_file = tmp_path / ".env"
    vault_file = tmp_path / "out.vault"
    _write(env_file)

    packed_calls = []
    # same mtime for 2 polls, then change on 3rd
    mtimes = [1.0, 1.0, 1.0, 2.0]
    mtime_iter = iter(mtimes)

    def fake_pack(src, dst, key):
        packed_calls.append(1)
        dst.write_bytes(b"v")

    with patch("envault.watch.pack", side_effect=fake_pack), \
         patch("envault.watch._mtime", side_effect=lambda p: next(mtime_iter)), \
         patch("envault.watch.time.sleep"), \
         patch("envault.watch.record"):
        watch(env_file, vault_file, "age1pub", max_events=1)

    assert len(packed_calls) == 1
