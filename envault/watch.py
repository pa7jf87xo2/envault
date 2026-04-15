"""watch.py — Monitor a .env file for changes and auto-repack the vault."""

from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Callable, Optional

from envault.vault import pack, VaultError
from envault.audit import record


class WatchError(Exception):
    """Raised when the watcher cannot be started or encounters a fatal error."""


def _mtime(path: Path) -> float:
    """Return the modification time of *path*, or -1 if it does not exist."""
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return -1.0


def watch(
    env_file: Path,
    vault_file: Path,
    public_key: str,
    *,
    interval: float = 1.0,
    max_events: Optional[int] = None,
    on_change: Optional[Callable[[Path], None]] = None,
) -> None:
    """Poll *env_file* and repack whenever it changes.

    Parameters
    ----------
    env_file:    Path to the plaintext .env file to monitor.
    vault_file:  Destination vault path passed to :func:`envault.vault.pack`.
    public_key:  age public key used for encryption.
    interval:    Polling interval in seconds (default 1 s).
    max_events:  Stop after this many change events (``None`` = run forever).
    on_change:   Optional callback invoked with *vault_file* after each pack.
    """
    env_file = Path(env_file)
    vault_file = Path(vault_file)

    if not env_file.exists():
        raise WatchError(f"env file not found: {env_file}")

    last_mtime = _mtime(env_file)
    events = 0

    while True:
        time.sleep(interval)
        current_mtime = _mtime(env_file)

        if current_mtime == last_mtime:
            continue

        last_mtime = current_mtime
        try:
            pack(env_file, vault_file, public_key)
        except VaultError as exc:
            raise WatchError(f"repack failed: {exc}") from exc

        record("watch", str(env_file), extra={"vault": str(vault_file)})

        if on_change is not None:
            on_change(vault_file)

        events += 1
        if max_events is not None and events >= max_events:
            break
