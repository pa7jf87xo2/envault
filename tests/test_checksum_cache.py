"""Tests for envault.checksum_cache."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.checksum_cache import (
    ChecksumCacheError,
    cache_path,
    clear_checksum,
    has_changed,
    load_checksum,
    save_checksum,
)


def _make_vault(tmp_path: Path, content: bytes = b"SECRET=abc\n") -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(content)
    return v


# ---------------------------------------------------------------------------
# cache_path
# ---------------------------------------------------------------------------

def test_cache_path_uses_suffix(tmp_path: Path) -> None:
    v = tmp_path / "my.vault"
    assert cache_path(v) == tmp_path / "my.checksum"


# ---------------------------------------------------------------------------
# save_checksum
# ---------------------------------------------------------------------------

def test_save_checksum_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(ChecksumCacheError, match="vault not found"):
        save_checksum(tmp_path / "missing.vault")


def test_save_checksum_creates_cache_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    save_checksum(v)
    assert cache_path(v).exists()


def test_save_checksum_returns_hex_digest(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    digest = save_checksum(v)
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_save_checksum_cache_contains_sha256(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    digest = save_checksum(v)
    data = json.loads(cache_path(v).read_text())
    assert data["sha256"] == digest


# ---------------------------------------------------------------------------
# load_checksum
# ---------------------------------------------------------------------------

def test_load_checksum_raises_when_no_cache(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    with pytest.raises(ChecksumCacheError, match="no checksum cache"):
        load_checksum(v)


def test_load_checksum_raises_on_corrupt_cache(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    cache_path(v).write_text("not-json", encoding="utf-8")
    with pytest.raises(ChecksumCacheError, match="corrupt"):
        load_checksum(v)


def test_load_checksum_returns_saved_digest(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    digest = save_checksum(v)
    assert load_checksum(v) == digest


# ---------------------------------------------------------------------------
# has_changed
# ---------------------------------------------------------------------------

def test_has_changed_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(ChecksumCacheError, match="vault not found"):
        has_changed(tmp_path / "missing.vault")


def test_has_changed_true_when_no_cache(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    assert has_changed(v) is True


def test_has_changed_false_after_save(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    save_checksum(v)
    assert has_changed(v) is False


def test_has_changed_true_after_modification(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    save_checksum(v)
    v.write_bytes(b"SECRET=xyz\n")
    assert has_changed(v) is True


# ---------------------------------------------------------------------------
# clear_checksum
# ---------------------------------------------------------------------------

def test_clear_checksum_removes_cache_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    save_checksum(v)
    assert clear_checksum(v) is True
    assert not cache_path(v).exists()


def test_clear_checksum_returns_false_when_no_cache(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    assert clear_checksum(v) is False
