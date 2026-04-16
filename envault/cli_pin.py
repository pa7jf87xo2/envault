"""CLI sub-commands for vault pinning."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.pin import PinError, pin, load_pin, clear_pin, is_pinned
from envault.verify import checksum


def _cmd_pin_set(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        cs = checksum(vault)
        entry = pin(vault, args.snapshot, cs)
        print(f"Pinned {vault.name} → snapshot={entry['snapshot']} checksum={entry['checksum']}")
    except PinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_pin_show(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        data = load_pin(vault)
        print(f"snapshot : {data['snapshot']}")
        print(f"checksum : {data['checksum']}")
    except PinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_pin_clear(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        clear_pin(vault)
        print(f"Pin cleared for {vault.name}.")
    except PinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_pin_status(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    if is_pinned(vault):
        print(f"{vault.name} is pinned.")
    else:
        print(f"{vault.name} is not pinned.")


def build_parser(sub: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Manage vault pins"
    if sub is not None:
        p = sub.add_parser("pin", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envault pin", description=desc)

    cmds = p.add_subparsers(dest="pin_cmd", required=True)

    for name, fn, help_text in [
        ("set", _cmd_pin_set, "Pin vault to current checksum"),
        ("show", _cmd_pin_show, "Show current pin info"),
        ("clear", _cmd_pin_clear, "Remove pin"),
        ("status", _cmd_pin_status, "Check if vault is pinned"),
    ]:
        sp = cmds.add_parser(name, help=help_text)
        sp.add_argument("vault", help="Path to vault file")
        if name == "set":
            sp.add_argument("snapshot", help="Snapshot name to record")
        sp.set_defaults(func=fn)

    return p
