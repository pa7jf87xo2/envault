"""Tests for envault.rotate."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.rotate import RotationError, rotate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(tmp_path: Path, name: str = "test.vault") -> Path:
    p = tmp_path / name
    p.write_bytes(b"fake-vault-content")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rotate_raises_when_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(RotationError, match="Vault file not found"):
        rotate(
            vault_path=tmp_path / "nonexistent.vault",
            old_identity=tmp_path / "key.txt",
            new_recipient="age1newrecipient",
        )


def test_rotate_raises_when_unpack_fails(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.rotate.unpack", side_effect=Exception("bad decrypt")):
        with pytest.raises(RotationError, match="Failed to decrypt vault"):
            rotate(
                vault_path=vault,
                old_identity=tmp_path / "key.txt",
                new_recipient="age1newrecipient",
            )


def test_rotate_raises_when_pack_fails(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    with patch("envault.rotate.unpack"), \
         patch("envault.rotate.pack", side_effect=Exception("bad encrypt")):
        with pytest.raises(RotationError, match="Failed to re-encrypt vault"):
            rotate(
                vault_path=vault,
                old_identity=tmp_path / "key.txt",
                new_recipient="age1newrecipient",
            )


def test_rotate_overwrites_vault_by_default(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    rotated_content = b"rotated-vault"

    def _fake_pack(source_path, vault_path, recipient):
        Path(vault_path).write_bytes(rotated_content)

    with patch("envault.rotate.unpack"), \
         patch("envault.rotate.pack", side_effect=_fake_pack):
        result = rotate(
            vault_path=vault,
            old_identity=tmp_path / "key.txt",
            new_recipient="age1newrecipient",
        )

    assert result == vault.resolve()
    assert vault.read_bytes() == rotated_content


def test_rotate_writes_to_custom_output_path(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    output = tmp_path / "subdir" / "rotated.vault"
    rotated_content = b"rotated-vault-custom"

    def _fake_pack(source_path, vault_path, recipient):
        Path(vault_path).write_bytes(rotated_content)

    with patch("envault.rotate.unpack"), \
         patch("envault.rotate.pack", side_effect=_fake_pack):
        result = rotate(
            vault_path=vault,
            old_identity=tmp_path / "key.txt",
            new_recipient="age1newrecipient",
            output_path=output,
        )

    assert result == output.resolve()
    assert output.read_bytes() == rotated_content
    # original vault untouched
    assert vault.read_bytes() == b"fake-vault-content"
