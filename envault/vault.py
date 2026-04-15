"""Vault file management: pack/unpack .env files into encrypted vault archives."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from envault.crypto import decrypt_file, encrypt_file

VAULT_EXTENSION = ".vault"
MANIFEST_NAME = "__manifest__.json"


class VaultError(Exception):
    """Raised when a vault operation fails."""


def pack(env_path: str | Path, recipient_pubkey: str, vault_path: str | Path | None = None) -> Path:
    """Encrypt an .env file into a vault file.

    Args:
        env_path: Path to the source .env file.
        recipient_pubkey: age public key of the recipient.
        vault_path: Destination path for the vault file. Defaults to <env_path>.vault.

    Returns:
        Path to the created vault file.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        raise VaultError(f"Source file not found: {env_path}")

    vault_path = Path(vault_path) if vault_path else env_path.with_suffix(VAULT_EXTENSION)

    manifest = {
        "source": env_path.name,
        "size": env_path.stat().st_size,
    }

    with tempfile.TemporaryDirectory() as tmp:
        bundle_path = Path(tmp) / "bundle.json"
        payload = {
            "manifest": manifest,
            "content": env_path.read_text(encoding="utf-8"),
        }
        bundle_path.write_text(json.dumps(payload), encoding="utf-8")
        encrypt_file(str(bundle_path), recipient_pubkey, str(vault_path))

    return vault_path


def unpack(vault_path: str | Path, identity_file: str | Path, output_dir: str | Path | None = None) -> Path:
    """Decrypt a vault file and restore the .env file.

    Args:
        vault_path: Path to the encrypted vault file.
        identity_file: Path to the age identity (private key) file.
        output_dir: Directory to write the restored .env file. Defaults to vault's directory.

    Returns:
        Path to the restored .env file.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise VaultError(f"Vault file not found: {vault_path}")

    output_dir = Path(output_dir) if output_dir else vault_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        bundle_path = Path(tmp) / "bundle.json"
        decrypt_file(str(vault_path), str(identity_file), str(bundle_path))
        payload = json.loads(bundle_path.read_text(encoding="utf-8"))

    manifest = payload["manifest"]
    content = payload["content"]

    output_path = output_dir / manifest["source"]
    output_path.write_text(content, encoding="utf-8")
    return output_path
