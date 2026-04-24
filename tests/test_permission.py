"""Tests for envault.permission."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.permission import (
    PermissionError,
    check_permission,
    load_permissions,
    permission_path,
    remove_permission,
    set_permission,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"dummy")
    return v


# ---------------------------------------------------------------------------
# permission_path
# ---------------------------------------------------------------------------

def test_permission_path_uses_suffix(tmp_path):
    v = tmp_path / "my.vault"
    assert permission_path(v) == tmp_path / "my.permissions.json"


# ---------------------------------------------------------------------------
# load_permissions
# ---------------------------------------------------------------------------

def test_load_permissions_raises_when_vault_missing(tmp_path):
    with pytest.raises(PermissionError, match="vault not found"):
        load_permissions(tmp_path / "ghost.vault")


def test_load_permissions_returns_empty_when_no_file(tmp_path):
    v = _make_vault(tmp_path)
    assert load_permissions(v) == {}


def test_load_permissions_raises_on_corrupt_file(tmp_path):
    v = _make_vault(tmp_path)
    permission_path(v).write_text("not json")
    with pytest.raises(PermissionError, match="corrupt"):
        load_permissions(v)


# ---------------------------------------------------------------------------
# set_permission
# ---------------------------------------------------------------------------

def test_set_permission_creates_sidecar(tmp_path):
    v = _make_vault(tmp_path)
    set_permission(v, "age1abc", "read")
    assert permission_path(v).exists()


def test_set_permission_returns_mapping(tmp_path):
    v = _make_vault(tmp_path)
    result = set_permission(v, "age1abc", "write")
    assert result == {"age1abc": "write"}


def test_set_permission_raises_on_invalid_role(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(PermissionError, match="invalid role"):
        set_permission(v, "age1abc", "superuser")


def test_set_permission_raises_on_empty_identity(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(PermissionError, match="identity must not be empty"):
        set_permission(v, "  ", "read")


def test_set_permission_overwrites_existing(tmp_path):
    v = _make_vault(tmp_path)
    set_permission(v, "age1abc", "read")
    result = set_permission(v, "age1abc", "admin")
    assert result["age1abc"] == "admin"


# ---------------------------------------------------------------------------
# remove_permission
# ---------------------------------------------------------------------------

def test_remove_permission_deletes_identity(tmp_path):
    v = _make_vault(tmp_path)
    set_permission(v, "age1abc", "read")
    result = remove_permission(v, "age1abc")
    assert "age1abc" not in result


def test_remove_permission_raises_when_not_found(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(PermissionError, match="identity not found"):
        remove_permission(v, "age1xyz")


# ---------------------------------------------------------------------------
# check_permission
# ---------------------------------------------------------------------------

def test_check_permission_returns_false_for_unknown_identity(tmp_path):
    v = _make_vault(tmp_path)
    assert check_permission(v, "age1xyz", "read") is False


def test_check_permission_exact_role(tmp_path):
    v = _make_vault(tmp_path)
    set_permission(v, "age1abc", "write")
    assert check_permission(v, "age1abc", "write") is True


def test_check_permission_higher_role_satisfies_lower(tmp_path):
    v = _make_vault(tmp_path)
    set_permission(v, "age1abc", "admin")
    assert check_permission(v, "age1abc", "read") is True


def test_check_permission_lower_role_fails_higher(tmp_path):
    v = _make_vault(tmp_path)
    set_permission(v, "age1abc", "read")
    assert check_permission(v, "age1abc", "write") is False


def test_check_permission_raises_on_unknown_required_role(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(PermissionError, match="unknown role"):
        check_permission(v, "age1abc", "owner")
