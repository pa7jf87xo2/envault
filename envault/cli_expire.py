"""CLI sub-commands for vault expiry management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.expire import ExpireError, check_expiry, clear_expiry, set_expiry


def _cmd_expire_set(ns: argparse.Namespace) -> None:
    try:
        entry = set_expiry(Path(ns.vault), days=ns.days)
        print(f"Expiry set: {entry['expires_at']}")
    except ExpireError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_expire_check(ns: argparse.Namespace) -> None:
    try:
        expired, msg = check_expiry(Path(ns.vault))
        status = "EXPIRED" if expired else "OK"
        print(f"[{status}] {msg}")
        if expired:
            sys.exit(2)
    except ExpireError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_expire_clear(ns: argparse.Namespace) -> None:
    try:
        removed = clear_expiry(Path(ns.vault))
        print("Expiry cleared." if removed else "No expiry was set.")
    except ExpireError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser(sub: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    if sub is not None:
        p = sub.add_parser("expire", help="manage vault expiry")
    else:
        p = argparse.ArgumentParser(prog="envault expire")

    cmds = p.add_subparsers(dest="expire_cmd", required=True)

    s = cmds.add_parser("set", help="set expiry on a vault")
    s.add_argument("vault", help="path to .vault file")
    s.add_argument("--days", type=int, required=True, help="TTL in days")
    s.set_defaults(func=_cmd_expire_set)

    c = cmds.add_parser("check", help="check whether a vault has expired")
    c.add_argument("vault", help="path to .vault file")
    c.set_defaults(func=_cmd_expire_check)

    cl = cmds.add_parser("clear", help="remove expiry metadata from a vault")
    cl.add_argument("vault", help="path to .vault file")
    cl.set_defaults(func=_cmd_expire_clear)

    return p
