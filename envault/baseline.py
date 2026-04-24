"""baseline.py – snapshot a vault's decrypted key set as a baseline for drift detection."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Optional

from envault.vault import unpack


class BaselineError(Exception):
    """Raised when a baseline operation fails."""


def baseline_path(vault: Path) -> Path:
    """Return the sidecar path for the baseline file."""
    return vault.with_suffix(".baseline.json")


def _parse_env_keys(text: str) -> dict[str, str]:
    """Return a mapping of key -> sha256(value) from decrypted env text."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = hashlib.sha256(value.strip().encode()).hexdigest()
    return result


def save_baseline(
    vault: Path,
    identity: Path,
    *,
    out: Optional[Path] = None,
) -> Path:
    """Decrypt *vault* and save a baseline of key/value-hashes.

    Returns the path to the written baseline file.
    Raises BaselineError on failure.
    """
    if not vault.exists():
        raise BaselineError(f"Vault not found: {vault}")
    try:
        text = unpack(vault, identity)
    except Exception as exc:  # noqa: BLE001
        raise BaselineError(f"Failed to decrypt vault: {exc}") from exc

    keys = _parse_env_keys(text)
    dest = out or baseline_path(vault)
    dest.write_text(json.dumps({"vault": str(vault), "keys": keys}, indent=2))
    return dest


def load_baseline(vault: Path) -> dict[str, str]:
    """Load a previously saved baseline for *vault*.

    Returns the key -> hash mapping.
    Raises BaselineError if the file is missing or corrupt.
    """
    bp = baseline_path(vault)
    if not bp.exists():
        raise BaselineError(f"No baseline found for vault: {vault}")
    try:
        data = json.loads(bp.read_text())
        return data["keys"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise BaselineError(f"Corrupt baseline file: {bp}") from exc


def diff_baseline(
    vault: Path,
    identity: Path,
) -> dict[str, list[str]]:
    """Compare the current vault contents against the saved baseline.

    Returns a dict with keys:
      'added'   – keys present now but not in baseline
      'removed' – keys in baseline but not present now
      'changed' – keys whose value hash differs
    Raises BaselineError if no baseline exists or decryption fails.
    """
    old = load_baseline(vault)
    try:
        text = unpack(vault, identity)
    except Exception as exc:  # noqa: BLE001
        raise BaselineError(f"Failed to decrypt vault: {exc}") from exc

    current = _parse_env_keys(text)
    added = [k for k in current if k not in old]
    removed = [k for k in old if k not in current]
    changed = [k for k in current if k in old and current[k] != old[k]]
    return {"added": added, "removed": removed, "changed": changed}
