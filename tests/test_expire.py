"""Tests for envault.expire."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.expire import (
    ExpireError,
    check_expiry,
    clear_expiry,
    expiry_path,
    load_expiry,
    set_expiry,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"fake-vault")
    return v


def test_expiry_path_uses_suffix(tmp_path):
    v = tmp_path / "my.vault"
    assert expiry_path(v).name == "my.vault.expiry.json"


def test_set_expiry_raises_when_vault_missing(tmp_path):
    with pytest.raises(ExpireError, match="vault not found"):
        set_expiry(tmp_path / "ghost.vault", days=7)


def test_set_expiry_raises_on_zero_days(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(ExpireError, match="positive"):
        set_expiry(v, days=0)


def test_set_expiry_creates_file(tmp_path):
    v = _make_vault(tmp_path)
    set_expiry(v, days=5)
    assert expiry_path(v).exists()


def test_set_expiry_returns_entry(tmp_path):
    v = _make_vault(tmp_path)
    entry = set_expiry(v, days=3)
    assert entry["days"] == 3
    assert "expires_at" in entry
    assert str(v) in entry["vault"]


def test_load_expiry_returns_none_when_no_file(tmp_path):
    v = _make_vault(tmp_path)
    assert load_expiry(v) is None


def test_load_expiry_raises_on_corrupt_file(tmp_path):
    v = _make_vault(tmp_path)
    expiry_path(v).write_text("not-json")
    with pytest.raises(ExpireError, match="corrupt"):
        load_expiry(v)


def test_check_expiry_no_expiry_set(tmp_path):
    v = _make_vault(tmp_path)
    expired, msg = check_expiry(v)
    assert not expired
    assert "no expiry" in msg


def test_check_expiry_not_yet_expired(tmp_path):
    v = _make_vault(tmp_path)
    set_expiry(v, days=10)
    expired, msg = check_expiry(v)
    assert not expired
    assert "valid until" in msg


def test_check_expiry_detects_expired(tmp_path):
    v = _make_vault(tmp_path)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).replace(microsecond=0)
    entry = {"vault": str(v), "expires_at": past.isoformat(), "days": 1}
    expiry_path(v).write_text(json.dumps(entry))
    expired, msg = check_expiry(v)
    assert expired
    assert "expired at" in msg


def test_check_expiry_raises_when_vault_missing(tmp_path):
    with pytest.raises(ExpireError, match="vault not found"):
        check_expiry(tmp_path / "gone.vault")


def test_clear_expiry_removes_file(tmp_path):
    v = _make_vault(tmp_path)
    set_expiry(v, days=7)
    assert clear_expiry(v) is True
    assert not expiry_path(v).exists()


def test_clear_expiry_returns_false_when_no_file(tmp_path):
    v = _make_vault(tmp_path)
    assert clear_expiry(v) is False
