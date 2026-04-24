"""Tests for envault.label."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.label import (
    LabelError,
    clear_label,
    label_path,
    load_label,
    set_label,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "secrets.vault"
    v.write_bytes(b"dummy")
    return v


# ---------------------------------------------------------------------------
# label_path
# ---------------------------------------------------------------------------

def test_label_path_uses_suffix(tmp_path: Path):
    v = tmp_path / "my.vault"
    assert label_path(v) == tmp_path / "my.vault.label.json"


# ---------------------------------------------------------------------------
# set_label
# ---------------------------------------------------------------------------

def test_set_label_raises_when_vault_missing(tmp_path: Path):
    with pytest.raises(LabelError, match="Vault not found"):
        set_label(tmp_path / "missing.vault", "prod")


def test_set_label_creates_sidecar(tmp_path: Path):
    v = _make_vault(tmp_path)
    set_label(v, "production")
    assert label_path(v).exists()


def test_set_label_returns_entry(tmp_path: Path):
    v = _make_vault(tmp_path)
    entry = set_label(v, "staging")
    assert entry["label"] == "staging"
    assert "vault" in entry


def test_set_label_strips_whitespace(tmp_path: Path):
    v = _make_vault(tmp_path)
    entry = set_label(v, "  dev  ")
    assert entry["label"] == "dev"


def test_set_label_raises_on_empty(tmp_path: Path):
    v = _make_vault(tmp_path)
    with pytest.raises(LabelError, match="empty or blank"):
        set_label(v, "   ")


def test_set_label_raises_on_too_long(tmp_path: Path):
    v = _make_vault(tmp_path)
    with pytest.raises(LabelError, match="maximum length"):
        set_label(v, "x" * 129)


def test_set_label_raises_on_invalid_chars(tmp_path: Path):
    v = _make_vault(tmp_path)
    with pytest.raises(LabelError, match="invalid characters"):
        set_label(v, "bad/label")


# ---------------------------------------------------------------------------
# load_label
# ---------------------------------------------------------------------------

def test_load_label_raises_when_vault_missing(tmp_path: Path):
    with pytest.raises(LabelError, match="Vault not found"):
        load_label(tmp_path / "missing.vault")


def test_load_label_returns_none_when_no_file(tmp_path: Path):
    v = _make_vault(tmp_path)
    assert load_label(v) is None


def test_load_label_returns_set_value(tmp_path: Path):
    v = _make_vault(tmp_path)
    set_label(v, "my-label")
    assert load_label(v) == "my-label"


def test_load_label_raises_on_corrupt_file(tmp_path: Path):
    v = _make_vault(tmp_path)
    label_path(v).write_text("not json")
    with pytest.raises(LabelError, match="Corrupt"):
        load_label(v)


# ---------------------------------------------------------------------------
# clear_label
# ---------------------------------------------------------------------------

def test_clear_label_raises_when_vault_missing(tmp_path: Path):
    with pytest.raises(LabelError, match="Vault not found"):
        clear_label(tmp_path / "missing.vault")


def test_clear_label_returns_false_when_no_file(tmp_path: Path):
    v = _make_vault(tmp_path)
    assert clear_label(v) is False


def test_clear_label_removes_sidecar(tmp_path: Path):
    v = _make_vault(tmp_path)
    set_label(v, "to-remove")
    result = clear_label(v)
    assert result is True
    assert not label_path(v).exists()


def test_clear_label_makes_load_return_none(tmp_path: Path):
    v = _make_vault(tmp_path)
    set_label(v, "temp")
    clear_label(v)
    assert load_label(v) is None
