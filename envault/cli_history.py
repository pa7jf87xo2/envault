"""cli_history.py – CLI sub-commands for vault operation history."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.history import HistoryError, clear_history, load_history, record_event


def _cmd_history_list(ns: argparse.Namespace) -> None:
    vault = Path(ns.vault)
    try:
        entries = load_history(vault)
    except HistoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not entries:
        print("no history recorded.")
        return
    for e in entries:
        parts = [e.get("ts", ""), e.get("action", "")]
        if "user" in e:
            parts.append(f"user={e['user']}")
        if "note" in e:
            parts.append(f"note={e['note']}")
        print("  ".join(parts))


def _cmd_history_record(ns: argparse.Namespace) -> None:
    vault = Path(ns.vault)
    try:
        entry = record_event(
            vault,
            ns.action,
            user=getattr(ns, "user", None),
            note=getattr(ns, "note", None),
        )
    except HistoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"recorded: {entry['action']} at {entry['ts']}")


def _cmd_history_clear(ns: argparse.Namespace) -> None:
    vault = Path(ns.vault)
    try:
        clear_history(vault)
    except HistoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print("history cleared.")


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Manage vault operation history.")
    parser: argparse.ArgumentParser = parent.add_parser("history", **kwargs) if parent else argparse.ArgumentParser(**kwargs)  # type: ignore[assignment]
    parser.add_argument("--vault", default=".env.vault", help="path to vault file")
    sub = parser.add_subparsers(dest="history_cmd", required=True)

    sub.add_parser("list", help="list recorded events").set_defaults(func=_cmd_history_list)

    rec = sub.add_parser("record", help="manually record an event")
    rec.add_argument("action", help="action label, e.g. pack/unpack/push")
    rec.add_argument("--user", default=None)
    rec.add_argument("--note", default=None)
    rec.set_defaults(func=_cmd_history_record)

    clr = sub.add_parser("clear", help="clear all history for the vault")
    clr.set_defaults(func=_cmd_history_clear)

    return parser
