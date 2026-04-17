"""Tests for envault.sign."""
from pathlib import Path
import json
import pytest
from envault.sign import (
    SignError,
    sig_path,
    sign,
    verify_signature,
    clear_signature,
)


def _make_vault(tmp_path: Path, content: bytes = b"SECRET=abc\n") -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(content)
    return v


def test_sig_path_uses_suffix(tmp_path):
    v = tmp_path / "env.vault"
    assert sig_path(v) == tmp_path / "env.vault.sig"


def test_sign_raises_when_vault_missing(tmp_path):
    with pytest.raises(SignError, match="vault not found"):
        sign(tmp_path / "missing.vault", "secret")


def test_sign_raises_on_empty_secret(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(SignError, match="secret must not be empty"):
        sign(v, "")


def test_sign_creates_sig_file(tmp_path):
    v = _make_vault(tmp_path)
    sign(v, "mysecret")
    assert sig_path(v).exists()


def test_sign_returns_entry_with_hmac(tmp_path):
    v = _make_vault(tmp_path)
    entry = sign(v, "mysecret")
    assert "hmac_sha256" in entry
    assert len(entry["hmac_sha256"]) == 64


def test_sign_sig_file_is_valid_json(tmp_path):
    v = _make_vault(tmp_path)
    sign(v, "mysecret")
    data = json.loads(sig_path(v).read_text())
    assert "hmac_sha256" in data


def test_verify_signature_returns_true_for_valid(tmp_path):
    v = _make_vault(tmp_path)
    sign(v, "mysecret")
    assert verify_signature(v, "mysecret") is True


def test_verify_signature_returns_false_for_wrong_secret(tmp_path):
    v = _make_vault(tmp_path)
    sign(v, "mysecret")
    assert verify_signature(v, "wrongsecret") is False


def test_verify_signature_raises_when_vault_missing(tmp_path):
    with pytest.raises(SignError, match="vault not found"):
        verify_signature(tmp_path / "missing.vault", "s")


def test_verify_signature_raises_when_sig_missing(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(SignError, match="signature file not found"):
        verify_signature(v, "mysecret")


def test_clear_signature_removes_file(tmp_path):
    v = _make_vault(tmp_path)
    sign(v, "mysecret")
    assert clear_signature(v) is True
    assert not sig_path(v).exists()


def test_clear_signature_returns_false_when_absent(tmp_path):
    v = _make_vault(tmp_path)
    assert clear_signature(v) is False
