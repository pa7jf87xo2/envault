"""Tests for envault.tag."""
import json
import pytest
from pathlib import Path
from envault.tag import (
    TagError, tags_path, load_tags, add_tag, remove_tag, list_tags,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "secrets.vault"
    v.write_bytes(b"dummy")
    return v


def test_tags_path_uses_suffix(tmp_path):
    v = tmp_path / "my.vault"
    assert tags_path(v) == tmp_path / "my.vault.tags.json"


def test_load_tags_raises_when_vault_missing(tmp_path):
    with pytest.raises(TagError, match="Vault not found"):
        load_tags(tmp_path / "missing.vault")


def test_load_tags_returns_empty_when_no_tags_file(tmp_path):
    v = _make_vault(tmp_path)
    assert load_tags(v) == []


def test_load_tags_raises_on_corrupt_file(tmp_path):
    v = _make_vault(tmp_path)
    tags_path(v).write_text("not json")
    with pytest.raises(TagError, match="Corrupt"):
        load_tags(v)


def test_load_tags_raises_when_not_list(tmp_path):
    v = _make_vault(tmp_path)
    tags_path(v).write_text(json.dumps({"a": 1}))
    with pytest.raises(TagError, match="array"):
        load_tags(v)


def test_add_tag_creates_tags_file(tmp_path):
    v = _make_vault(tmp_path)
    result = add_tag(v, "production")
    assert result == ["production"]
    assert tags_path(v).exists()


def test_add_tag_is_idempotent(tmp_path):
    v = _make_vault(tmp_path)
    add_tag(v, "staging")
    result = add_tag(v, "staging")
    assert result.count("staging") == 1


def test_add_tag_raises_on_empty_tag(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(TagError, match="empty"):
        add_tag(v, "  ")


def test_add_multiple_tags(tmp_path):
    v = _make_vault(tmp_path)
    add_tag(v, "alpha")
    add_tag(v, "beta")
    assert load_tags(v) == ["alpha", "beta"]


def test_remove_tag_removes_existing(tmp_path):
    v = _make_vault(tmp_path)
    add_tag(v, "old")
    result = remove_tag(v, "old")
    assert "old" not in result


def test_remove_tag_raises_when_not_present(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(TagError, match="not found"):
        remove_tag(v, "ghost")


def test_list_tags_returns_all(tmp_path):
    v = _make_vault(tmp_path)
    add_tag(v, "x")
    add_tag(v, "y")
    assert list_tags(v) == ["x", "y"]
