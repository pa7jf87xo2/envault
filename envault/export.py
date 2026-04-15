"""Export decrypted .env contents to various formats (shell, JSON, dotenv)."""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Dict, List, Literal

from envault.vault import unpack

ExportFormat = Literal["dotenv", "shell", "json"]


class ExportError(Exception):
    """Raised when export fails."""


def _parse_env(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines, skipping comments and blanks."""
    result: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def _to_shell(env: Dict[str, str]) -> str:
    """Render env vars as export KEY=VALUE shell lines."""
    lines: List[str] = []
    for key, value in env.items():
        lines.append(f"export {key}={shlex.quote(value)}")
    return "\n".join(lines)


def _to_dotenv(env: Dict[str, str]) -> str:
    """Render env vars in standard dotenv format."""
    lines: List[str] = []
    for key, value in env.items():
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def _to_json(env: Dict[str, str]) -> str:
    """Render env vars as a JSON object."""
    return json.dumps(env, indent=2)


def export_vault(
    vault: Path,
    identity: Path,
    fmt: ExportFormat = "dotenv",
    keys: List[str] | None = None,
) -> str:
    """Decrypt *vault* and return its contents rendered as *fmt*.

    Args:
        vault:    Path to the .vault file.
        identity: Path to the age private-key file.
        fmt:      One of ``dotenv``, ``shell``, or ``json``.
        keys:     Optional allowlist of keys to include; ``None`` means all.

    Returns:
        A string in the requested format.

    Raises:
        ExportError: If the vault is missing, decryption fails, or the
                     requested format is unknown.
    """
    if not vault.exists():
        raise ExportError(f"Vault not found: {vault}")

    try:
        tmp = Path("/tmp/_envault_export.env")
        unpack(vault, tmp, identity)
        raw = tmp.read_text()
        tmp.unlink(missing_ok=True)
    except Exception as exc:  # noqa: BLE001
        raise ExportError(f"Failed to decrypt vault: {exc}") from exc

    env = _parse_env(raw)

    if keys is not None:
        env = {k: v for k, v in env.items() if k in keys}

    if fmt == "dotenv":
        return _to_dotenv(env)
    if fmt == "shell":
        return _to_shell(env)
    if fmt == "json":
        return _to_json(env)
    raise ExportError(f"Unknown export format: {fmt!r}")
