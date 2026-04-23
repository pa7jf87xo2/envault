"""Profile management for envault.

Allows named configuration profiles (e.g. 'dev', 'staging', 'prod') to be
associated with a vault, making it easy to switch between environments.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class ProfileError(Exception):
    """Raised when a profile operation fails."""


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def profile_path(vault: Path) -> Path:
    """Return the sidecar file that stores profile data for *vault*."""
    return vault.with_suffix(".profiles.json")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_raw(vault: Path) -> Dict[str, dict]:
    """Load raw profile mapping from disk, returning an empty dict if absent."""
    if not vault.exists():
        raise ProfileError(f"Vault not found: {vault}")
    path = profile_path(vault)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise ValueError("root must be a JSON object")
        return data
    except (json.JSONDecodeError, ValueError) as exc:
        raise ProfileError(f"Corrupt profiles file {path}: {exc}") from exc


def _save_raw(vault: Path, data: Dict[str, dict]) -> None:
    """Persist *data* to the sidecar file."""
    profile_path(vault).write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_profiles(vault: Path) -> Dict[str, dict]:
    """Return all profiles associated with *vault*.

    Each profile is a dict that may contain arbitrary metadata such as
    ``recipient``, ``remote``, or ``description``.

    Raises :class:`ProfileError` if the vault is missing or the sidecar is
    corrupt.
    """
    return _load_raw(vault)


def set_profile(
    vault: Path,
    name: str,
    *,
    recipient: Optional[str] = None,
    remote: Optional[str] = None,
    description: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    """Create or update a named profile for *vault*.

    Returns the stored profile dict.

    Raises :class:`ProfileError` if the vault is missing or *name* is empty.
    """
    name = name.strip()
    if not name:
        raise ProfileError("Profile name must not be empty.")

    data = _load_raw(vault)
    profile: dict = data.get(name, {})

    if recipient is not None:
        profile["recipient"] = recipient
    if remote is not None:
        profile["remote"] = remote
    if description is not None:
        profile["description"] = description
    if extra:
        profile.update(extra)

    data[name] = profile
    _save_raw(vault, data)
    return profile


def get_profile(vault: Path, name: str) -> dict:
    """Return the profile dict for *name*.

    Raises :class:`ProfileError` if the profile does not exist.
    """
    data = _load_raw(vault)
    if name not in data:
        raise ProfileError(f"Profile '{name}' not found.")
    return data[name]


def remove_profile(vault: Path, name: str) -> None:
    """Delete the profile *name* from *vault*.

    Raises :class:`ProfileError` if the profile does not exist.
    """
    data = _load_raw(vault)
    if name not in data:
        raise ProfileError(f"Profile '{name}' not found.")
    del data[name]
    _save_raw(vault, data)


def list_profiles(vault: Path) -> List[str]:
    """Return a sorted list of profile names for *vault*."""
    return sorted(_load_raw(vault).keys())
