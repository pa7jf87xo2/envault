"""Tests for envault.status."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.status import StatusError, VaultStatus, get_status


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_vault(tmp_path: Path, content: bytes = b"encrypted") -> Path:
    v = tmp_path / "secrets.vault"
    v.write_bytes(content)
    return v


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_get_status_raises_when_vault_missing(tmp_path):
    with pytest.raises(StatusError, match="vault not found"):
        get_status(tmp_path / "missing.vault")


def test_get_status_returns_vault_status(tmp_path):
    v = _make_vault(tmp_path)
    with (
        patch("envault.status.is_locked", return_value=False),
        patch("envault.status.load_pin", return_value=None),
        patch("envault.status.load_tags", return_value=[]),
        patch("envault.status.expiry_path", return_value=tmp_path / "no.expiry"),
    ):
        s = get_status(v)
    assert isinstance(s, VaultStatus)
    assert s.exists is True
    assert s.vault == v


def test_get_status_reports_size(tmp_path):
    payload = b"x" * 42
    v = _make_vault(tmp_path, payload)
    with (
        patch("envault.status.is_locked", return_value=False),
        patch("envault.status.load_pin", return_value=None),
        patch("envault.status.load_tags", return_value=[]),
        patch("envault.status.expiry_path", return_value=tmp_path / "no.expiry"),
    ):
        s = get_status(v)
    assert s.size_bytes == 42


def test_get_status_reports_locked(tmp_path):
    v = _make_vault(tmp_path)
    with (
        patch("envault.status.is_locked", return_value=True),
        patch("envault.status.load_pin", return_value=None),
        patch("envault.status.load_tags", return_value=[]),
        patch("envault.status.expiry_path", return_value=tmp_path / "no.expiry"),
    ):
        s = get_status(v)
    assert s.locked is True


def test_get_status_reports_tags(tmp_path):
    v = _make_vault(tmp_path)
    with (
        patch("envault.status.is_locked", return_value=False),
        patch("envault.status.load_pin", return_value=None),
        patch("envault.status.load_tags", return_value=["prod", "v2"]),
        patch("envault.status.expiry_path", return_value=tmp_path / "no.expiry"),
    ):
        s = get_status(v)
    assert s.tags == ["prod", "v2"]


def test_get_status_reports_expiry(tmp_path):
    v = _make_vault(tmp_path)
    expiry_file = tmp_path / "secrets.vault.expiry"
    expiry_file.write_text("{}")  # existence triggers expiry branch
    with (
        patch("envault.status.is_locked", return_value=False),
        patch("envault.status.load_pin", return_value=None),
        patch("envault.status.load_tags", return_value=[]),
        patch("envault.status.expiry_path", return_value=expiry_file),
        patch(
            "envault.status.load_expiry",
            return_value={"expires_at": "2099-01-01", "expired": False},
        ),
    ):
        s = get_status(v)
    assert s.expiry_date == "2099-01-01"
    assert s.expired is False


def test_vault_status_as_dict(tmp_path):
    v = _make_vault(tmp_path)
    s = VaultStatus(
        vault=v,
        exists=True,
        size_bytes=10,
        locked=False,
        pinned_version="abc123",
        tags=["staging"],
        expired=False,
        expiry_date="2099-06-01",
    )
    d = s.as_dict()
    assert d["locked"] is False
    assert d["pinned_version"] == "abc123"
    assert d["tags"] == ["staging"]
    assert d["expiry_date"] == "2099-06-01"
