"""CLI sub-commands for vault watermarking."""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

from envault.watermark import WatermarkError, set_watermark, load_watermark, clear_watermark


def _cmd_watermark_set(args: argparse.Namespace) -> None:
    machine = args.machine or _hostname()
    try:
        entry = set_watermark(
            Path(args.vault),
            author=args.author,
            machine=machine,
            note=args.note or None,
        )
    except WatermarkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Watermark set — author={entry['author']}  stamped_at={entry['stamped_at']}")
    if "machine" in entry:
        print(f"  machine : {entry['machine']}")
    if "note" in entry:
        print(f"  note    : {entry['note']}")


def _cmd_watermark_show(args: argparse.Namespace) -> None:
    try:
        wm = load_watermark(Path(args.vault))
    except WatermarkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if wm is None:
        print("No watermark found.")
        return

    print(f"author     : {wm['author']}")
    print(f"stamped_at : {wm['stamped_at']}")
    if "machine" in wm:
        print(f"machine    : {wm['machine']}")
    if "note" in wm:
        print(f"note       : {wm['note']}")


def _cmd_watermark_clear(args: argparse.Namespace) -> None:
    try:
        removed = clear_watermark(Path(args.vault))
    except WatermarkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if removed:
        print("Watermark cleared.")
    else:
        print("No watermark to clear.")


def _hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Embed or inspect a provenance watermark on a vault file."
    if parent is not None:
        parser = parent.add_parser("watermark", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="envault watermark", description=desc)

    sub = parser.add_subparsers(dest="watermark_cmd", required=True)

    p_set = sub.add_parser("set", help="Stamp a watermark onto the vault.")
    p_set.add_argument("vault", help="Path to the vault file.")
    p_set.add_argument("--author", required=True, help="Author / identity string.")
    p_set.add_argument("--machine", default=None, help="Machine name (defaults to hostname).")
    p_set.add_argument("--note", default=None, help="Optional free-text note.")
    p_set.set_defaults(func=_cmd_watermark_set)

    p_show = sub.add_parser("show", help="Display the current watermark.")
    p_show.add_argument("vault", help="Path to the vault file.")
    p_show.set_defaults(func=_cmd_watermark_show)

    p_clear = sub.add_parser("clear", help="Remove the watermark sidecar.")
    p_clear.add_argument("vault", help="Path to the vault file.")
    p_clear.set_defaults(func=_cmd_watermark_clear)

    return parser
