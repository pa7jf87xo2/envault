"""envault.permission – per-vault permission rules sidecar.

Stores a simple mapping of {identity: role} where role is one of
'read', 'write', or 'admin'.  The sidecar is a JSON file stored
alongside the vault.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

VALID_ROLES = {"read", "write", "admin"}


class PermissionError(Exception):  # noqa: A001
    """Raised when a permission operation fails."""


def permission_path(vault: Path) -> Path:
    """Return the sidecar path for *vault*."""
    return vault.with_suffix(".permissions.json")


def _load_raw(vault: Path) -> Dict[str, str]:
    if not vault.exists():
        raise PermissionError(f"vault not found: {vault}")
    p = permission_path(vault)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise PermissionError(f"corrupt permissions file: {exc}") from exc
    if not isinstance(data, dict):
        raise PermissionError("permissions file must contain a JSON object")
    return data


def load_permissions(vault: Path) -> Dict[str, str]:
    """Return the {identity: role} mapping for *vault*."""
    return _load_raw(vault)


def set_permission(vault: Path, identity: str, role: str) -> Dict[str, str]:
    """Grant *identity* the given *role* on *vault*.

    Returns the updated mapping.
    """
    if not identity.strip():
        raise PermissionError("identity must not be empty")
    if role not in VALID_ROLES:
        raise PermissionError(
            f"invalid role {role!r}; must be one of {sorted(VALID_ROLES)}"
        )
    data = _load_raw(vault)
    data[identity] = role
    permission_path(vault).write_text(json.dumps(data, indent=2))
    return data


def remove_permission(vault: Path, identity: str) -> Dict[str, str]:
    """Remove *identity* from the permission list for *vault*.

    Returns the updated mapping.  Raises :class:`PermissionError` if the
    identity is not present.
    """
    data = _load_raw(vault)
    if identity not in data:
        raise PermissionError(f"identity not found: {identity}")
    del data[identity]
    permission_path(vault).write_text(json.dumps(data, indent=2))
    return data


def check_permission(vault: Path, identity: str, required_role: str) -> bool:
    """Return True if *identity* holds at least *required_role* on *vault*.

    Role hierarchy: read < write < admin.
    """
    hierarchy = ["read", "write", "admin"]
    if required_role not in hierarchy:
        raise PermissionError(f"unknown role: {required_role!r}")
    data = _load_raw(vault)
    actual = data.get(identity)
    if actual is None:
        return False
    return hierarchy.index(actual) >= hierarchy.index(required_role)
