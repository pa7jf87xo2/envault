"""Verify the integrity and authenticity of a vault file."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from envault.vault import unpack


class VerifyError(Exception):
    """Raised when vault verification fails."""


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_env_keys(env_text: str) -> list[str]:
    """Extract variable names from a .env-formatted string.

    Skips blank lines and comment lines (starting with ``#``).
    """
    keys = []
    for line in env_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            keys.append(stripped.split("=", 1)[0].strip())
    return keys


def checksum(vault_path: Path) -> str:
    """Return the SHA-256 checksum of *vault_path*.

    Raises
    ------
    VerifyError
        If the vault file does not exist.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise VerifyError(f"Vault not found: {vault_path}")
    return _sha256(vault_path)


def verify(vault_path: Path, identity_path: Path) -> dict:
    """Verify that *vault_path* can be decrypted with *identity_path*.

    Returns a result dict with keys:
      - ``ok`` (bool)
      - ``checksum`` (str) – SHA-256 of the vault file
      - ``keys`` (list[str]) – variable names found in the decrypted env
      - ``error`` (str | None) – error message when ``ok`` is False

    Raises
    ------
    VerifyError
        If the vault or identity file does not exist.
    """
    vault_path = Path(vault_path)
    identity_path = Path(identity_path)

    if not vault_path.exists():
        raise VerifyError(f"Vault not found: {vault_path}")
    if not identity_path.exists():
        raise VerifyError(f"Identity file not found: {identity_path}")

    digest = _sha256(vault_path)

    try:
        env_text = unpack(vault_path, identity_path)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "checksum": digest, "keys": [], "error": str(exc)}

    keys = _parse_env_keys(env_text)

    return {"ok": True, "checksum": digest, "keys": keys, "error": None}
