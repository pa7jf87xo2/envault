"""Encryption and decryption utilities using age encryption via pyage/subprocess."""

import subprocess
import shutil
from pathlib import Path


AGE_BINARY = "age"
AGE_KEYGEN_BINARY = "age-keygen"


class AgeNotFoundError(Exception):
    """Raised when the age binary is not found on PATH."""


class EncryptionError(Exception):
    """Raised when encryption fails."""


class DecryptionError(Exception):
    """Raised when decryption fails."""


def _require_age() -> None:
    """Ensure the age binary is available."""
    if not shutil.which(AGE_BINARY):
        raise AgeNotFoundError(
            "'age' binary not found. Install it from https://github.com/FiloSottile/age"
        )


def generate_keypair(output_path: Path) -> str:
    """Generate a new age keypair, write private key to output_path, return public key."""
    _require_age()
    result = subprocess.run(
        [AGE_KEYGEN_BINARY, "-o", str(output_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EncryptionError(f"age-keygen failed: {result.stderr.strip()}")
    # Public key is printed to stderr by age-keygen
    for line in result.stderr.splitlines():
        if line.startswith("Public key:"):
            return line.split(":", 1)[1].strip()
    raise EncryptionError("Could not parse public key from age-keygen output.")


def encrypt_file(input_path: Path, output_path: Path, recipient_public_key: str) -> None:
    """Encrypt input_path with the given age public key, writing to output_path."""
    _require_age()
    result = subprocess.run(
        [AGE_BINARY, "-r", recipient_public_key, "-o", str(output_path), str(input_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EncryptionError(f"Encryption failed: {result.stderr.strip()}")


def decrypt_file(input_path: Path, output_path: Path, identity_path: Path) -> None:
    """Decrypt input_path using the age identity file, writing plaintext to output_path."""
    _require_age()
    result = subprocess.run(
        [AGE_BINARY, "-d", "-i", str(identity_path), "-o", str(output_path), str(input_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DecryptionError(f"Decryption failed: {result.stderr.strip()}")
