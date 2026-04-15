"""Pre/post hook execution for envault pack/unpack lifecycle events."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional


class HookError(Exception):
    """Raised when a hook script fails or cannot be executed."""


_VALID_HOOKS = frozenset(["pre-pack", "post-pack", "pre-unpack", "post-unpack"])


def hooks_dir(base: Path) -> Path:
    """Return the canonical hooks directory relative to *base*."""
    return base / ".envault" / "hooks"


def hook_path(base: Path, name: str) -> Path:
    """Return the path for a named hook script."""
    if name not in _VALID_HOOKS:
        raise HookError(f"Unknown hook '{name}'. Valid hooks: {sorted(_VALID_HOOKS)}")
    return hooks_dir(base) / name


def install_hook(base: Path, name: str, script: str, overwrite: bool = False) -> Path:
    """Write *script* to the hook file for *name*.

    The file is made executable (chmod 0o755).  Raises *HookError* if the
    hook already exists and *overwrite* is False.
    """
    path = hook_path(base, name)
    if path.exists() and not overwrite:
        raise HookError(f"Hook '{name}' already exists at {path}. Use overwrite=True to replace.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script)
    path.chmod(0o755)
    return path


def run_hook(
    base: Path,
    name: str,
    env: Optional[dict] = None,
    timeout: int = 30,
) -> Optional[subprocess.CompletedProcess]:
    """Execute the hook script *name* if it exists.

    Returns the *CompletedProcess* result or *None* when no hook is installed.
    Raises *HookError* on non-zero exit or timeout.
    """
    path = hook_path(base, name)
    if not path.exists():
        return None

    merged_env = {**os.environ, **(env or {})}
    try:
        result = subprocess.run(
            [str(path)],
            env=merged_env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise HookError(f"Hook '{name}' timed out after {timeout}s") from exc
    except OSError as exc:
        raise HookError(f"Hook '{name}' could not be executed: {exc}") from exc

    if result.returncode != 0:
        raise HookError(
            f"Hook '{name}' exited with code {result.returncode}.\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result
