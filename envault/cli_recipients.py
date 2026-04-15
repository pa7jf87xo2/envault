"""CLI sub-commands for managing vault recipients."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.recipients import (
    RecipientsError,
    recipients_path,
    load_recipients,
    add_recipient,
    remove_recipient,
)


def _cmd_recipients_list(args: argparse.Namespace) -> int:
    path = recipients_path(args.dir)
    try:
        keys = load_recipients(path)
    except RecipientsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not keys:
        print("No recipients configured.")
    else:
        for key in keys:
            print(key)
    return 0


def _cmd_recipients_add(args: argparse.Namespace) -> int:
    path = recipients_path(args.dir)
    try:
        add_recipient(path, args.key)
    except RecipientsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Added recipient: {args.key}")
    return 0


def _cmd_recipients_remove(args: argparse.Namespace) -> int:
    path = recipients_path(args.dir)
    try:
        remove_recipient(path, args.key)
    except RecipientsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Removed recipient: {args.key}")
    return 0


def build_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach *recipients* sub-commands to an existing subparsers action."""
    rp = parent.add_parser("recipients", help="Manage trusted recipients")
    rp.add_argument("--dir", type=Path, default=Path("."), metavar="DIR")
    sub = rp.add_subparsers(dest="recipients_cmd", required=True)

    sub.add_parser("list", help="List current recipients").set_defaults(
        func=_cmd_recipients_list
    )

    add_p = sub.add_parser("add", help="Add a recipient public key")
    add_p.add_argument("key", metavar="PUBLIC_KEY")
    add_p.set_defaults(func=_cmd_recipients_add)

    rm_p = sub.add_parser("remove", help="Remove a recipient public key")
    rm_p.add_argument("key", metavar="PUBLIC_KEY")
    rm_p.set_defaults(func=_cmd_recipients_remove)
