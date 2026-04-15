"""sync.py — push/pull encrypted vault files to/from a remote location.

Supports local filesystem paths and scp-style remote targets
(user@host:/path/to/dir).  Remote transfers delegate to the system
`scp` binary so no extra Python dependencies are required.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class SyncError(Exception):
    """Raised when a push or pull operation fails."""


def _is_remote(target: str) -> bool:
    """Return True if *target* looks like an scp remote (user@host:/path)."""
    return ":" in target and not target.startswith("/")


def _require_scp() -> None:
    if shutil.which("scp") is None:
        raise SyncError(
            "'scp' executable not found; install OpenSSH client to sync with remote targets."
        )


def push(vault_path: Path, destination: str) -> None:
    """Copy *vault_path* to *destination*.

    *destination* may be a local directory path or an scp-style remote
    string such as ``user@host:/backups/``.
    """
    if not vault_path.exists():
        raise SyncError(f"Vault file not found: {vault_path}")

    if _is_remote(destination):
        _require_scp()
        result = subprocess.run(
            ["scp", str(vault_path), destination],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise SyncError(f"scp push failed: {result.stderr.strip()}")
    else:
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(vault_path, dest_path / vault_path.name)


def pull(source: str, destination: Path) -> None:
    """Copy a vault file from *source* to *destination*.

    *source* may be a local file path or an scp-style remote string.
    *destination* is the local path where the file should be written.
    """
    if _is_remote(source):
        _require_scp()
        destination.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["scp", source, str(destination)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise SyncError(f"scp pull failed: {result.stderr.strip()}")
    else:
        src_path = Path(source)
        if not src_path.exists():
            raise SyncError(f"Source file not found: {src_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, destination)
