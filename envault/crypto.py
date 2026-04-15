"""Low-level age encryption/decryption helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class AgeNotFoundError(RuntimeError):
    """Raised when the `age` binary cannot be found on PATH."""


class EncryptionError(RuntimeError):
    """Raised when age encryption fails."""


class DecryptionError(RuntimeError):
    """Raised when age decryption fails."""


def _require_age() -> str:
    """Return the path to the age binary or raise AgeNotFoundError."""
    binary = shutil.which("age")
    if binary is None:
        raise AgeNotFoundError(
            "'age' binary not found on PATH. Install it from https://github.com/FiloSottile/age"
        )
    return binary


def generate_keypair() -> tuple[str, str]:
    """Generate a new age keypair.

    Returns:
        A (public_key, private_key) tuple of strings.

    Raises:
        AgeNotFoundError: If age-keygen is not installed.
        EncryptionError: If key generation fails.
    """
    keygen = shutil.which("age-keygen")
    if keygen is None:
        raise AgeNotFoundError("'age-keygen' binary not found on PATH.")

    result = subprocess.run([keygen], capture_output=True, text=True)
    if result.returncode != 0:
        raise EncryptionError(f"age-keygen failed: {result.stderr.strip()}")

    private_key = ""
    public_key = ""
    for line in result.stdout.splitlines():
        if line.startswith("AGE-SECRET-KEY"):
            private_key = line.strip()
        elif line.startswith("# public key:"):
            public_key = line.split(":", 1)[1].strip()

    if not private_key or not public_key:
        raise EncryptionError("Could not parse age-keygen output.")

    return public_key, private_key


def encrypt_file(src: str, recipient_pubkey: str, dest: str) -> None:
    """Encrypt *src* for *recipient_pubkey* and write ciphertext to *dest*."""
    age = _require_age()
    result = subprocess.run(
        [age, "--recipient", recipient_pubkey, "--output", dest, src],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EncryptionError(f"age encryption failed: {result.stderr.strip()}")


def decrypt_file(src: str, identity_file: str, dest: str) -> None:
    """Decrypt *src* using *identity_file* and write plaintext to *dest*."""
    age = _require_age()
    result = subprocess.run(
        [age, "--decrypt", "--identity", identity_file, "--output", dest, src],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DecryptionError(f"age decryption failed: {result.stderr.strip()}")
