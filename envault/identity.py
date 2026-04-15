"""Manage age identity files (private keys) on the local machine."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from envault.crypto import generate_keypair

DEFAULT_IDENTITY_DIR = Path.home() / ".config" / "envault"
DEFAULT_IDENTITY_FILE = DEFAULT_IDENTITY_DIR / "identity.txt"


class IdentityError(Exception):
    """Raised when identity management fails."""


def init_identity(identity_path: str | Path | None = None, overwrite: bool = False) -> tuple[Path, str]:
    """Create a new age identity file if one does not already exist.

    Args:
        identity_path: Where to store the identity file. Defaults to ~/.config/envault/identity.txt.
        overwrite: If True, replace an existing identity file.

    Returns:
        (identity_path, public_key) tuple.
    """
    identity_path = Path(identity_path) if identity_path else DEFAULT_IDENTITY_FILE

    if identity_path.exists() and not overwrite:
        raise IdentityError(
            f"Identity file already exists at {identity_path}. "
            "Use overwrite=True to replace it."
        )

    public_key, private_key = generate_keypair()

    identity_path.parent.mkdir(parents=True, exist_ok=True)
    identity_path.write_text(private_key + "\n", encoding="utf-8")
    # Restrict permissions to owner only (600)
    identity_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    return identity_path, public_key


def load_public_key(identity_path: str | Path | None = None) -> str:
    """Read the public key that corresponds to a stored identity file.

    The public key is derived by re-running age-keygen --convert on the private key.
    """
    import shutil
    import subprocess

    identity_path = Path(identity_path) if identity_path else DEFAULT_IDENTITY_FILE
    if not identity_path.exists():
        raise IdentityError(f"Identity file not found: {identity_path}")

    keygen = shutil.which("age-keygen")
    if keygen is None:
        raise IdentityError("'age-keygen' not found; cannot derive public key.")

    private_key = identity_path.read_text(encoding="utf-8").strip()
    result = subprocess.run(
        [keygen, "-y"],
        input=private_key,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise IdentityError(f"Failed to derive public key: {result.stderr.strip()}")

    return result.stdout.strip()
