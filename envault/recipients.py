"""Manage trusted public-key recipients for multi-user vault sharing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

RECIPIENTS_FILENAME = ".envault-recipients"
_AGE_PUBKEY_RE = re.compile(r"^age1[a-z0-9]{58}$")


class RecipientsError(Exception):
    """Raised when a recipients operation fails."""


def _validate_key(key: str) -> str:
    key = key.strip()
    if not _AGE_PUBKEY_RE.match(key):
        raise RecipientsError(f"Invalid age public key: {key!r}")
    return key


def recipients_path(directory: Path | str = ".") -> Path:
    """Return the canonical recipients file path for *directory*."""
    return Path(directory) / RECIPIENTS_FILENAME


def load_recipients(path: Path) -> List[str]:
    """Return the list of public keys stored in *path*."""
    if not path.exists():
        raise RecipientsError(f"Recipients file not found: {path}")
    keys: List[str] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        keys.append(_validate_key(line))
    return keys


def add_recipient(path: Path, public_key: str) -> None:
    """Append *public_key* to the recipients file, creating it if absent."""
    public_key = _validate_key(public_key)
    existing: List[str] = []
    if path.exists():
        existing = load_recipients(path)
    if public_key in existing:
        raise RecipientsError(f"Recipient already present: {public_key}")
    with path.open("a") as fh:
        fh.write(public_key + "\n")


def remove_recipient(path: Path, public_key: str) -> None:
    """Remove *public_key* from the recipients file."""
    public_key = _validate_key(public_key)
    if not path.exists():
        raise RecipientsError(f"Recipients file not found: {path}")
    existing = load_recipients(path)
    if public_key not in existing:
        raise RecipientsError(f"Recipient not found: {public_key}")
    updated = [k for k in existing if k != public_key]
    path.write_text("\n".join(updated) + ("\n" if updated else ""))
