"""Tests for envault.sync (push / pull)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.sync import SyncError, pull, push


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_vault(tmp_path: Path, name: str = "env.vault") -> Path:
    p = tmp_path / name
    p.write_bytes(b"encrypted-payload")
    return p


# ---------------------------------------------------------------------------
# push — local
# ---------------------------------------------------------------------------

def test_push_local_copies_file(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    dest_dir = tmp_path / "backup"
    push(vault, str(dest_dir))
    assert (dest_dir / vault.name).exists()


def test_push_local_creates_missing_dest_dir(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    dest_dir = tmp_path / "deep" / "nested"
    push(vault, str(dest_dir))
    assert (dest_dir / vault.name).read_bytes() == b"encrypted-payload"


def test_push_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(SyncError, match="Vault file not found"):
        push(tmp_path / "missing.vault", str(tmp_path / "dest"))


# ---------------------------------------------------------------------------
# push — remote
# ---------------------------------------------------------------------------

def test_push_remote_calls_scp(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    completed = MagicMock(returncode=0)
    with patch("shutil.which", return_value="/usr/bin/scp"), \
         patch("subprocess.run", return_value=completed) as mock_run:
        push(vault, "user@host:/remote/dir/")
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "scp"
    assert str(vault) in cmd


def test_push_remote_raises_on_scp_error(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    completed = MagicMock(returncode=1, stderr="permission denied")
    with patch("shutil.which", return_value="/usr/bin/scp"), \
         patch("subprocess.run", return_value=completed):
        with pytest.raises(SyncError, match="scp push failed"):
            push(vault, "user@host:/remote/dir/")


def test_push_remote_raises_when_scp_missing(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("shutil.which", return_value=None):
        with pytest.raises(SyncError, match="scp.*not found"):
            push(vault, "user@host:/remote/dir/")


# ---------------------------------------------------------------------------
# pull — local
# ---------------------------------------------------------------------------

def test_pull_local_copies_file(tmp_path: Path) -> None:
    src = _make_vault(tmp_path, "source.vault")
    dest = tmp_path / "received" / "env.vault"
    pull(str(src), dest)
    assert dest.read_bytes() == b"encrypted-payload"


def test_pull_local_raises_when_source_missing(tmp_path: Path) -> None:
    with pytest.raises(SyncError, match="Source file not found"):
        pull(str(tmp_path / "ghost.vault"), tmp_path / "out.vault")


# ---------------------------------------------------------------------------
# pull — remote
# ---------------------------------------------------------------------------

def test_pull_remote_calls_scp(tmp_path: Path) -> None:
    dest = tmp_path / "env.vault"
    completed = MagicMock(returncode=0)
    with patch("shutil.which", return_value="/usr/bin/scp"), \
         patch("subprocess.run", return_value=completed) as mock_run:
        pull("user@host:/remote/env.vault", dest)
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "scp"
    assert str(dest) in cmd
