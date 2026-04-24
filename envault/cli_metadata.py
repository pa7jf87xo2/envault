"""CLI sub-commands for vault metadata management."""

from __future__ import annotations

import argparse
import json
import sys

from envault.metadata import MetadataError, clear_metadata, load_metadata, remove_metadata, set_metadata
from pathlib import Path


def _cmd_metadata_list(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        data = load_metadata(vault)
    except MetadataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not data:
        print("(no metadata)")
        return
    for key, value in sorted(data.items()):
        print(f"{key} = {json.dumps(value)}")


def _cmd_metadata_set(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        value: object = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value  # treat as plain string
    try:
        set_metadata(vault, args.key, value)
    except MetadataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"metadata '{args.key}' set on {vault}")


def _cmd_metadata_remove(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        remove_metadata(vault, args.key)
    except MetadataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"metadata '{args.key}' removed from {vault}")


def _cmd_metadata_clear(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        clear_metadata(vault)
    except MetadataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"all metadata cleared for {vault}")


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs: dict = dict(description="Manage vault metadata annotations.")
    parser: argparse.ArgumentParser = (
        parent.add_parser("metadata", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    )
    sub = parser.add_subparsers(dest="metadata_cmd", required=True)

    for name, fn, extra in [
        ("list", _cmd_metadata_list, []),
        ("set", _cmd_metadata_set, [("key",), ("value",)]),
        ("remove", _cmd_metadata_remove, [("key",)]),
        ("clear", _cmd_metadata_clear, []),
    ]:
        p = sub.add_parser(name)
        p.add_argument("vault", help="path to .vault file")
        for pos in extra:
            p.add_argument(*pos)
        p.set_defaults(func=fn)

    return parser


if __name__ == "__main__":  # pragma: no cover
    _parser = build_parser()
    _args = _parser.parse_args()
    _args.func(_args)
