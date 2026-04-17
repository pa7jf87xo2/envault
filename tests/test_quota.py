"""Tests for envault.quota."""
from pathlib import Path
import pytest
from envault.quota import (
    QuotaError,
    quota_path,
    set_quota,
    load_quota,
    check_quota,
    clear_quota,
    DEFAULT_MAX_BYTES,
)


def _make_vault(tmp_path: Path, size: int = 10) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"x" * size)
    return v


def test_quota_path_uses_suffix(tmp_path):
    v = tmp_path / "my.vault"
    assert quota_path(v) == tmp_path / "my.quota.json"


def test_set_quota_raises_when_vault_missing(tmp_path):
    with pytest.raises(QuotaError, match="vault not found"):
        set_quota(tmp_path / "missing.vault", 1024)


def test_set_quota_raises_on_non_positive(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(QuotaError, match="positive"):
        set_quota(v, 0)


def test_set_quota_creates_file(tmp_path):
    v = _make_vault(tmp_path)
    set_quota(v, 2048)
    assert quota_path(v).exists()


def test_set_quota_returns_entry(tmp_path):
    v = _make_vault(tmp_path)
    entry = set_quota(v, 512)
    assert entry["max_bytes"] == 512


def test_load_quota_returns_none_when_missing(tmp_path):
    v = _make_vault(tmp_path)
    assert load_quota(v) is None


def test_load_quota_returns_stored_value(tmp_path):
    v = _make_vault(tmp_path)
    set_quota(v, 4096)
    q = load_quota(v)
    assert q["max_bytes"] == 4096


def test_load_quota_raises_on_corrupt_file(tmp_path):
    v = _make_vault(tmp_path)
    quota_path(v).write_text("not-json")
    with pytest.raises(QuotaError, match="corrupt"):
        load_quota(v)


def test_check_quota_ok(tmp_path):
    v = _make_vault(tmp_path, size=10)
    set_quota(v, 100)
    result = check_quota(v)
    assert result["ok"] is True
    assert result["size"] == 10


def test_check_quota_raises_when_exceeded(tmp_path):
    v = _make_vault(tmp_path, size=200)
    set_quota(v, 100)
    with pytest.raises(QuotaError, match="exceeds quota"):
        check_quota(v)


def test_check_quota_uses_default_when_no_quota_set(tmp_path):
    v = _make_vault(tmp_path, size=10)
    result = check_quota(v)
    assert result["max_bytes"] == DEFAULT_MAX_BYTES


def test_check_quota_raises_when_vault_missing(tmp_path):
    with pytest.raises(QuotaError, match="vault not found"):
        check_quota(tmp_path / "ghost.vault")


def test_clear_quota_removes_file(tmp_path):
    v = _make_vault(tmp_path)
    set_quota(v, 1024)
    clear_quota(v)
    assert not quota_path(v).exists()


def test_clear_quota_noop_when_not_set(tmp_path):
    v = _make_vault(tmp_path)
    clear_quota(v)  # should not raise
