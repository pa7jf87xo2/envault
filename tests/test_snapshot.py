"""Tests for envault.snapshot."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.snapshot import (
    SnapshotError,
    list_snapshots,
    restore_snapshot,
    save_snapshot,
    snapshots_dir,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_vault(tmp_path: Path, name: str = "test.vault") -> Path:
    p = tmp_path / name
    p.write_bytes(b"encrypted-payload")
    return p


# ---------------------------------------------------------------------------
# snapshots_dir
# ---------------------------------------------------------------------------

def test_snapshots_dir_returns_correct_path(tmp_path: Path) -> None:
    assert snapshots_dir(tmp_path) == tmp_path / ".envault_snapshots"


# ---------------------------------------------------------------------------
# save_snapshot
# ---------------------------------------------------------------------------

def test_save_snapshot_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(SnapshotError, match="Vault not found"):
        save_snapshot(tmp_path / "missing.vault")


def test_save_snapshot_creates_file(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    snap = save_snapshot(vault)
    assert snap.exists()


def test_save_snapshot_uses_custom_name(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    snap = save_snapshot(vault, name="before-deploy")
    assert "before-deploy" in snap.name


def test_save_snapshot_content_matches(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    snap = save_snapshot(vault, name="v1")
    assert snap.read_bytes() == vault.read_bytes()


def test_save_snapshot_raises_on_duplicate_name(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    save_snapshot(vault, name="dup")
    with pytest.raises(SnapshotError, match="already exists"):
        save_snapshot(vault, name="dup")


def test_save_snapshot_raises_on_invalid_name(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with pytest.raises(SnapshotError, match="Invalid snapshot name"):
        save_snapshot(vault, name="bad/name")


# ---------------------------------------------------------------------------
# list_snapshots
# ---------------------------------------------------------------------------

def test_list_snapshots_empty_when_no_dir(tmp_path: Path) -> None:
    assert list_snapshots(tmp_path) == []


def test_list_snapshots_returns_sorted(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    save_snapshot(vault, name="aaa")
    save_snapshot(vault, name="bbb")
    snaps = list_snapshots(tmp_path)
    assert len(snaps) == 2
    assert snaps[0].name < snaps[1].name


def test_list_snapshots_filters_by_stem(tmp_path: Path) -> None:
    vault_a = _make_vault(tmp_path, "alpha.vault")
    vault_b = _make_vault(tmp_path, "beta.vault")
    save_snapshot(vault_a, name="s1")
    save_snapshot(vault_b, name="s2")
    snaps = list_snapshots(tmp_path, vault_stem="alpha")
    assert len(snaps) == 1
    assert "alpha" in snaps[0].name


# ---------------------------------------------------------------------------
# restore_snapshot
# ---------------------------------------------------------------------------

def test_restore_snapshot_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(SnapshotError, match="Snapshot not found"):
        restore_snapshot(tmp_path / "ghost.vault", tmp_path / "out.vault")


def test_restore_snapshot_raises_if_dest_exists_no_overwrite(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    snap = save_snapshot(vault, name="r1")
    with pytest.raises(SnapshotError, match="already exists"):
        restore_snapshot(snap, vault)  # vault still exists


def test_restore_snapshot_overwrites_when_requested(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    snap = save_snapshot(vault, name="r2")
    vault.write_bytes(b"changed")
    restore_snapshot(snap, vault, overwrite=True)
    assert vault.read_bytes() == b"encrypted-payload"
