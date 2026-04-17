"""Vault signing and signature verification using SHA-256 HMAC."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

SIG_SUFFIX = ".sig"


class SignError(Exception):
    pass


def sig_path(vault: Path) -> Path:
    return vault.with_suffix(vault.suffix + SIG_SUFFIX)


def sign(vault: Path, secret: str) -> dict:
    """Sign a vault file with a shared secret. Returns the signature entry."""
    if not vault.exists():
        raise SignError(f"vault not found: {vault}")
    if not secret:
        raise SignError("secret must not be empty")
    digest = hmac.new(
        secret.encode(), vault.read_bytes(), hashlib.sha256
    ).hexdigest()
    entry = {"vault": str(vault), "hmac_sha256": digest}
    sig_path(vault).write_text(json.dumps(entry) + "\n")
    return entry


def verify_signature(vault: Path, secret: str) -> bool:
    """Return True if the vault signature matches the current contents."""
    if not vault.exists():
        raise SignError(f"vault not found: {vault}")
    sp = sig_path(vault)
    if not sp.exists():
        raise SignError(f"signature file not found: {sp}")
    if not secret:
        raise SignError("secret must not be empty")
    entry = json.loads(sp.read_text())
    expected = entry.get("hmac_sha256", "")
    actual = hmac.new(
        secret.encode(), vault.read_bytes(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, actual)


def clear_signature(vault: Path) -> bool:
    """Remove the signature file if present. Returns True if removed."""
    sp = sig_path(vault)
    if sp.exists():
        sp.unlink()
        return True
    return False
