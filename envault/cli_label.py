"""CLI sub-commands for vault label management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.label import LabelError, clear_label, load_label, set_label


def _cmd_label_set(ns: argparse.Namespace) -> None:
    """Attach a label to a vault."""
    try:
        entry = set_label(Path(ns.vault), ns.label)
        print(f"Label set: {entry['label']!r} → {ns.vault}")
    except LabelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_label_show(ns: argparse.Namespace) -> None:
    """Print the current label for a vault."""
    try:
        label = load_label(Path(ns.vault))
    except LabelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if label is None:
        print("(no label set)")
    else:
        print(label)


def _cmd_label_clear(ns: argparse.Namespace) -> None:
    """Remove the label from a vault."""
    try:
        removed = clear_label(Path(ns.vault))
    except LabelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if removed:
        print(f"Label cleared for {ns.vault}")
    else:
        print(f"No label was set for {ns.vault}")


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    """Build (and optionally attach) the *label* sub-command parser."""
    kwargs: dict = dict(
        description="Manage human-readable labels attached to vault files."
    )
    if parent is not None:
        parser = parent.add_parser("label", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envault label", **kwargs)

    sub = parser.add_subparsers(dest="label_cmd", required=True)

    # set
    p_set = sub.add_parser("set", help="Attach a label to a vault.")
    p_set.add_argument("vault", help="Path to the vault file.")
    p_set.add_argument("label", help="Label text (max 128 chars).")
    p_set.set_defaults(func=_cmd_label_set)

    # show
    p_show = sub.add_parser("show", help="Print the vault's current label.")
    p_show.add_argument("vault", help="Path to the vault file.")
    p_show.set_defaults(func=_cmd_label_show)

    # clear
    p_clear = sub.add_parser("clear", help="Remove the label from a vault.")
    p_clear.add_argument("vault", help="Path to the vault file.")
    p_clear.set_defaults(func=_cmd_label_clear)

    return parser
