"""CLI sub-commands for vault alias management."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.alias import AliasError, load_aliases, set_alias, remove_alias, resolve_alias


def _cmd_alias_list(ns: argparse.Namespace) -> None:
    try:
        aliases = load_aliases(Path(ns.vault))
    except AliasError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not aliases:
        print("no aliases defined")
        return
    for name, target in sorted(aliases.items()):
        print(f"{name} -> {target}")


def _cmd_alias_set(ns: argparse.Namespace) -> None:
    try:
        set_alias(Path(ns.vault), ns.name, ns.target)
    except AliasError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"alias set: {ns.name} -> {ns.target}")


def _cmd_alias_remove(ns: argparse.Namespace) -> None:
    try:
        remove_alias(Path(ns.vault), ns.name)
    except AliasError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"alias removed: {ns.name}")


def _cmd_alias_resolve(ns: argparse.Namespace) -> None:
    try:
        target = resolve_alias(Path(ns.vault), ns.name)
    except AliasError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(target)


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Manage short aliases for vault paths"
    if parent is not None:
        p = parent.add_parser("alias", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envault alias", description=desc)

    p.add_argument("--vault", default=".envault", metavar="PATH")
    sub = p.add_subparsers(dest="alias_cmd", required=True)

    sub.add_parser("list", help="List all aliases").set_defaults(func=_cmd_alias_list)

    sp_set = sub.add_parser("set", help="Set an alias")
    sp_set.add_argument("name")
    sp_set.add_argument("target")
    sp_set.set_defaults(func=_cmd_alias_set)

    sp_rm = sub.add_parser("remove", help="Remove an alias")
    sp_rm.add_argument("name")
    sp_rm.set_defaults(func=_cmd_alias_remove)

    sp_res = sub.add_parser("resolve", help="Print target for an alias")
    sp_res.add_argument("name")
    sp_res.set_defaults(func=_cmd_alias_resolve)

    return p
