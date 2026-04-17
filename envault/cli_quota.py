"""CLI sub-commands for vault quota management."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.quota import QuotaError, set_quota, load_quota, check_quota, clear_quota, DEFAULT_MAX_BYTES


def _cmd_quota_set(ns: argparse.Namespace) -> None:
    try:
        entry = set_quota(Path(ns.vault), ns.max_bytes)
        print(f"Quota set: {entry['max_bytes']} bytes for {ns.vault}")
    except QuotaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_quota_show(ns: argparse.Namespace) -> None:
    try:
        q = load_quota(Path(ns.vault))
        if q is None:
            print(f"No quota set (default: {DEFAULT_MAX_BYTES} B)")
        else:
            print(f"max_bytes: {q['max_bytes']}")
    except QuotaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_quota_check(ns: argparse.Namespace) -> None:
    try:
        result = check_quota(Path(ns.vault))
        print(f"ok  size={result['size']} B  limit={result['max_bytes']} B")
    except QuotaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_quota_clear(ns: argparse.Namespace) -> None:
    try:
        clear_quota(Path(ns.vault))
        print(f"Quota cleared for {ns.vault}")
    except QuotaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser(sub: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Manage vault size quotas"
    if sub is not None:
        p = sub.add_parser("quota", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envault quota", description=desc)

    sp = p.add_subparsers(dest="quota_cmd", required=True)

    for name, fn, help_text in [
        ("set", _cmd_quota_set, "Set a size quota"),
        ("show", _cmd_quota_show, "Show current quota"),
        ("check", _cmd_quota_check, "Check vault against quota"),
        ("clear", _cmd_quota_clear, "Remove quota"),
    ]:
        cp = sp.add_parser(name, help=help_text)
        cp.add_argument("vault", help="Path to vault file")
        if name == "set":
            cp.add_argument("max_bytes", type=int, help="Maximum allowed bytes")
        cp.set_defaults(func=fn)

    return p
