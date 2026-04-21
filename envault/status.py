"""envault.status – summarise the overall state of a vault."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envault.expire import load_expiry, expiry_path
from envault.lock import is_locked
from envault.pin import load_pin
from envault.tag import load_tags


class StatusError(Exception):
    """Raised when status cannot be determined."""


@dataclass
class VaultStatus:
    vault: Path
    exists: bool
    size_bytes: int
    locked: bool
    pinned_version: Optional[str]
    tags: list[str] = field(default_factory=list)
    expired: Optional[bool] = None          # None = no expiry set
    expiry_date: Optional[str] = None
    extra: dict =n
    def as_dict(self) -> dict:
        return {
            "vault": str(self.vault),
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "locked": self.locked,
            "pinned_version": self.pinned_version,
            "tags": self.tags,
            "expired": self.expired,
            "expiry_date": self.expiry_date,
            **self.extra,
        }


def get_status(vault: Path) -> VaultStatus:
    """Return a :class:`VaultStatus` for *vault*.

    Raises :class:`StatusError` if *vault* does not exist.
    """
    vault = Path(vault)
    if not vault.exists():
        raise StatusError(f"vault not found: {vault}")

    size = vault.stat().st_size

    locked = is_locked(vault)

    try:
        pin_entry = load_pin(vault)
        pinned = pin_entry.get("version") if pin_entry else None
    except Exception:
        pinned = None

    try:
        tags = load_tags(vault)
    except Exception:
        tags = []

    expired: Optional[bool] = None
    expiry_date: Optional[str] = None
    if expiry_path(vault).exists():
        try:
            entry = load_expiry(vault)
            expiry_date = entry.get("expires_at")
            expired = entry.get("expired", False)
        except Exception:
            pass

    return VaultStatus(
        vault=vault,
        exists=True,
        size_bytes=size,
        locked=locked,
        pinned_version=pinned,
        tags=tags,
        expired=expired,
        expiry_date=expiry_date,
    )
