"""Pin a vault to a specific snapshot for reproducible deploys."""
from __future__ import annotations

import json
from pathlib import Path

PIN_SUFFIX = ".pin.json"


class PinError(Exception):
    pass


def pin_path(vault: Path) -> Path:
    return vault.with_name(vault.name + PIN_SUFFIX)


def pin(vault: Path, snapshot: str, checksum: str) -> dict:
    """Write a pin file recording the snapshot name and checksum."""
    if not vault.exists():
        raise PinError(f"vault not found: {vault}")
    entry = {"snapshot": snapshot, "checksum": checksum}
    pin_path(vault).write_text(json.dumps(entry, indent=2))
    return entry


def load_pin(vault: Path) -> dict:
    """Load pin metadata for a vault."""
    p = pin_path(vault)
    if not p.exists():
        raise PinError(f"no pin found for vault: {vault}")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise PinError(f"corrupt pin file: {exc}") from exc


def clear_pin(vault: Path) -> None:
    """Remove the pin file if present."""
    p = pin_path(vault)
    if not p.exists():
        raise PinError(f"no pin found for vault: {vault}")
    p.unlink()


def is_pinned(vault: Path) -> bool:
    return pin_path(vault).exists()
