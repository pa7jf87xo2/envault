"""CLI sub-commands for vault access control."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.access import AccessError, load_access, add_access, remove_access, check_access


def _cmd_access_list(ns: argparse.Namespace) -> None:
    vault = Path(ns.vault)
    try:
        keys = load_access(vault)
    except AccessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not keys:
        print("(no access restrictions — all keys allowed)")
    else:
        for k in keys:
            print(k)


def _cmd_access_add(ns: argparse.Namespace) -> None:
    vault = Path(ns.vault)
    try:
        keys = add_access(vault, ns.public_key)
    except AccessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Added. {len(keys)} key(s) in access list.")


def _cmd_access_remove(ns: argparse.Namespace) -> None:
    vault = Path(ns.vault)
    try:
        keys = remove_access(vault, ns.public_key)
    except AccessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Removed. {len(keys)} key(s) remaining.")


def _cmd_access_check(ns: argparse.Namespace) -> None:
    vault = Path(ns.vault)
    try:
        allowed = check_access(vault, ns.public_key)
    except AccessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if allowed:
        print("allowed")
    else:
        print("denied")
        sys.exit(1)


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Manage per-vault access control lists."
    if parent is not None:
        p = parent.add_parser("access", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envault access", description=desc)

    p.add_argument("--vault", default=".env.vault", metavar="VAULT")
    sub = p.add_subparsers(dest="access_cmd", required=True)

    sub.add_parser("list", help="List allowed public keys").set_defaults(func=_cmd_access_list)

    add_p = sub.add_parser("add", help="Add a public key")
    add_p.add_argument("public_key", metavar="PUBLIC_KEY")
    add_p.set_defaults(func=_cmd_access_add)

    rm_p = sub.add_parser("remove", help="Remove a public key")
    rm_p.add_argument("public_key", metavar="PUBLIC_KEY")
    rm_p.set_defaults(func=_cmd_access_remove)

    chk_p = sub.add_parser("check", help="Check if a key is allowed")
    chk_p.add_argument("public_key", metavar="PUBLIC_KEY")
    chk_p.set_defaults(func=_cmd_access_check)

    return p
