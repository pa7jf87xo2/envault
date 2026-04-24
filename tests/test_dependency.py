"""Tests for envault.dependency."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.dependency import (
    DependencyError,
    add_dependency,
    clear_dependencies,
    dependency_path,
    load_dependencies,
    remove_dependency,
)


def _make_vault(tmp_path: Path, name: str = "test.vault") -> Path:
    v = tmp_path / name
    v.write_bytes(b"fake-vault")
    return v


def test_dependency_path_uses_suffix(tmp_path: Path) -> None:
    v = tmp_path / "my.vault"
    assert dependency_path(v) == tmp_path / "my.deps.json"


def test_load_dependencies_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(DependencyError, match="vault not found"):
        load_dependencies(tmp_path / "ghost.vault")


def test_load_dependencies_returns_empty_when_no_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    assert load_dependencies(v) == []


def test_load_dependencies_raises_on_corrupt_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    dependency_path(v).write_text("not-json")
    with pytest.raises(DependencyError, match="corrupt"):
        load_dependencies(v)


def test_load_dependencies_raises_when_not_list(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    dependency_path(v).write_text(json.dumps({"key": "val"}))
    with pytest.raises(DependencyError, match="JSON array"):
        load_dependencies(v)


def test_add_dependency_creates_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    deps = add_dependency(v, "other.vault")
    assert deps == ["other.vault"]
    assert dependency_path(v).exists()


def test_add_dependency_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(DependencyError, match="vault not found"):
        add_dependency(tmp_path / "ghost.vault", "x.vault")


def test_add_dependency_raises_on_empty_string(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    with pytest.raises(DependencyError, match="empty"):
        add_dependency(v, "   ")


def test_add_dependency_is_idempotent(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    add_dependency(v, "a.vault")
    deps = add_dependency(v, "a.vault")
    assert deps.count("a.vault") == 1


def test_remove_dependency_removes_entry(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    add_dependency(v, "a.vault")
    add_dependency(v, "b.vault")
    deps = remove_dependency(v, "a.vault")
    assert "a.vault" not in deps
    assert "b.vault" in deps


def test_remove_dependency_raises_when_not_present(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    with pytest.raises(DependencyError, match="not found"):
        remove_dependency(v, "missing.vault")


def test_clear_dependencies_removes_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    add_dependency(v, "a.vault")
    clear_dependencies(v)
    assert not dependency_path(v).exists()


def test_clear_dependencies_noop_when_no_file(tmp_path: Path) -> None:
    v = _make_vault(tmp_path)
    clear_dependencies(v)  # should not raise
