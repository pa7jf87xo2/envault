"""Access control: restrict vault operations to allowed public keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

ACCESS_SUFFIX = ".access.json"


class AccessError(Exception):
    pass


def access_path(vault: Path) -> Path:
    return vault.with_name(vault.name + ACCESS_SUFFIX)


def load_access(vault: Path) -> List[str]:
    """Return list of allowed public keys for *vault*."""
    if not vault.exists():
        raise AccessError(f"Vault not found: {vault}")
    ap = access_path(vault)
    if not ap.exists():
        return []
    try:
        data = json.loads(ap.read_text())
    except json.JSONDecodeError as exc:
        raise AccessError(f"Corrupt access file: {exc}") from exc
    if not isinstance(data, list):
        raise AccessError("Access file must contain a JSON array")
    return [str(k) for k in data]


def add_access(vault: Path, public_key: str) -> List[str]:
    """Add *public_key* to the allowed list. Returns updated list."""
    if not vault.exists():
        raise AccessError(f"Vault not found: {vault}")
    if not public_key.startswith("age"):
        raise AccessError(f"Invalid public key (must start with 'age'): {public_key}")
    keys = load_access(vault)
    if public_key in keys:
        return keys
    keys.append(public_key)
    access_path(vault).write_text(json.dumps(keys, indent=2))
    return keys


def remove_access(vault: Path, public_key: str) -> List[str]:
    """Remove *public_key* from the allowed list. Returns updated list."""
    keys = load_access(vault)
    if public_key not in keys:
        raise AccessError(f"Key not in access list: {public_key}")
    keys = [k for k in keys if k != public_key]
    access_path(vault).write_text(json.dumps(keys, indent=2))
    return keys


def check_access(vault: Path, public_key: str) -> bool:
    """Return True if *public_key* is allowed, or if no access list exists."""
    keys = load_access(vault)
    if not keys:
        return True
    return public_key in keys
