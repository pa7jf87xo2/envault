"""Tests for envault.namespace."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.namespace import (
    NamespaceError,
    clear_namespace,
    load_namespace,
    namespace_path,
    set_namespace,
)


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "secrets.vault"
    vault.write_bytes(b"dummy")
    return vault


# ---------------------------------------------------------------------------
# namespace_path
# ---------------------------------------------------------------------------

def test_namespace_path_uses_suffix(tmp_path: Path) -> None:
    vault = tmp_path / "secrets.vault"
    ns = namespace_path(vault)
    assert ns.name == "secrets.namespace.json"
    assert ns.parent == tmp_path


# ---------------------------------------------------------------------------
# load_namespace
# ---------------------------------------------------------------------------

def test_load_namespace_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(NamespaceError, match="vault not found"):
        load_namespace(tmp_path / "missing.vault")


def test_load_namespace_returns_none_when_no_file(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    assert load_namespace(vault) is None


def test_load_namespace_returns_set_value(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    ns_file = namespace_path(vault)
    ns_file.write_text(json.dumps({"namespace": "production"}))
    assert load_namespace(vault) == "production"


def test_load_namespace_raises_on_corrupt_file(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    namespace_path(vault).write_text("not-json{{")
    with pytest.raises(NamespaceError, match="corrupt"):
        load_namespace(vault)


def test_load_namespace_raises_on_missing_key(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    namespace_path(vault).write_text(json.dumps({"other": "value"}))
    with pytest.raises(NamespaceError, match="corrupt"):
        load_namespace(vault)


# ---------------------------------------------------------------------------
# set_namespace
# ---------------------------------------------------------------------------

def test_set_namespace_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(NamespaceError, match="vault not found"):
        set_namespace(tmp_path / "missing.vault", "staging")


def test_set_namespace_creates_sidecar(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    set_namespace(vault, "staging")
    assert namespace_path(vault).exists()


def test_set_namespace_returns_namespace(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    result = set_namespace(vault, "staging")
    assert result == "staging"


def test_set_namespace_persists_value(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    set_namespace(vault, "production")
    assert load_namespace(vault) == "production"


def test_set_namespace_raises_on_empty(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with pytest.raises(NamespaceError, match="empty"):
        set_namespace(vault, "   ")


def test_set_namespace_raises_on_whitespace(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with pytest.raises(NamespaceError, match="whitespace"):
        set_namespace(vault, "my namespace")


# ---------------------------------------------------------------------------
# clear_namespace
# ---------------------------------------------------------------------------

def test_clear_namespace_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(NamespaceError, match="vault not found"):
        clear_namespace(tmp_path / "missing.vault")


def test_clear_namespace_removes_sidecar(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    set_namespace(vault, "staging")
    clear_namespace(vault)
    assert not namespace_path(vault).exists()


def test_clear_namespace_noop_when_not_set(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    clear_namespace(vault)  # should not raise
    assert not namespace_path(vault).exists()
