"""CLI sub-commands for vault tagging."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.tag import TagError, add_tag, list_tags, remove_tag


def _cmd_tag_list(args: argparse.Namespace) -> None:
    try:
        tags = list_tags(Path(args.vault))
    except TagError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not tags:
        print("(no tags)")
    else:
        for t in tags:
            print(t)


def _cmd_tag_add(args: argparse.Namespace) -> None:
    try:
        result = add_tag(Path(args.vault), args.tag)
    except TagError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Tags: {', '.join(result)}")


def _cmd_tag_remove(args: argparse.Namespace) -> None:
    try:
        result = remove_tag(Path(args.vault), args.tag)
    except TagError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    remaining = ', '.join(result) if result else '(none)'
    print(f"Tags: {remaining}")


def build_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = parent.add_parser("tag", help="Manage vault tags")
    sp = p.add_subparsers(dest="tag_cmd", required=True)

    for sub_name, handler, extra in [
        ("list", _cmd_tag_list, []),
        ("add", _cmd_tag_add, [("tag", {"help": "Tag to add"})]),
        ("remove", _cmd_tag_remove, [("tag", {"help": "Tag to remove"})]),
    ]:
        s = sp.add_parser(sub_name)
        s.add_argument("vault", help="Path to vault file")
        for name, kwargs in extra:
            s.add_argument(name, **kwargs)
        s.set_defaults(func=handler)
