"""Tests for envault.metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.metadata import (
    MetadataError,
    clear_metadata,
    load_metadata,
    metadata_path,
    remove_metadata,
    set_metadata,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"dummy")
    return v


def test_metadata_path_uses_suffix(tmp_path: Path) -> None:
    v = tmp_path / "my.vault"
    assert metadata_path(v) == tmp_path / "my.vault.meta.json"


def test_load_metadata_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(MetadataError, match="vault not found"):
        load_metadata(tmp_path / "ghost.vault")


def test_load_metadata_returns_empty_when_no_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    assert load_metadata(v) == {}


def test_load_metadata_raises_on_corrupt_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    metadata_path(v).write_text("not json{{{")
    with pytest.raises(MetadataError, match="corrupt"):
        load_metadata(v)


def test_set_metadata_creates_sidecar(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    set_metadata(v, "env", "production")
    assert metadata_path(v).exists()


def test_set_metadata_returns_full_dict(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    result = set_metadata(v, "owner", "alice")
    assert result == {"owner": "alice"}


def test_set_metadata_accumulates_keys(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    set_metadata(v, "a", 1)
    result = set_metadata(v, "b", 2)
    assert result == {"a": 1, "b": 2}


def test_set_metadata_overwrites_existing_key(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    set_metadata(v, "env", "staging")
    result = set_metadata(v, "env", "production")
    assert result["env"] == "production"


def test_set_metadata_raises_on_empty_key(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    with pytest.raises(MetadataError, match="non-empty string"):
        set_metadata(v, "", "value")


def test_remove_metadata_deletes_key(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    set_metadata(v, "x", 42)
    result = remove_metadata(v, "x")
    assert "x" not in result


def test_remove_metadata_raises_when_key_missing(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    with pytest.raises(MetadataError, match="key not found"):
        remove_metadata(v, "nonexistent")


def test_clear_metadata_removes_sidecar(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    set_metadata(v, "k", "v")
    clear_metadata(v)
    assert not metadata_path(v).exists()


def test_clear_metadata_noop_when_no_sidecar(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    clear_metadata(v)  # should not raise


def test_clear_metadata_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(MetadataError, match="vault not found"):
        clear_metadata(tmp_path / "ghost.vault")


def test_sidecar_is_valid_json(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    set_metadata(v, "key", {"nested": True})
    raw = metadata_path(v).read_text()
    parsed = json.loads(raw)
    assert parsed["key"] == {"nested": True}
