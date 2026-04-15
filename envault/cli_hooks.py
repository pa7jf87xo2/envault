"""CLI sub-commands for managing envault lifecycle hooks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.hooks import (
    HookError,
    _VALID_HOOKS,
    hook_path,
    hooks_dir,
    install_hook,
)

_DEFAULT_SCRIPT = """#!/bin/sh
# envault hook: {name}
# Add your commands below.
exit 0
"""


def _cmd_hooks_list(args: argparse.Namespace) -> None:
    base = Path(args.base)
    hdir = hooks_dir(base)
    installed = []
    for name in sorted(_VALID_HOOKS):
        p = hdir / name
        status = "installed" if p.exists() else "not installed"
        installed.append(f"  {name:<14} {status}")
    print("Hooks:\n" + "\n".join(installed))


def _cmd_hooks_install(args: argparse.Namespace) -> None:
    base = Path(args.base)
    script = _DEFAULT_SCRIPT.format(name=args.name)
    try:
        path = install_hook(base, args.name, script, overwrite=args.force)
    except HookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Hook '{args.name}' installed at {path}")


def _cmd_hooks_remove(args: argparse.Namespace) -> None:
    base = Path(args.base)
    try:
        path = hook_path(base, args.name)
    except HookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not path.exists():
        print(f"Hook '{args.name}' is not installed.")
        return
    path.unlink()
    print(f"Hook '{args.name}' removed.")


def build_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = parent.add_parser("hooks", help="Manage lifecycle hooks")
    p.add_argument("--base", default=".", help="Project base directory")
    sub = p.add_subparsers(dest="hooks_cmd", required=True)

    sub.add_parser("list", help="List all hooks and their status").set_defaults(
        func=_cmd_hooks_list
    )

    inst = sub.add_parser("install", help="Install a hook script")
    inst.add_argument("name", choices=sorted(_VALID_HOOKS))
    inst.add_argument("--force", action="store_true", help="Overwrite existing hook")
    inst.set_defaults(func=_cmd_hooks_install)

    rm = sub.add_parser("remove", help="Remove an installed hook")
    rm.add_argument("name", choices=sorted(_VALID_HOOKS))
    rm.set_defaults(func=_cmd_hooks_remove)
