"""Tests for envault.access."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.access import (
    AccessError,
    access_path,
    load_access,
    add_access,
    remove_access,
    check_access,
)

VALID_KEY = "age1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqs"
VALID_KEY2 = "age1abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef"


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"data")
    return v


def test_access_path_uses_suffix(tmp_path):
    v = tmp_path / "my.vault"
    assert access_path(v).name == "my.vault.access.json"


def test_load_access_raises_when_vault_missing(tmp_path):
    with pytest.raises(AccessError, match="Vault not found"):
        load_access(tmp_path / "ghost.vault")


def test_load_access_returns_empty_when_no_file(tmp_path):
    v = _make_vault(tmp_path)
    assert load_access(v) == []


def test_load_access_raises_on_corrupt_file(tmp_path):
    v = _make_vault(tmp_path)
    access_path(v).write_text("not json")
    with pytest.raises(AccessError, match="Corrupt"):
        load_access(v)


def test_load_access_raises_when_not_list(tmp_path):
    v = _make_vault(tmp_path)
    access_path(v).write_text(json.dumps({"key": "val"}))
    with pytest.raises(AccessError, match="JSON array"):
        load_access(v)


def test_add_access_creates_file(tmp_path):
    v = _make_vault(tmp_path)
    keys = add_access(v, VALID_KEY)
    assert VALID_KEY in keys
    assert access_path(v).exists()


def test_add_access_raises_on_invalid_key(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(AccessError, match="Invalid public key"):
        add_access(v, "notakey")


def test_add_access_deduplicates(tmp_path):
    v = _make_vault(tmp_path)
    add_access(v, VALID_KEY)
    keys = add_access(v, VALID_KEY)
    assert keys.count(VALID_KEY) == 1


def test_remove_access_removes_key(tmp_path):
    v = _make_vault(tmp_path)
    add_access(v, VALID_KEY)
    keys = remove_access(v, VALID_KEY)
    assert VALID_KEY not in keys


def test_remove_access_raises_when_key_missing(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(AccessError, match="not in access list"):
        remove_access(v, VALID_KEY)


def test_check_access_true_when_no_list(tmp_path):
    v = _make_vault(tmp_path)
    assert check_access(v, VALID_KEY) is True


def test_check_access_true_for_allowed_key(tmp_path):
    v = _make_vault(tmp_path)
    add_access(v, VALID_KEY)
    assert check_access(v, VALID_KEY) is True


def test_check_access_false_for_unlisted_key(tmp_path):
    v = _make_vault(tmp_path)
    add_access(v, VALID_KEY)
    assert check_access(v, VALID_KEY2) is False
