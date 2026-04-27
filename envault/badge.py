"""Badge generation for vault status summaries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from envault.status import get_status, StatusError

BadgeColor = Literal["brightgreen", "green", "yellow", "orange", "red", "lightgrey"]


class BadgeError(Exception):
    """Raised when badge generation fails."""


def _color_for_status(locked: bool, expired: bool, has_expiry: bool) -> BadgeColor:
    if expired:
        return "red"
    if locked:
        return "orange"
    if has_expiry:
        return "yellow"
    return "brightgreen"


def _label_for_status(locked: bool, expired: bool) -> str:
    if expired:
        return "expired"
    if locked:
        return "locked"
    return "active"


def generate_badge(vault: Path, identity: Path) -> dict:
    """Return a shields.io-compatible badge dict for *vault*.

    Parameters
    ----------
    vault:
        Path to the ``.vault`` file.
    identity:
        Path to the age identity file used for decryption.

    Returns
    -------
    dict
        A mapping with ``schemaVersion``, ``label``, ``message`` and ``color``
        keys suitable for serialising as a shields.io endpoint JSON response.
    """
    try:
        st = get_status(vault, identity)
    except StatusError as exc:
        raise BadgeError(str(exc)) from exc

    expired = bool(st.expired)
    locked = bool(st.locked)
    has_expiry = st.expires_at is not None

    color = _color_for_status(locked, expired, has_expiry)
    message = _label_for_status(locked, expired)

    return {
        "schemaVersion": 1,
        "label": "envault",
        "message": message,
        "color": color,
    }


def write_badge(vault: Path, identity: Path, dest: Path) -> Path:
    """Write a shields.io JSON badge to *dest* and return the path."""
    badge = generate_badge(vault, identity)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(badge, indent=2) + "\n", encoding="utf-8")
    return dest
