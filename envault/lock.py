"""Vault locking — prevent concurrent modifications via a lock file."""

from __future__ import annotations

import os
import time
from pathlib import Path


class LockError(Exception):
    """Raised when a lock cannot be acquired or released."""


def lock_path(vault: Path) -> Path:
    return vault.with_suffix(vault.suffix + ".lock")


def acquire(vault: Path, timeout: float = 5.0, poll: float = 0.1) -> Path:
    """Acquire a lock for *vault*. Returns the lock path.

    Raises LockError if the lock cannot be acquired within *timeout* seconds.
    """
    lp = lock_path(vault)
    if not vault.exists():
        raise LockError(f"vault not found: {vault}")
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(str(lp), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return lp
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise LockError(
                    f"could not acquire lock for {vault} within {timeout}s"
                )
            time.sleep(poll)


def release(vault: Path) -> None:
    """Release the lock for *vault*. Raises LockError if no lock exists."""
    lp = lock_path(vault)
    if not lp.exists():
        raise LockError(f"no lock file found for {vault}")
    lp.unlink()


def is_locked(vault: Path) -> bool:
    """Return True if *vault* currently has a lock file."""
    return lock_path(vault).exists()
