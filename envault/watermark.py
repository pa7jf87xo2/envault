"""Watermark support — embed and read a provenance marker in a vault sidecar."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

WATERMARK_SUFFIX = ".watermark.json"


class WatermarkError(Exception):
    """Raised when a watermark operation fails."""


def watermark_path(vault: Path) -> Path:
    """Return the sidecar path for *vault*."""
    return vault.with_suffix(WATERMARK_SUFFIX)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def set_watermark(
    vault: Path,
    author: str,
    machine: str | None = None,
    note: str | None = None,
) -> dict:
    """Write a watermark sidecar next to *vault* and return the entry."""
    if not vault.exists():
        raise WatermarkError(f"vault not found: {vault}")
    if not author.strip():
        raise WatermarkError("author must not be empty")

    entry: dict = {
        "author": author.strip(),
        "stamped_at": _now_iso(),
    }
    if machine is not None:
        entry["machine"] = machine.strip()
    if note is not None:
        entry["note"] = note.strip()

    wpath = watermark_path(vault)
    wpath.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return entry


def load_watermark(vault: Path) -> dict | None:
    """Return the watermark dict for *vault*, or ``None`` if absent."""
    if not vault.exists():
        raise WatermarkError(f"vault not found: {vault}")

    wpath = watermark_path(vault)
    if not wpath.exists():
        return None

    try:
        return json.loads(wpath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WatermarkError(f"corrupt watermark file: {exc}") from exc


def clear_watermark(vault: Path) -> bool:
    """Remove the watermark sidecar.  Returns True if a file was deleted."""
    if not vault.exists():
        raise WatermarkError(f"vault not found: {vault}")

    wpath = watermark_path(vault)
    if wpath.exists():
        wpath.unlink()
        return True
    return False
