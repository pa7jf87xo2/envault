"""Vault label management — attach a human-readable label to a vault file."""

from __future__ import annotations

import json
from pathlib import Path


class LabelError(Exception):
    """Raised when a label operation fails."""


MAX_LABEL_LENGTH = 128
_ALLOWED_CHARS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.:()"
)


def label_path(vault: Path) -> Path:
    """Return the sidecar path for *vault*'s label."""
    return vault.with_suffix(vault.suffix + ".label.json")


def _validate_label(label: str) -> None:
    if not label or not label.strip():
        raise LabelError("Label must not be empty or blank.")
    if len(label) > MAX_LABEL_LENGTH:
        raise LabelError(
            f"Label exceeds maximum length of {MAX_LABEL_LENGTH} characters."
        )
    bad = set(label) - _ALLOWED_CHARS
    if bad:
        raise LabelError(f"Label contains invalid characters: {sorted(bad)}")


def set_label(vault: Path, label: str) -> dict:
    """Attach *label* to *vault*, creating or overwriting the sidecar file."""
    if not vault.exists():
        raise LabelError(f"Vault not found: {vault}")
    _validate_label(label)
    entry = {"vault": str(vault), "label": label.strip()}
    label_path(vault).write_text(json.dumps(entry, indent=2) + "\n")
    return entry


def load_label(vault: Path) -> str | None:
    """Return the label for *vault*, or *None* if no label has been set."""
    if not vault.exists():
        raise LabelError(f"Vault not found: {vault}")
    lp = label_path(vault)
    if not lp.exists():
        return None
    try:
        data = json.loads(lp.read_text())
    except json.JSONDecodeError as exc:
        raise LabelError(f"Corrupt label file: {lp}") from exc
    return data.get("label")


def clear_label(vault: Path) -> bool:
    """Remove the label sidecar for *vault*.  Returns True if it existed."""
    if not vault.exists():
        raise LabelError(f"Vault not found: {vault}")
    lp = label_path(vault)
    if lp.exists():
        lp.unlink()
        return True
    return False
