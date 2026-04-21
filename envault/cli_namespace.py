"""CLI sub-commands for vault namespace management.

Sub-commands
------------
  envault namespace set <vault> <name>   -- assign a namespace
  envault namespace show <vault>         -- print current namespace
  envault namespace clear <vault>        -- remove namespace
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.namespace import NamespaceError, clear_namespace, load_namespace, set_namespace


def _cmd_namespace_set(args: argparse.Namespace) -> None:
    try:
        ns = set_namespace(Path(args.vault), args.name)
        print(f"namespace set to '{ns}'")
    except NamespaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_namespace_show(args: argparse.Namespace) -> None:
    try:
        ns = load_namespace(Path(args.vault))
    except NamespaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if ns is None:
        print("(no namespace set)")
    else:
        print(ns)


def _cmd_namespace_clear(args: argparse.Namespace) -> None:
    try:
        clear_namespace(Path(args.vault))
        print("namespace cleared")
    except NamespaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Build (and optionally attach) the 'namespace' argument parser."""
    kwargs: dict = dict(
        description="Manage vault namespaces.",
        help="manage vault namespaces",
    )
    if parent is not None:
        parser = parent.add_parser("namespace", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envault namespace", **kwargs)

    sub = parser.add_subparsers(dest="namespace_cmd", required=True)

    # set
    p_set = sub.add_parser("set", help="assign a namespace to a vault")
    p_set.add_argument("vault", help="path to the vault file")
    p_set.add_argument("name", help="namespace string (no whitespace)")
    p_set.set_defaults(func=_cmd_namespace_set)

    # show
    p_show = sub.add_parser("show", help="print the current namespace")
    p_show.add_argument("vault", help="path to the vault file")
    p_show.set_defaults(func=_cmd_namespace_show)

    # clear
    p_clear = sub.add_parser("clear", help="remove the namespace from a vault")
    p_clear.add_argument("vault", help="path to the vault file")
    p_clear.set_defaults(func=_cmd_namespace_clear)

    return parser
