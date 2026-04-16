"""Tests for envault.pin."""
import json
import pytest
from pathlib import Path
from envault.pin import (
    PinError,
    pin_path,
    pin,
    load_pin,
    clear_pin,
    is_pinned,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "secrets.env.age"
    v.write_bytes(b"data")
    return v


def test_pin_path_uses_suffix(tmp_path):
    v = tmp_path / "secrets.env.age"
    assert pin_path(v).name == "secrets.env.age.pin.json"


def test_pin_raises_when_vault_missing(tmp_path):
    v = tmp_path / "missing.age"
    with pytest.raises(PinError, match="vault not found"):
        pin(v, "snap", "abc123")


def test_pin_creates_pin_file(tmp_path):
    v = _make_vault(tmp_path)
    pin(v, "snap-1", "deadbeef")
    assert pin_path(v).exists()


def test_pin_returns_entry(tmp_path):
    v = _make_vault(tmp_path)
    entry = pin(v, "snap-1", "deadbeef")
    assert entry["snapshot"] == "snap-1"
    assert entry["checksum"] == "deadbeef"


def test_load_pin_raises_when_missing(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(PinError, match="no pin found"):
        load_pin(v)


def test_load_pin_returns_data(tmp_path):
    v = _make_vault(tmp_path)
    pin(v, "snap-2", "cafebabe")
    data = load_pin(v)
    assert data["snapshot"] == "snap-2"
    assert data["checksum"] == "cafebabe"


def test_load_pin_raises_on_corrupt(tmp_path):
    v = _make_vault(tmp_path)
    pin_path(v).write_text("not json")
    with pytest.raises(PinError, match="corrupt"):
        load_pin(v)


def test_clear_pin_removes_file(tmp_path):
    v = _make_vault(tmp_path)
    pin(v, "snap-3", "ff")
    clear_pin(v)
    assert not pin_path(v).exists()


def test_clear_pin_raises_when_missing(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(PinError, match="no pin found"):
        clear_pin(v)


def test_is_pinned_false_when_no_pin(tmp_path):
    v = _make_vault(tmp_path)
    assert not is_pinned(v)


def test_is_pinned_true_after_pin(tmp_path):
    v = _make_vault(tmp_path)
    pin(v, "snap-4", "00")
    assert is_pinned(v)
