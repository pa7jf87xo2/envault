"""envault.rollback — restore a vault to a previous snapshot or archive.

Provides a single `rollback` function that locates a named snapshot (or the
most-recent one when no name is supplied) and copies it over the active vault
file, optionally writing an audit entry and recording the event in history.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from envault import audit, snapshot as _snap
from envault.history import record_event


class RollbackError(Exception):
    """Raised when a rollback operation cannot be completed."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def rollback(
    vault: Path,
    *,
    name: Optional[str] = None,
    dry_run: bool = False,
    record_history: bool = True,
) -> Path:
    """Restore *vault* from a snapshot.

    Parameters
    ----------
    vault:
        Path to the active ``.vault`` file that will be overwritten.
    name:
        Snapshot stem to restore.  When *None* the most-recent snapshot is
        used.  Accepts either the bare timestamp (e.g. ``"20240101T120000"``)
        or the full filename (e.g. ``"20240101T120000.vault"``).
    dry_run:
        When *True* the function resolves and validates the snapshot but does
        **not** overwrite the vault file.  Useful for previewing which
        snapshot would be applied.
    record_history:
        When *True* (default) a ``rollback`` event is appended to the vault's
        history log via :func:`envault.history.record_event`.

    Returns
    -------
    Path
        The snapshot file that was (or would be) restored.

    Raises
    ------
    RollbackError
        If the vault file does not exist, no snapshots are available, or the
        requested snapshot cannot be found.
    """
    vault = Path(vault)
    if not vault.exists():
        raise RollbackError(f"Vault not found: {vault}")

    snap_dir = _snap.snapshots_dir(vault)
    if not snap_dir.exists() or not any(snap_dir.iterdir()):
        raise RollbackError(f"No snapshots found for vault: {vault}")

    source = _resolve_snapshot(snap_dir, name)

    if not dry_run:
        shutil.copy2(source, vault)
        audit.record(
            "rollback",
            vault=str(vault),
            snapshot=source.name,
        )
        if record_history:
            try:
                record_event(
                    vault,
                    action="rollback",
                    detail=source.name,
                )
            except Exception:  # history failure must not abort the rollback
                pass

    return source


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_snapshot(snap_dir: Path, name: Optional[str]) -> Path:
    """Return the Path of the snapshot to restore.

    When *name* is ``None`` the lexicographically last ``.vault`` file in
    *snap_dir* is returned (snapshots are timestamped so this equals the
    most-recent one).
    """
    candidates = sorted(snap_dir.glob("*.vault"))
    if not candidates:
        raise RollbackError(f"Snapshot directory is empty: {snap_dir}")

    if name is None:
        return candidates[-1]

    # Accept bare stem or full filename.
    stem = name if not name.endswith(".vault") else name[:-6]
    for path in candidates:
        if path.stem == stem or path.name == name:
            return path

    raise RollbackError(
        f"Snapshot '{name}' not found in {snap_dir}. "
        f"Available: {[p.name for p in candidates]}"
    )
