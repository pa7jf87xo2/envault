"""Tests for envault.cli_hooks."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_hooks import (
    _cmd_hooks_install,
    _cmd_hooks_list,
    _cmd_hooks_remove,
    build_parser,
)
from envault.hooks import hook_path, install_hook


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"base": ".", "force": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_hooks_list_shows_all_hooks(tmp_path: Path, capsys) -> None:
    _cmd_hooks_list(_ns(base=str(tmp_path)))
    out = capsys.readouterr().out
    for name in ("pre-pack", "post-pack", "pre-unpack", "post-unpack"):
        assert name in out


def test_hooks_list_shows_installed_status(tmp_path: Path, capsys) -> None:
    install_hook(tmp_path, "pre-pack", "#!/bin/sh\nexit 0\n")
    _cmd_hooks_list(_ns(base=str(tmp_path)))
    out = capsys.readouterr().out
    assert "installed" in out


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------

def test_hooks_install_creates_hook(tmp_path: Path, capsys) -> None:
    _cmd_hooks_install(_ns(base=str(tmp_path), name="post-pack"))
    assert hook_path(tmp_path, "post-pack").exists()
    out = capsys.readouterr().out
    assert "installed" in out


def test_hooks_install_fails_if_exists(tmp_path: Path, capsys) -> None:
    install_hook(tmp_path, "pre-pack", "#!/bin/sh\nexit 0\n")
    with pytest.raises(SystemExit) as exc_info:
        _cmd_hooks_install(_ns(base=str(tmp_path), name="pre-pack"))
    assert exc_info.value.code == 1
    assert "already exists" in capsys.readouterr().err


def test_hooks_install_force_overwrites(tmp_path: Path, capsys) -> None:
    install_hook(tmp_path, "pre-pack", "#!/bin/sh\nexit 0\n")
    _cmd_hooks_install(_ns(base=str(tmp_path), name="pre-pack", force=True))
    assert hook_path(tmp_path, "pre-pack").exists()


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------

def test_hooks_remove_deletes_hook(tmp_path: Path, capsys) -> None:
    install_hook(tmp_path, "post-unpack", "#!/bin/sh\nexit 0\n")
    _cmd_hooks_remove(_ns(base=str(tmp_path), name="post-unpack"))
    assert not hook_path(tmp_path, "post-unpack").exists()


def test_hooks_remove_not_installed_is_graceful(tmp_path: Path, capsys) -> None:
    _cmd_hooks_remove(_ns(base=str(tmp_path), name="pre-unpack"))
    out = capsys.readouterr().out
    assert "not installed" in out


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

def test_build_parser_registers_subcommands() -> None:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_parser(sub)
    ns = root.parse_args(["hooks", "list"])
    assert ns.hooks_cmd == "list"
