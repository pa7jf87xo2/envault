"""Vault metadata: attach arbitrary key/value annotations to a vault file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MetadataError(Exception):
    """Raised when a metadata operation fails."""


def metadata_path(vault: Path) -> Path:
    """Return the sidecar path for *vault*'s metadata."""
    return vault.with_suffix(vault.suffix + ".meta.json")


def load_metadata(vault: Path) -> dict[str, Any]:
    """Return the metadata dict for *vault*.

    Returns an empty dict when no metadata file exists yet.
    Raises :class:`MetadataError` if *vault* itself is missing or the
    sidecar is corrupt.
    """
    if not vault.exists():
        raise MetadataError(f"vault not found: {vault}")
    path = metadata_path(vault)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise MetadataError(f"corrupt metadata file: {exc}") from exc


def set_metadata(vault: Path, key: str, value: Any) -> dict[str, Any]:
    """Set *key* to *value* in *vault*'s metadata and persist it.

    Returns the full (updated) metadata dict.
    """
    if not key or not isinstance(key, str):
        raise MetadataError("key must be a non-empty string")
    data = load_metadata(vault)
    data[key] = value
    metadata_path(vault).write_text(json.dumps(data, indent=2))
    return data


def remove_metadata(vault: Path, key: str) -> dict[str, Any]:
    """Remove *key* from *vault*'s metadata.

    Raises :class:`MetadataError` if the key does not exist.
    Returns the updated metadata dict.
    """
    data = load_metadata(vault)
    if key not in data:
        raise MetadataError(f"key not found in metadata: {key!r}")
    del data[key]
    metadata_path(vault).write_text(json.dumps(data, indent=2))
    return data


def clear_metadata(vault: Path) -> None:
    """Delete the metadata sidecar for *vault* if it exists."""
    if not vault.exists():
        raise MetadataError(f"vault not found: {vault}")
    path = metadata_path(vault)
    if path.exists():
        path.unlink()
