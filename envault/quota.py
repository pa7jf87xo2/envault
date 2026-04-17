"""Vault size quota tracking and enforcement."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_MAX_BYTES = 1024 * 1024  # 1 MiB


class QuotaError(Exception):
    pass


def quota_path(vault: Path) -> Path:
    return vault.with_suffix(".quota.json")


def set_quota(vault: Path, max_bytes: int) -> dict:
    """Persist a quota config for *vault*."""
    if not vault.exists():
        raise QuotaError(f"vault not found: {vault}")
    if max_bytes <= 0:
        raise QuotaError("max_bytes must be a positive integer")
    entry = {"max_bytes": max_bytes}
    quota_path(vault).write_text(json.dumps(entry))
    return entry


def load_quota(vault: Path) -> dict | None:
    """Return the stored quota dict, or None if none is set."""
    p = quota_path(vault)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise QuotaError(f"corrupt quota file: {exc}") from exc


def check_quota(vault: Path) -> dict:
    """Raise QuotaError if *vault* exceeds its quota.

    Returns a status dict with keys: size, max_bytes, ok.
    """
    if not vault.exists():
        raise QuotaError(f"vault not found: {vault}")
    size = vault.stat().st_size
    quota = load_quota(vault)
    max_bytes = quota["max_bytes"] if quota else DEFAULT_MAX_BYTES
    ok = size <= max_bytes
    if not ok:
        raise QuotaError(
            f"vault size {size} B exceeds quota {max_bytes} B"
        )
    return {"size": size, "max_bytes": max_bytes, "ok": True}


def clear_quota(vault: Path) -> None:
    """Remove quota config for *vault*."""
    p = quota_path(vault)
    if p.exists():
        p.unlink()
