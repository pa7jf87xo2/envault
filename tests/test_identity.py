"""Tests for envault.identity module."""

from __future__ import annotations

import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.identity import IdentityError, init_identity, load_public_key


# ---------------------------------------------------------------------------
# init_identity()
# ---------------------------------------------------------------------------


def test_init_identity_creates_file(tmp_path):
    identity_path = tmp_path / "identity.txt"

    with patch("envault.identity.generate_keypair", return_value=("age1pub", "AGE-SECRET-KEY-1PRIV")):
        path, pubkey = init_identity(identity_path)

    assert path == identity_path
    assert identity_path.exists()
    assert pubkey == "age1pub"
    assert "AGE-SECRET-KEY-1PRIV" in identity_path.read_text()


def test_init_identity_sets_restrictive_permissions(tmp_path):
    identity_path = tmp_path / "identity.txt"

    with patch("envault.identity.generate_keypair", return_value=("age1pub", "AGE-SECRET-KEY-1PRIV")):
        init_identity(identity_path)

    mode = identity_path.stat().st_mode
    # Owner read+write only
    assert mode & stat.S_IRWXG == 0
    assert mode & stat.S_IRWXO == 0


def test_init_identity_raises_if_exists_no_overwrite(tmp_path):
    identity_path = tmp_path / "identity.txt"
    identity_path.write_text("existing", encoding="utf-8")

    with pytest.raises(IdentityError, match="already exists"):
        init_identity(identity_path, overwrite=False)


def test_init_identity_overwrites_when_requested(tmp_path):
    identity_path = tmp_path / "identity.txt"
    identity_path.write_text("old", encoding="utf-8")

    with patch("envault.identity.generate_keypair", return_value=("age1newpub", "AGE-SECRET-KEY-1NEW")):
        path, pubkey = init_identity(identity_path, overwrite=True)

    assert pubkey == "age1newpub"
    assert "AGE-SECRET-KEY-1NEW" in identity_path.read_text()


# ---------------------------------------------------------------------------
# load_public_key()
# ---------------------------------------------------------------------------


def test_load_public_key_raises_when_file_missing(tmp_path):
    with pytest.raises(IdentityError, match="Identity file not found"):
        load_public_key(tmp_path / "no-such-identity.txt")


def test_load_public_key_returns_pubkey(tmp_path):
    identity_path = tmp_path / "identity.txt"
    identity_path.write_text("AGE-SECRET-KEY-1FAKE", encoding="utf-8")

    import subprocess
    mock_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="age1derivedpubkey\n", stderr=""
    )

    with patch("shutil.which", return_value="/usr/bin/age-keygen"), \
         patch("subprocess.run", return_value=mock_result):
        pubkey = load_public_key(identity_path)

    assert pubkey == "age1derivedpubkey"
