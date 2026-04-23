"""Tests for envault.retention."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.retention import (
    RetentionError,
    clear_retention,
    is_stale,
    load_retention,
    retention_path,
    set_retention,
)


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "secrets.env.age"
    vault.write_bytes(b"encrypted")
    return vault


# ---------------------------------------------------------------------------
# retention_path
# ---------------------------------------------------------------------------

def test_retention_path_uses_suffix(tmp_path: Path) -> None:
    vault = tmp_path / "my.env.age"
    assert retention_path(vault).name == "my.env.retention.json"


# ---------------------------------------------------------------------------
# set_retention
# ---------------------------------------------------------------------------

def test_set_retention_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(RetentionError, match="Vault not found"):
        set_retention(tmp_path / "ghost.age", days=30)


def test_set_retention_raises_on_zero_days(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with pytest.raises(RetentionError, match="positive"):
        set_retention(vault, days=0)


def test_set_retention_raises_on_negative_days(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with pytest.raises(RetentionError, match="positive"):
        set_retention(vault, days=-5)


def test_set_retention_creates_sidecar(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    set_retention(vault, days=14)
    assert retention_path(vault).exists()


def test_set_retention_returns_policy(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    policy = set_retention(vault, days=7)
    assert policy["days"] == 7
    assert "set_at" in policy
    assert "expires_at" in policy


def test_set_retention_stores_max_snapshots(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    policy = set_retention(vault, days=30, max_snapshots=5)
    assert policy["max_snapshots"] == 5


def test_set_retention_raises_on_invalid_max_snapshots(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with pytest.raises(RetentionError, match="max_snapshots"):
        set_retention(vault, days=30, max_snapshots=0)


# ---------------------------------------------------------------------------
# load_retention
# ---------------------------------------------------------------------------

def test_load_retention_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(RetentionError, match="Vault not found"):
        load_retention(tmp_path / "ghost.age")


def test_load_retention_returns_none_when_no_sidecar(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    assert load_retention(vault) is None


def test_load_retention_returns_policy(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    set_retention(vault, days=10)
    policy = load_retention(vault)
    assert policy is not None
    assert policy["days"] == 10


def test_load_retention_raises_on_corrupt_file(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    retention_path(vault).write_text("not json")
    with pytest.raises(RetentionError, match="Corrupt"):
        load_retention(vault)


# ---------------------------------------------------------------------------
# is_stale
# ---------------------------------------------------------------------------

def test_is_stale_returns_false_when_no_policy(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    assert is_stale(vault) is False


def test_is_stale_returns_false_within_period(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    set_retention(vault, days=30)
    assert is_stale(vault) is False


def test_is_stale_returns_true_when_expired(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    past = datetime.now(tz=timezone.utc) - timedelta(days=1)
    policy = {
        "days": 30,
        "set_at": (past - timedelta(days=30)).isoformat(),
        "expires_at": past.isoformat(),
    }
    retention_path(vault).write_text(json.dumps(policy))
    assert is_stale(vault) is True


# ---------------------------------------------------------------------------
# clear_retention
# ---------------------------------------------------------------------------

def test_clear_retention_removes_sidecar(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    set_retention(vault, days=7)
    clear_retention(vault)
    assert not retention_path(vault).exists()


def test_clear_retention_is_idempotent(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    clear_retention(vault)  # no sidecar — should not raise


def test_clear_retention_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(RetentionError, match="Vault not found"):
        clear_retention(tmp_path / "ghost.age")
