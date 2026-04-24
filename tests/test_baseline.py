"""Tests for envault.baseline."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.baseline import (
    BaselineError,
    baseline_path,
    diff_baseline,
    load_baseline,
    save_baseline,
)


def _make_vault(tmp_path: Path, name: str = "test.vault") -> Path:
    p = tmp_path / name
    p.write_bytes(b"dummy-encrypted-content")
    return p


_IDENTITY = Path("/fake/identity.txt")
_ENV_TEXT = "DB_HOST=localhost\nDB_PASS=secret\n# comment\n\nAPI_KEY=abc123\n"


# ---------------------------------------------------------------------------
# baseline_path
# ---------------------------------------------------------------------------

def test_baseline_path_uses_suffix(tmp_path: Path) -> None:
    vault = tmp_path / "prod.vault"
    assert baseline_path(vault) == tmp_path / "prod.baseline.json"


# ---------------------------------------------------------------------------
# save_baseline
# ---------------------------------------------------------------------------

def test_save_baseline_raises_when_vault_missing(tmp_path: Path) -> None:
    vault = tmp_path / "missing.vault"
    with pytest.raises(BaselineError, match="Vault not found"):
        save_baseline(vault, _IDENTITY)


def test_save_baseline_raises_on_decrypt_failure(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.baseline.unpack", side_effect=RuntimeError("bad key")):
        with pytest.raises(BaselineError, match="Failed to decrypt vault"):
            save_baseline(vault, _IDENTITY)


def test_save_baseline_creates_file(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.baseline.unpack", return_value=_ENV_TEXT):
        dest = save_baseline(vault, _IDENTITY)
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert "keys" in data
    assert "DB_HOST" in data["keys"]
    assert "API_KEY" in data["keys"]


def test_save_baseline_skips_comments_and_blanks(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.baseline.unpack", return_value=_ENV_TEXT):
        dest = save_baseline(vault, _IDENTITY)
    data = json.loads(dest.read_text())
    assert all(not k.startswith("#") for k in data["keys"])


def test_save_baseline_custom_output_path(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    out = tmp_path / "custom.json"
    with patch("envault.baseline.unpack", return_value=_ENV_TEXT):
        dest = save_baseline(vault, _IDENTITY, out=out)
    assert dest == out
    assert out.exists()


# ---------------------------------------------------------------------------
# load_baseline
# ---------------------------------------------------------------------------

def test_load_baseline_raises_when_missing(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with pytest.raises(BaselineError, match="No baseline found"):
        load_baseline(vault)


def test_load_baseline_raises_on_corrupt_file(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    baseline_path(vault).write_text("not-json")
    with pytest.raises(BaselineError, match="Corrupt baseline file"):
        load_baseline(vault)


def test_load_baseline_returns_key_hashes(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.baseline.unpack", return_value=_ENV_TEXT):
        save_baseline(vault, _IDENTITY)
    keys = load_baseline(vault)
    assert isinstance(keys, dict)
    assert "DB_HOST" in keys and len(keys["DB_HOST"]) == 64  # sha256 hex


# ---------------------------------------------------------------------------
# diff_baseline
# ---------------------------------------------------------------------------

def test_diff_baseline_raises_when_no_baseline(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with pytest.raises(BaselineError, match="No baseline found"):
        diff_baseline(vault, _IDENTITY)


def test_diff_baseline_no_changes(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.baseline.unpack", return_value=_ENV_TEXT):
        save_baseline(vault, _IDENTITY)
        result = diff_baseline(vault, _IDENTITY)
    assert result == {"added": [], "removed": [], "changed": []}


def test_diff_baseline_detects_added_key(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.baseline.unpack", return_value=_ENV_TEXT):
        save_baseline(vault, _IDENTITY)
    new_text = _ENV_TEXT + "NEW_KEY=newvalue\n"
    with patch("envault.baseline.unpack", return_value=new_text):
        result = diff_baseline(vault, _IDENTITY)
    assert "NEW_KEY" in result["added"]


def test_diff_baseline_detects_removed_key(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.baseline.unpack", return_value=_ENV_TEXT):
        save_baseline(vault, _IDENTITY)
    trimmed = "DB_HOST=localhost\n"
    with patch("envault.baseline.unpack", return_value=trimmed):
        result = diff_baseline(vault, _IDENTITY)
    assert "API_KEY" in result["removed"]
    assert "DB_PASS" in result["removed"]


def test_diff_baseline_detects_changed_value(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.baseline.unpack", return_value=_ENV_TEXT):
        save_baseline(vault, _IDENTITY)
    changed = _ENV_TEXT.replace("DB_PASS=secret", "DB_PASS=newsecret")
    with patch("envault.baseline.unpack", return_value=changed):
        result = diff_baseline(vault, _IDENTITY)
    assert "DB_PASS" in result["changed"]
