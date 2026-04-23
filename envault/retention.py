"""Retention policy management for vault files."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

RETENTION_SUFFIX = ".retention.json"


class RetentionError(Exception):
    """Raised when a retention operation fails."""


def retention_path(vault: Path) -> Path:
    """Return the sidecar retention file path for *vault*."""
    return vault.with_suffix(RETENTION_SUFFIX)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def set_retention(vault: Path, days: int, *, max_snapshots: Optional[int] = None) -> dict:
    """Set a retention policy for *vault*.

    Parameters
    ----------
    vault:
        Path to the encrypted vault file.
    days:
        Number of days to retain the vault before it is considered stale.
    max_snapshots:
        Optional cap on the number of snapshots to keep.

    Returns
    -------
    dict
        The written policy entry.
    """
    if not vault.exists():
        raise RetentionError(f"Vault not found: {vault}")
    if days <= 0:
        raise RetentionError("Retention period must be a positive number of days.")
    if max_snapshots is not None and max_snapshots <= 0:
        raise RetentionError("max_snapshots must be a positive integer.")

    policy: dict = {
        "days": days,
        "set_at": _now().isoformat(),
        "expires_at": (_now() + timedelta(days=days)).isoformat(),
    }
    if max_snapshots is not None:
        policy["max_snapshots"] = max_snapshots

    retention_path(vault).write_text(json.dumps(policy, indent=2))
    return policy


def load_retention(vault: Path) -> Optional[dict]:
    """Load the retention policy for *vault*, or ``None`` if not set."""
    if not vault.exists():
        raise RetentionError(f"Vault not found: {vault}")
    rp = retention_path(vault)
    if not rp.exists():
        return None
    try:
        return json.loads(rp.read_text())
    except json.JSONDecodeError as exc:
        raise RetentionError(f"Corrupt retention file: {exc}") from exc


def is_stale(vault: Path) -> bool:
    """Return ``True`` if the vault has exceeded its retention period."""
    policy = load_retention(vault)
    if policy is None:
        return False
    expires_at = datetime.fromisoformat(policy["expires_at"])
    return _now() > expires_at


def clear_retention(vault: Path) -> None:
    """Remove the retention policy sidecar for *vault*."""
    if not vault.exists():
        raise RetentionError(f"Vault not found: {vault}")
    rp = retention_path(vault)
    if rp.exists():
        rp.unlink()
