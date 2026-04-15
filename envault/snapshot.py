"""Snapshot management: save and restore named vault snapshots."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

SNAPSHOT_DIR_NAME = ".envault_snapshots"


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def snapshots_dir(base: Path) -> Path:
    """Return the snapshots directory relative to *base*."""
    return base / SNAPSHOT_DIR_NAME


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def save_snapshot(vault: Path, name: str | None = None, *, base: Path | None = None) -> Path:
    """Copy *vault* into the snapshots directory.

    Parameters
    ----------
    vault:  path to the ``.vault`` file to snapshot.
    name:   optional label; if omitted a UTC timestamp is used.
    base:   directory that contains the snapshots folder (defaults to
            ``vault.parent``).

    Returns the path of the newly created snapshot file.
    """
    if not vault.exists():
        raise SnapshotError(f"Vault not found: {vault}")

    label = name or _ts()
    # Reject labels that would produce unsafe filenames
    if any(c in label for c in ("/", "\\", "\0")):
        raise SnapshotError(f"Invalid snapshot name: {label!r}")

    dest_dir = snapshots_dir(base or vault.parent)
    dest_dir.mkdir(parents=True, exist_ok=True)

    stem = vault.stem
    dest = dest_dir / f"{stem}__{label}{vault.suffix}"
    if dest.exists():
        raise SnapshotError(f"Snapshot already exists: {dest.name}")

    shutil.copy2(vault, dest)
    return dest


def list_snapshots(base: Path, vault_stem: str | None = None) -> list[Path]:
    """Return snapshot files sorted by name (oldest first).

    If *vault_stem* is given only snapshots for that vault are returned.
    """
    sdir = snapshots_dir(base)
    if not sdir.exists():
        return []
    files = sorted(sdir.glob("*.vault"))
    if vault_stem:
        files = [f for f in files if f.name.startswith(f"{vault_stem}__")]
    return files


def restore_snapshot(snapshot: Path, dest: Path, *, overwrite: bool = False) -> None:
    """Overwrite *dest* with the contents of *snapshot*."""
    if not snapshot.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot}")
    if dest.exists() and not overwrite:
        raise SnapshotError(
            f"Destination already exists: {dest}. Pass overwrite=True to replace it."
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(snapshot, dest)
