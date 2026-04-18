"""Vault alias management — short names that map to vault paths."""
from __future__ import annotations

import json
from pathlib import Path


class AliasError(Exception):
    pass


def alias_path(vault: Path) -> Path:
    return vault.with_suffix(".aliases.json")


def load_aliases(vault: Path) -> dict[str, str]:
    if not vault.exists():
        raise AliasError(f"vault not found: {vault}")
    p = alias_path(vault)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise AliasError(f"corrupt aliases file: {exc}") from exc
    if not isinstance(data, dict):
        raise AliasError("aliases file must contain a JSON object")
    return data


def set_alias(vault: Path, name: str, target: str) -> dict[str, str]:
    """Add or update *name* -> *target* in the alias map."""
    if not name.strip():
        raise AliasError("alias name must not be empty")
    if not target.strip():
        raise AliasError("alias target must not be empty")
    aliases = load_aliases(vault)
    aliases[name] = target
    alias_path(vault).write_text(json.dumps(aliases, indent=2))
    return aliases


def remove_alias(vault: Path, name: str) -> dict[str, str]:
    aliases = load_aliases(vault)
    if name not in aliases:
        raise AliasError(f"alias not found: {name!r}")
    del aliases[name]
    alias_path(vault).write_text(json.dumps(aliases, indent=2))
    return aliases


def resolve_alias(vault: Path, name: str) -> str:
    """Return the target for *name*, raising AliasError if absent."""
    aliases = load_aliases(vault)
    if name not in aliases:
        raise AliasError(f"alias not found: {name!r}")
    return aliases[name]
