"""Search for keys across decrypted vault contents without writing to disk."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, NamedTuple, Optional

from envault.vault import unpack, VaultError


class SearchError(Exception):
    """Raised when a search operation fails."""


class SearchMatch(NamedTuple):
    line_number: int
    key: str
    value: str
    raw: str


def _parse_env_line(line: str) -> Optional[tuple[str, str]]:
    """Return (key, value) for a valid KEY=VALUE line, else None."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if "=" not in stripped:
        return None
    key, _, value = stripped.partition("=")
    return key.strip(), value.strip()


def search_vault(
    vault_path: Path,
    pattern: str,
    identity_path: Path,
    *,
    keys_only: bool = False,
    ignore_case: bool = False,
) -> List[SearchMatch]:
    """Decrypt *vault_path* in-memory and return lines matching *pattern*.

    Parameters
    ----------
    vault_path:    Path to the ``.vault`` file.
    pattern:       Regular-expression pattern to search for.
    identity_path: Age identity file used for decryption.
    keys_only:     When True only the key portion of each line is searched.
    ignore_case:   When True the match is case-insensitive.
    """
    if not vault_path.exists():
        raise SearchError(f"Vault not found: {vault_path}")

    try:
        env_text = unpack(vault_path, identity_path, dest=None, return_text=True)
    except VaultError as exc:
        raise SearchError(f"Failed to decrypt vault: {exc}") from exc

    flags = re.IGNORECASE if ignore_case else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as exc:
        raise SearchError(f"Invalid search pattern: {exc}") from exc

    matches: List[SearchMatch] = []
    for lineno, raw in enumerate(env_text.splitlines(), start=1):
        parsed = _parse_env_line(raw)
        if parsed is None:
            continue
        key, value = parsed
        haystack = key if keys_only else raw
        if regex.search(haystack):
            matches.append(SearchMatch(line_number=lineno, key=key, value=value, raw=raw))

    return matches
