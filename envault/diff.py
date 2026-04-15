"""Diff support: compare a decrypted vault snapshot against a live .env file."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import List, Tuple

from envault.vault import unpack


class DiffError(Exception):
    """Raised when a diff operation fails."""


def _read_lines(path: Path) -> List[str]:
    """Return lines from *path*, each terminated with a newline."""
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def diff_vault(
    vault_path: Path,
    live_path: Path,
    identity_path: Path,
    *,
    context: int = 3,
) -> Tuple[bool, str]:
    """Decrypt *vault_path* into a temp location and unified-diff it against *live_path*.

    Returns ``(changed, unified_diff_text)``.
    Raises :class:`DiffError` if either file cannot be read or decrypted.
    """
    if not vault_path.exists():
        raise DiffError(f"Vault file not found: {vault_path}")
    if not live_path.exists():
        raise DiffError(f"Live .env file not found: {live_path}")

    import tempfile

    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_env = Path(tmp) / ".env"
            unpack(vault_path, tmp_env, identity_path)
            vault_lines = _read_lines(tmp_env)
    except Exception as exc:  # pragma: no cover
        raise DiffError(f"Failed to decrypt vault: {exc}") from exc

    live_lines = _read_lines(live_path)

    diff_lines = list(
        difflib.unified_diff(
            vault_lines,
            live_lines,
            fromfile=f"vault:{vault_path.name}",
            tofile=f"live:{live_path.name}",
            n=context,
        )
    )

    changed = bool(diff_lines)
    return changed, "".join(diff_lines)


def summarise_diff(unified_diff: str) -> Tuple[int, int]:
    """Return ``(additions, deletions)`` line counts from a unified diff string."""
    additions = sum(1 for l in unified_diff.splitlines() if l.startswith("+") and not l.startswith("+++ "))
    deletions = sum(1 for l in unified_diff.splitlines() if l.startswith("-") and not l.startswith("--- "))
    return additions, deletions
