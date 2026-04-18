"""Tests for envault.alias."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.alias import (
    AliasError,
    alias_path,
    load_aliases,
    set_alias,
    remove_alias,
    resolve_alias,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"data")
    return v


def test_alias_path_uses_suffix(tmp_path):
    v = tmp_path / "my.vault"
    assert alias_path(v) == tmp_path / "my.aliases.json"


def test_load_aliases_raises_when_vault_missing(tmp_path):
    with pytest.raises(AliasError, match="vault not found"):
        load_aliases(tmp_path / "missing.vault")


def test_load_aliases_returns_empty_when_no_file(tmp_path):
    v = _make_vault(tmp_path)
    assert load_aliases(v) == {}


def test_load_aliases_raises_on_corrupt_file(tmp_path):
    v = _make_vault(tmp_path)
    alias_path(v).write_text("not json")
    with pytest.raises(AliasError, match="corrupt"):
        load_aliases(v)


def test_load_aliases_raises_when_not_dict(tmp_path):
    v = _make_vault(tmp_path)
    alias_path(v).write_text(json.dumps(["a", "b"]))
    with pytest.raises(AliasError, match="JSON object"):
        load_aliases(v)


def test_set_alias_creates_file(tmp_path):
    v = _make_vault(tmp_path)
    result = set_alias(v, "prod", "/envs/prod.vault")
    assert result["prod"] == "/envs/prod.vault"
    assert alias_path(v).exists()


def test_set_alias_updates_existing(tmp_path):
    v = _make_vault(tmp_path)
    set_alias(v, "prod", "/envs/prod.vault")
    result = set_alias(v, "prod", "/envs/prod2.vault")
    assert result["prod"] == "/envs/prod2.vault"
    assert len(result) == 1


def test_set_alias_raises_on_empty_name(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(AliasError, match="name must not be empty"):
        set_alias(v, "  ", "target")


def test_set_alias_raises_on_empty_target(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(AliasError, match="target must not be empty"):
        set_alias(v, "prod", "")


def test_remove_alias_deletes_entry(tmp_path):
    v = _make_vault(tmp_path)
    set_alias(v, "prod", "/envs/prod.vault")
    result = remove_alias(v, "prod")
    assert "prod" not in result


def test_remove_alias_raises_when_missing(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(AliasError, match="alias not found"):
        remove_alias(v, "ghost")


def test_resolve_alias_returns_target(tmp_path):
    v = _make_vault(tmp_path)
    set_alias(v, "staging", "/envs/staging.vault")
    assert resolve_alias(v, "staging") == "/envs/staging.vault"


def test_resolve_alias_raises_when_missing(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(AliasError, match="alias not found"):
        resolve_alias(v, "nope")
