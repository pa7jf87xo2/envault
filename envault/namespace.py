"""Namespace support for envault vaults.

Allows tagging a vault with a logical namespace (e.g. 'production', 'staging')
so multiple vaults can be organised and referenced by name.
"""
from __future__ import annotations

import json
from pathlib import Path

NAMESPACE_SUFFIX = ".namespace.json"


class NamespaceError(Exception):
    """Raised when a namespace operation fails."""


def namespace_path(vault: Path) -> Path:
    """Return the namespace sidecar path for *vault*."""
    return vault.with_suffix("").with_suffix(NAMESPACE_SUFFIX)


def load_namespace(vault: Path) -> str | None:
    """Return the namespace string for *vault*, or ``None`` if unset.

    Raises :class:`NamespaceError` if *vault* does not exist or the
    sidecar file is corrupt.
    """
    if not vault.exists():
        raise NamespaceError(f"vault not found: {vault}")
    ns_file = namespace_path(vault)
    if not ns_file.exists():
        return None
    try:
        data = json.loads(ns_file.read_text())
        return data["namespace"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise NamespaceError(f"corrupt namespace file: {ns_file}") from exc


def set_namespace(vault: Path, namespace: str) -> str:
    """Assign *namespace* to *vault* and return the namespace string.

    Raises :class:`NamespaceError` if *vault* does not exist or
    *namespace* is empty / contains whitespace.
    """
    if not vault.exists():
        raise NamespaceError(f"vault not found: {vault}")
    namespace = namespace.strip()
    if not namespace:
        raise NamespaceError("namespace must not be empty")
    if any(c.isspace() for c in namespace):
        raise NamespaceError("namespace must not contain whitespace")
    ns_file = namespace_path(vault)
    ns_file.write_text(json.dumps({"namespace": namespace}))
    return namespace


def clear_namespace(vault: Path) -> None:
    """Remove the namespace sidecar for *vault* if present.

    Raises :class:`NamespaceError` if *vault* does not exist.
    """
    if not vault.exists():
        raise NamespaceError(f"vault not found: {vault}")
    ns_file = namespace_path(vault)
    if ns_file.exists():
        ns_file.unlink()
