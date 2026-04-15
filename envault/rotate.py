"""Key rotation helpers for envault.

Allows re-encrypting an existing vault file under a new recipient public key
without exposing the plaintext .env on disk any longer than necessary.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from envault.crypto import decrypt_file, encrypt_file
from envault.vault import pack, unpack


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate(
    vault_path: str | Path,
    old_identity: str | Path,
    new_recipient: str,
    *,
    output_path: str | Path | None = None,
) -> Path:
    """Re-encrypt *vault_path* for *new_recipient* using *old_identity* to decrypt.

    Parameters
    ----------
    vault_path:
        Path to the existing ``.vault`` file.
    old_identity:
        Path to the age identity file (private key) that can decrypt the vault.
    new_recipient:
        age public key string for the new recipient.
    output_path:
        Destination for the rotated vault.  Defaults to overwriting *vault_path*.

    Returns
    -------
    Path
        Absolute path to the newly written vault file.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise RotationError(f"Vault file not found: {vault_path}")

    output_path = Path(output_path) if output_path else vault_path

    with tempfile.TemporaryDirectory(prefix="envault-rotate-") as tmp:
        tmp_dir = Path(tmp)
        tmp_env = tmp_dir / ".env"
        tmp_vault = tmp_dir / "rotated.vault"

        # Decrypt existing vault into a temp .env file
        try:
            unpack(
                vault_path=str(vault_path),
                dest_path=str(tmp_env),
                identity=str(old_identity),
            )
        except Exception as exc:
            raise RotationError(f"Failed to decrypt vault for rotation: {exc}") from exc

        # Re-encrypt under the new recipient
        try:
            pack(
                source_path=str(tmp_env),
                vault_path=str(tmp_vault),
                recipient=new_recipient,
            )
        except Exception as exc:
            raise RotationError(f"Failed to re-encrypt vault: {exc}") from exc

        # Move rotated vault to final destination
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_vault.replace(output_path)

    return output_path.resolve()
