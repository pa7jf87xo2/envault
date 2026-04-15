"""CLI sub-commands for vault snapshots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.snapshot import SnapshotError, list_snapshots, restore_snapshot, save_snapshot


def _cmd_snapshot_save(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        snap = save_snapshot(vault, name=args.name or None)
        print(f"Snapshot saved: {snap}")
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_snapshot_list(args: argparse.Namespace) -> None:
    base = Path(args.base)
    snaps = list_snapshots(base, vault_stem=args.stem or None)
    if not snaps:
        print("No snapshots found.")
        return
    for snap in snaps:
        print(snap.name)


def _cmd_snapshot_restore(args: argparse.Namespace) -> None:
    snapshot = Path(args.snapshot)
    dest = Path(args.dest)
    try:
        restore_snapshot(snapshot, dest, overwrite=args.overwrite)
        print(f"Restored {snapshot.name} → {dest}")
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    if parent is not None:
        parser = parent.add_parser("snapshot", help="Manage vault snapshots")
    else:
        parser = argparse.ArgumentParser(prog="envault snapshot")

    sub = parser.add_subparsers(dest="snapshot_cmd", required=True)

    # save
    p_save = sub.add_parser("save", help="Save a snapshot of a vault file")
    p_save.add_argument("vault", help="Path to the .vault file")
    p_save.add_argument("--name", default="", help="Optional snapshot label")
    p_save.set_defaults(func=_cmd_snapshot_save)

    # list
    p_list = sub.add_parser("list", help="List available snapshots")
    p_list.add_argument("base", help="Directory containing the snapshots folder")
    p_list.add_argument("--stem", default="", help="Filter by vault stem name")
    p_list.set_defaults(func=_cmd_snapshot_list)

    # restore
    p_restore = sub.add_parser("restore", help="Restore a snapshot to a vault path")
    p_restore.add_argument("snapshot", help="Path to the snapshot file")
    p_restore.add_argument("dest", help="Destination vault path")
    p_restore.add_argument(
        "--overwrite", action="store_true", help="Overwrite destination if it exists"
    )
    p_restore.set_defaults(func=_cmd_snapshot_restore)

    return parser
