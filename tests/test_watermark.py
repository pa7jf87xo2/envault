"""Tests for envault.watermark."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.watermark import (
    WatermarkError,
    watermark_path,
    set_watermark,
    load_watermark,
    clear_watermark,
    WATERMARK_SUFFIX,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "secrets.vault"
    v.write_bytes(b"dummy")
    return v


# ---------------------------------------------------------------------------
# watermark_path
# ---------------------------------------------------------------------------

def test_watermark_path_uses_suffix(tmp_path):
    v = tmp_path / "my.vault"
    wp = watermark_path(v)
    assert wp.name.endswith(WATERMARK_SUFFIX)
    assert wp.parent == tmp_path


# ---------------------------------------------------------------------------
# set_watermark
# ---------------------------------------------------------------------------

def test_set_watermark_raises_when_vault_missing(tmp_path):
    with pytest.raises(WatermarkError, match="vault not found"):
        set_watermark(tmp_path / "ghost.vault", author="alice")


def test_set_watermark_raises_on_empty_author(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(WatermarkError, match="author must not be empty"):
        set_watermark(v, author="   ")


def test_set_watermark_creates_sidecar(tmp_path):
    v = _make_vault(tmp_path)
    set_watermark(v, author="alice")
    assert watermark_path(v).exists()


def test_set_watermark_returns_entry(tmp_path):
    v = _make_vault(tmp_path)
    entry = set_watermark(v, author="bob", machine="laptop", note="initial")
    assert entry["author"] == "bob"
    assert entry["machine"] == "laptop"
    assert entry["note"] == "initial"
    assert "stamped_at" in entry


def test_set_watermark_omits_none_fields(tmp_path):
    v = _make_vault(tmp_path)
    entry = set_watermark(v, author="carol")
    assert "machine" not in entry
    assert "note" not in entry


def test_set_watermark_overwrites_existing(tmp_path):
    v = _make_vault(tmp_path)
    set_watermark(v, author="alice")
    set_watermark(v, author="bob")
    data = json.loads(watermark_path(v).read_text())
    assert data["author"] == "bob"


# ---------------------------------------------------------------------------
# load_watermark
# ---------------------------------------------------------------------------

def test_load_watermark_raises_when_vault_missing(tmp_path):
    with pytest.raises(WatermarkError, match="vault not found"):
        load_watermark(tmp_path / "ghost.vault")


def test_load_watermark_returns_none_when_no_sidecar(tmp_path):
    v = _make_vault(tmp_path)
    assert load_watermark(v) is None


def test_load_watermark_returns_dict(tmp_path):
    v = _make_vault(tmp_path)
    set_watermark(v, author="dave", machine="ci")
    wm = load_watermark(v)
    assert wm is not None
    assert wm["author"] == "dave"
    assert wm["machine"] == "ci"


def test_load_watermark_raises_on_corrupt_file(tmp_path):
    v = _make_vault(tmp_path)
    watermark_path(v).write_text("not-json", encoding="utf-8")
    with pytest.raises(WatermarkError, match="corrupt watermark"):
        load_watermark(v)


# ---------------------------------------------------------------------------
# clear_watermark
# ---------------------------------------------------------------------------

def test_clear_watermark_raises_when_vault_missing(tmp_path):
    with pytest.raises(WatermarkError, match="vault not found"):
        clear_watermark(tmp_path / "ghost.vault")


def test_clear_watermark_returns_false_when_no_sidecar(tmp_path):
    v = _make_vault(tmp_path)
    assert clear_watermark(v) is False


def test_clear_watermark_deletes_sidecar(tmp_path):
    v = _make_vault(tmp_path)
    set_watermark(v, author="eve")
    result = clear_watermark(v)
    assert result is True
    assert not watermark_path(v).exists()
