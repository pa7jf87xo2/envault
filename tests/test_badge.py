"""Tests for envault.badge."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.badge import (
    BadgeError,
    generate_badge,
    write_badge,
    _color_for_status,
    _label_for_status,
)
from envault.status import StatusError


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"fake")
    return v


def _fake_status(locked=False, expired=False, expires_at=None):
    st = MagicMock()
    st.locked = locked
    st.expired = expired
    st.expires_at = expires_at
    return st


# ---------------------------------------------------------------------------
# _color_for_status
# ---------------------------------------------------------------------------

def test_color_expired_is_red():
    assert _color_for_status(locked=False, expired=True, has_expiry=True) == "red"


def test_color_locked_is_orange():
    assert _color_for_status(locked=True, expired=False, has_expiry=False) == "orange"


def test_color_has_expiry_is_yellow():
    assert _color_for_status(locked=False, expired=False, has_expiry=True) == "yellow"


def test_color_active_is_brightgreen():
    assert _color_for_status(locked=False, expired=False, has_expiry=False) == "brightgreen"


# ---------------------------------------------------------------------------
# _label_for_status
# ---------------------------------------------------------------------------

def test_label_expired():
    assert _label_for_status(locked=False, expired=True) == "expired"


def test_label_locked():
    assert _label_for_status(locked=True, expired=False) == "locked"


def test_label_active():
    assert _label_for_status(locked=False, expired=False) == "active"


# ---------------------------------------------------------------------------
# generate_badge
# ---------------------------------------------------------------------------

def test_generate_badge_active(tmp_path):
    vault = _make_vault(tmp_path)
    identity = tmp_path / "key.txt"
    identity.write_text("key")

    with patch("envault.badge.get_status", return_value=_fake_status()) as _mock:
        badge = generate_badge(vault, identity)

    assert badge["schemaVersion"] == 1
    assert badge["label"] == "envault"
    assert badge["message"] == "active"
    assert badge["color"] == "brightgreen"


def test_generate_badge_locked(tmp_path):
    vault = _make_vault(tmp_path)
    identity = tmp_path / "key.txt"
    identity.write_text("key")

    with patch("envault.badge.get_status", return_value=_fake_status(locked=True)):
        badge = generate_badge(vault, identity)

    assert badge["message"] == "locked"
    assert badge["color"] == "orange"


def test_generate_badge_raises_on_status_error(tmp_path):
    vault = _make_vault(tmp_path)
    identity = tmp_path / "key.txt"
    identity.write_text("key")

    with patch("envault.badge.get_status", side_effect=StatusError("boom")):
        with pytest.raises(BadgeError, match="boom"):
            generate_badge(vault, identity)


# ---------------------------------------------------------------------------
# write_badge
# ---------------------------------------------------------------------------

def test_write_badge_creates_file(tmp_path):
    vault = _make_vault(tmp_path)
    identity = tmp_path / "key.txt"
    identity.write_text("key")
    dest = tmp_path / "badges" / "status.json"

    with patch("envault.badge.get_status", return_value=_fake_status()):
        result = write_badge(vault, identity, dest)

    assert result == dest
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert data["message"] == "active"


def test_write_badge_creates_parent_dirs(tmp_path):
    vault = _make_vault(tmp_path)
    identity = tmp_path / "key.txt"
    identity.write_text("key")
    dest = tmp_path / "a" / "b" / "c" / "badge.json"

    with patch("envault.badge.get_status", return_value=_fake_status()):
        write_badge(vault, identity, dest)

    assert dest.exists()
