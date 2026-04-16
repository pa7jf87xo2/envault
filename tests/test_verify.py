"""Tests for envault.verify."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from envault.verify import VerifyError, checksum, verify


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _fake_unpack_ok(vault_path, identity_path):
    return "API_KEY=abc123\nDB_URL=postgres://localhost/db\n# comment\n"


def _fake_unpack_fail(vault_path, identity_path):
    raise RuntimeError("decryption failed")


# ---------------------------------------------------------------------------
# checksum
# ---------------------------------------------------------------------------

def test_checksum_raises_when_vault_missing(tmp_path):
    with pytest.raises(VerifyError, match="Vault not found"):
        checksum(tmp_path / "missing.vault")


def test_checksum_returns_hex_string(tmp_path):
    vault = tmp_path / "env.vault"
    _write(vault, "some encrypted bytes")
    result = checksum(vault)
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex digest


def test_checksum_differs_for_different_content(tmp_path):
    v1 = tmp_path / "a.vault"
    v2 = tmp_path / "b.vault"
    _write(v1, "content-a")
    _write(v2, "content-b")
    assert checksum(v1) != checksum(v2)


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

def test_verify_raises_when_vault_missing(tmp_path):
    identity = tmp_path / "key.txt"
    _write(identity, "age-secret-key")
    with pytest.raises(VerifyError, match="Vault not found"):
        verify(tmp_path / "missing.vault", identity)


def test_verify_raises_when_identity_missing(tmp_path):
    vault = tmp_path / "env.vault"
    _write(vault, "encrypted")
    with pytest.raises(VerifyError, match="Identity file not found"):
        verify(vault, tmp_path / "missing.txt")


def test_verify_returns_ok_on_success(tmp_path):
    vault = tmp_path / "env.vault"
    identity = tmp_path / "key.txt"
    _write(vault, "encrypted")
    _write(identity, "age-secret-key")

    with patch("envault.verify.unpack", side_effect=_fake_unpack_ok):
        result = verify(vault, identity)

    assert result["ok"] is True
    assert result["error"] is None
    assert "API_KEY" in result["keys"]
    assert "DB_URL" in result["keys"]
    assert len(result["checksum"]) == 64


def test_verify_excludes_comments_from_keys(tmp_path):
    vault = tmp_path / "env.vault"
    identity = tmp_path / "key.txt"
    _write(vault, "encrypted")
    _write(identity, "age-secret-key")

    with patch("envault.verify.unpack", side_effect=_fake_unpack_ok):
        result = verify(vault, identity)

    assert all(not k.startswith("#") for k in result["keys"])


def test_verify_returns_not_ok_on_decrypt_failure(tmp_path):
    vault = tmp_path / "env.vault"
    identity = tmp_path / "key.txt"
    _write(vault, "encrypted")
    _write(identity, "age-secret-key")

    with patch("envault.verify.unpack", side_effect=_fake_unpack_fail):
        result = verify(vault, identity)

    assert result["ok"] is False
    assert "decryption failed" in result["error"]
    assert result["keys"] == []
    assert len(result["checksum"]) == 64
