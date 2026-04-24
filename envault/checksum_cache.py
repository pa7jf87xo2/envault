"""Checksum cache — persist and compare vault checksums to detect changes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


class ChecksumCacheError(Exception):
    """Raised when checksum cache operations fail."""


def cache_path(vault: Path) -> Path:
    """Return the sidecar cache file path for *vault*."""
    return vault.with_suffix(".checksum")


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of *path*."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def save_checksum(vault: Path) -> str:
    """Compute and persist the checksum of *vault*.

    Returns the hex digest that was saved.
    Raises ChecksumCacheError if the vault file does not exist.
    """
    if not vault.exists():
        raise ChecksumCacheError(f"vault not found: {vault}")
    digest = _sha256(vault)
    entry = {"vault": str(vault), "sha256": digest}
    cache_path(vault).write_text(json.dumps(entry) + "\n", encoding="utf-8")
    return digest


def load_checksum(vault: Path) -> str:
    """Load the previously saved checksum for *vault*.

    Raises ChecksumCacheError if the cache file is missing or corrupt.
    """
    cp = cache_path(vault)
    if not cp.exists():
        raise ChecksumCacheError(f"no checksum cache for: {vault}")
    try:
        data = json.loads(cp.read_text(encoding="utf-8"))
        return data["sha256"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise ChecksumCacheError(f"corrupt checksum cache: {cp}") from exc


def has_changed(vault: Path) -> bool:
    """Return True if *vault* differs from its cached checksum.

    Returns True when no cache exists yet (treat as changed).
    Raises ChecksumCacheError if the vault file does not exist.
    """
    if not vault.exists():
        raise ChecksumCacheError(f"vault not found: {vault}")
    try:
        cached = load_checksum(vault)
    except ChecksumCacheError:
        return True
    return _sha256(vault) != cached


def clear_checksum(vault: Path) -> bool:
    """Remove the checksum cache for *vault*.

    Returns True if a cache file was deleted, False if none existed.
    """
    cp = cache_path(vault)
    if cp.exists():
        cp.unlink()
        return True
    return False
