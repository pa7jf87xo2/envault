"""Tests for envault.hooks."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from envault.hooks import (
    HookError,
    hook_path,
    hooks_dir,
    install_hook,
    run_hook,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_NOOP = "#!/bin/sh\nexit 0\n"
_FAIL = "#!/bin/sh\necho 'boom' >&2\nexit 1\n"
_SLOW = "#!/bin/sh\nsleep 10\n"


# ---------------------------------------------------------------------------
# hooks_dir / hook_path
# ---------------------------------------------------------------------------

def test_hooks_dir_returns_correct_path(tmp_path: Path) -> None:
    assert hooks_dir(tmp_path) == tmp_path / ".envault" / "hooks"


def test_hook_path_valid_name(tmp_path: Path) -> None:
    p = hook_path(tmp_path, "pre-pack")
    assert p.name == "pre-pack"


def test_hook_path_invalid_name_raises(tmp_path: Path) -> None:
    with pytest.raises(HookError, match="Unknown hook"):
        hook_path(tmp_path, "post-deploy")


# ---------------------------------------------------------------------------
# install_hook
# ---------------------------------------------------------------------------

def test_install_hook_creates_file(tmp_path: Path) -> None:
    path = install_hook(tmp_path, "pre-pack", _NOOP)
    assert path.exists()
    assert path.read_text() == _NOOP


def test_install_hook_is_executable(tmp_path: Path) -> None:
    path = install_hook(tmp_path, "post-pack", _NOOP)
    mode = path.stat().st_mode
    assert mode & stat.S_IXUSR


def test_install_hook_raises_if_exists_no_overwrite(tmp_path: Path) -> None:
    install_hook(tmp_path, "pre-pack", _NOOP)
    with pytest.raises(HookError, match="already exists"):
        install_hook(tmp_path, "pre-pack", _NOOP)


def test_install_hook_overwrites_when_requested(tmp_path: Path) -> None:
    install_hook(tmp_path, "pre-pack", _NOOP)
    new_script = "#!/bin/sh\necho updated\n"
    install_hook(tmp_path, "pre-pack", new_script, overwrite=True)
    assert hook_path(tmp_path, "pre-pack").read_text() == new_script


# ---------------------------------------------------------------------------
# run_hook
# ---------------------------------------------------------------------------

def test_run_hook_returns_none_when_not_installed(tmp_path: Path) -> None:
    result = run_hook(tmp_path, "pre-unpack")
    assert result is None


def test_run_hook_executes_successfully(tmp_path: Path) -> None:
    install_hook(tmp_path, "post-unpack", _NOOP)
    result = run_hook(tmp_path, "post-unpack")
    assert result is not None
    assert result.returncode == 0


def test_run_hook_raises_on_failure(tmp_path: Path) -> None:
    install_hook(tmp_path, "pre-pack", _FAIL)
    with pytest.raises(HookError, match="exited with code 1"):
        run_hook(tmp_path, "pre-pack")


def test_run_hook_raises_on_timeout(tmp_path: Path) -> None:
    install_hook(tmp_path, "pre-pack", _SLOW)
    with pytest.raises(HookError, match="timed out"):
        run_hook(tmp_path, "pre-pack", timeout=1)


def test_run_hook_passes_env(tmp_path: Path) -> None:
    script = "#!/bin/sh\ntest \"$ENVAULT_TEST\" = \"hello\"\n"
    install_hook(tmp_path, "post-pack", script)
    result = run_hook(tmp_path, "post-pack", env={"ENVAULT_TEST": "hello"})
    assert result is not None and result.returncode == 0
