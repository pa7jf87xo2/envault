"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.crypto import (
    generate_keypair,
    encrypt_file,
    decrypt_file,
    AgeNotFoundError,
    EncryptionError,
    DecryptionError,
)


PUBLIC_KEY = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"


def _ok(stdout="", stderr=""):
    m = MagicMock()
    m.returncode = 0
    m.stdout = stdout
    m.stderr = stderr
    return m


def _fail(stderr="error"):
    m = MagicMock()
    m.returncode = 1
    m.stderr = stderr
    return m


@patch("envault.crypto.shutil.which", return_value=None)
def test_require_age_raises_when_missing(mock_which):
    with pytest.raises(AgeNotFoundError):
        encrypt_file(Path("a"), Path("b"), PUBLIC_KEY)


@patch("envault.crypto.shutil.which", return_value="/usr/bin/age")
@patch("envault.crypto.subprocess.run")
def test_generate_keypair_returns_public_key(mock_run, _):
    mock_run.return_value = _ok(stderr=f"Public key: {PUBLIC_KEY}")
    key = generate_keypair(Path("/tmp/key.txt"))
    assert key == PUBLIC_KEY


@patch("envault.crypto.shutil.which", return_value="/usr/bin/age")
@patch("envault.crypto.subprocess.run")
def test_generate_keypair_raises_on_failure(mock_run, _):
    mock_run.return_value = _fail("keygen error")
    with pytest.raises(EncryptionError, match="age-keygen failed"):
        generate_keypair(Path("/tmp/key.txt"))


@patch("envault.crypto.shutil.which", return_value="/usr/bin/age")
@patch("envault.crypto.subprocess.run")
def test_encrypt_file_success(mock_run, _):
    mock_run.return_value = _ok()
    encrypt_file(Path(".env"), Path(".env.age"), PUBLIC_KEY)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "-r" in args and PUBLIC_KEY in args


@patch("envault.crypto.shutil.which", return_value="/usr/bin/age")
@patch("envault.crypto.subprocess.run")
def test_encrypt_file_raises_on_failure(mock_run, _):
    mock_run.return_value = _fail("bad recipient")
    with pytest.raises(EncryptionError, match="Encryption failed"):
        encrypt_file(Path(".env"), Path(".env.age"), PUBLIC_KEY)


@patch("envault.crypto.shutil.which", return_value="/usr/bin/age")
@patch("envault.crypto.subprocess.run")
def test_decrypt_file_success(mock_run, _):
    mock_run.return_value = _ok()
    decrypt_file(Path(".env.age"), Path(".env"), Path("/tmp/key.txt"))
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "-d" in args and "-i" in args


@patch("envault.crypto.shutil.which", return_value="/usr/bin/age")
@patch("envault.crypto.subprocess.run")
def test_decrypt_file_raises_on_failure(mock_run, _):
    mock_run.return_value = _fail("wrong identity")
    with pytest.raises(DecryptionError, match="Decryption failed"):
        decrypt_file(Path(".env.age"), Path(".env"), Path("/tmp/key.txt"))
