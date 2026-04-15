"""Tests for envault.vault (pack/unpack round-trip)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.vault import VaultError, pack, unpack


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_ENV = "DB_URL=postgres://localhost/mydb\nSECRET_KEY=supersecret\n"


def _make_env_file(tmp_path: Path, name: str = ".env", content: str = SAMPLE_ENV) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# pack()
# ---------------------------------------------------------------------------


def test_pack_raises_when_source_missing(tmp_path):
    with pytest.raises(VaultError, match="Source file not found"):
        pack(tmp_path / "nonexistent.env", "age1pubkey")


def test_pack_creates_vault_file(tmp_path):
    env_file = _make_env_file(tmp_path)
    vault_file = tmp_path / ".env.vault"

    with patch("envault.vault.encrypt_file") as mock_enc:
        result = pack(env_file, "age1pubkey", vault_file)

    assert result == vault_file
    mock_enc.assert_called_once()
    # Ensure the destination arg matches
    _, _, dest = mock_enc.call_args.args
    assert dest == str(vault_file)


def test_pack_default_vault_path(tmp_path):
    env_file = _make_env_file(tmp_path)

    with patch("envault.vault.encrypt_file"):
        result = pack(env_file, "age1pubkey")

    assert result == env_file.with_suffix(".vault")


def test_pack_bundle_contains_content(tmp_path):
    env_file = _make_env_file(tmp_path)
    captured_bundle: dict = {}

    def fake_encrypt(src, pubkey, dest):
        data = Path(src).read_text(encoding="utf-8")
        captured_bundle.update(json.loads(data))

    with patch("envault.vault.encrypt_file", side_effect=fake_encrypt):
        pack(env_file, "age1pubkey")

    assert captured_bundle["content"] == SAMPLE_ENV
    assert captured_bundle["manifest"]["source"] == ".env"


# ---------------------------------------------------------------------------
# unpack()
# ---------------------------------------------------------------------------


def test_unpack_raises_when_vault_missing(tmp_path):
    with pytest.raises(VaultError, match="Vault file not found"):
        unpack(tmp_path / "missing.vault", tmp_path / "identity.txt")


def test_unpack_restores_env_file(tmp_path):
    vault_file = tmp_path / ".env.vault"
    vault_file.write_bytes(b"fake-ciphertext")
    identity_file = tmp_path / "identity.txt"
    identity_file.write_text("AGE-SECRET-KEY-1FAKE", encoding="utf-8")

    payload = json.dumps({"manifest": {"source": ".env"}, "content": SAMPLE_ENV})

    def fake_decrypt(src, identity, dest):
        Path(dest).write_text(payload, encoding="utf-8")

    with patch("envault.vault.decrypt_file", side_effect=fake_decrypt):
        result = unpack(vault_file, identity_file, tmp_path)

    assert result == tmp_path / ".env"
    assert result.read_text(encoding="utf-8") == SAMPLE_ENV
