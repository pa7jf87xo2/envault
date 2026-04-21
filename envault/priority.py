"""envault.priority — Assign and query priority levels for vault files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

VALID_LEVELS = ("low", "normal", "high", "critical")
DEFAULT_LEVEL = "normal"


class PriorityError(Exception):
    """Raised when a priority operation fails."""


def priority_path(vault: Path) -> Path:
    """Return the sidecar file path for *vault*'s priority metadata."""
    return vault.with_suffix(".priority.json")


def set_priority(vault: Path, level: str) -> dict:
    """Persist *level* as the priority for *vault*.

    Returns the stored entry ``{"vault": ..., "level": ...}``.
    Raises :class:`PriorityError` if *vault* does not exist or *level* is invalid.
    """
    if not vault.exists():
        raise PriorityError(f"vault not found: {vault}")
    if level not in VALID_LEVELS:
        raise PriorityError(
            f"invalid priority level {level!r}; choose from {VALID_LEVELS}"
        )
    entry = {"vault": str(vault), "level": level}
    priority_path(vault).write_text(json.dumps(entry))
    return entry


def load_priority(vault: Path) -> Optional[str]:
    """Return the stored priority level for *vault*, or ``None`` if unset.

    Raises :class:`PriorityError` if *vault* does not exist or the sidecar
    file is corrupt.
    """
    if not vault.exists():
        raise PriorityError(f"vault not found: {vault}")
    p = priority_path(vault)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        return data["level"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise PriorityError(f"corrupt priority file: {p}") from exc


def clear_priority(vault: Path) -> bool:
    """Remove the priority sidecar for *vault*.

    Returns ``True`` if a file was removed, ``False`` if there was nothing to
    remove.  Raises :class:`PriorityError` if *vault* does not exist.
    """
    if not vault.exists():
        raise PriorityError(f"vault not found: {vault}")
    p = priority_path(vault)
    if p.exists():
        p.unlink()
        return True
    return False
