"""Vault expiry: set and check TTL on encrypted vaults."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

EXPIRY_SUFFIX = ".expiry.json"


class ExpireError(Exception):
    pass


def expiry_path(vault: Path) -> Path:
    return vault.with_name(vault.name + EXPIRY_SUFFIX)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def set_expiry(vault: Path, days: int) -> dict:
    """Record an expiry date for *vault*. Returns the stored entry."""
    if not vault.exists():
        raise ExpireError(f"vault not found: {vault}")
    if days <= 0:
        raise ExpireError("days must be a positive integer")

    expires_at = _now().replace(microsecond=0)
    from datetime import timedelta
    expires_at = expires_at + timedelta(days=days)

    entry = {
        "vault": str(vault),
        "expires_at": expires_at.isoformat(),
        "days": days,
    }
    expiry_path(vault).write_text(json.dumps(entry, indent=2))
    return entry


def load_expiry(vault: Path) -> dict | None:
    """Return the expiry entry for *vault*, or None if not set."""
    p = expiry_path(vault)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise ExpireError(f"corrupt expiry file: {exc}") from exc


def check_expiry(vault: Path) -> tuple[bool, str]:
    """Return (expired, message). Raises ExpireError on missing vault."""
    if not vault.exists():
        raise ExpireError(f"vault not found: {vault}")
    entry = load_expiry(vault)
    if entry is None:
        return False, "no expiry set"
    expires_at = datetime.fromisoformat(entry["expires_at"])
    if _now() >= expires_at:
        return True, f"expired at {expires_at.isoformat()}"
    return False, f"valid until {expires_at.isoformat()}"


def clear_expiry(vault: Path) -> bool:
    """Remove expiry metadata. Returns True if a file was deleted."""
    p = expiry_path(vault)
    if p.exists():
        p.unlink()
        return True
    return False
