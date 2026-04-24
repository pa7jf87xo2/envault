"""CLI sub-commands for managing vault schedules."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.schedule import ScheduleError, due_schedules, load_schedule, remove_schedule, set_schedule


def _cmd_schedule_set(args: argparse.Namespace) -> None:
    """envault schedule set <vault> <action> <interval_days>"""
    try:
        entry = set_schedule(
            Path(args.vault),
            args.action,
            args.interval_days,
            overwrite=args.overwrite,
        )
        print(
            f"Scheduled '{entry['action']}' every {entry['interval_days']} day(s). "
            f"Next run: {entry['next_run']}"
        )
    except ScheduleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_schedule_list(args: argparse.Namespace) -> None:
    """envault schedule list <vault>"""
    try:
        schedules = load_schedule(Path(args.vault))
    except ScheduleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not schedules:
        print("No schedules configured.")
        return

    for action, entry in schedules.items():
        print(
            f"{action:12s}  every {entry['interval_days']:3d}d  "
            f"next: {entry['next_run']}"
        )


def _cmd_schedule_remove(args: argparse.Namespace) -> None:
    """envault schedule remove <vault> <action>"""
    try:
        removed = remove_schedule(Path(args.vault), args.action)
    except ScheduleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if removed:
        print(f"Removed schedule for '{args.action}'.")
    else:
        print(f"No schedule found for '{args.action}'.")


def _cmd_schedule_due(args: argparse.Namespace) -> None:
    """envault schedule due <vault> — list overdue schedules."""
    try:
        due = due_schedules(Path(args.vault))
    except ScheduleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not due:
        print("No schedules are currently due.")
        return
    for entry in due:
        print(f"{entry['action']:12s}  overdue since {entry['next_run']}")


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[name-defined]
    if parent is not None:
        p = parent.add_parser("schedule", help="Manage periodic vault schedules")
    else:
        p = argparse.ArgumentParser(prog="envault schedule")

    sub = p.add_subparsers(dest="schedule_cmd", required=True)

    # set
    ps = sub.add_parser("set", help="Create or update a schedule")
    ps.add_argument("vault")
    ps.add_argument("action", choices=("rotate", "pack", "snapshot"))
    ps.add_argument("interval_days", type=int)
    ps.add_argument("--overwrite", action="store_true", default=False)
    ps.set_defaults(func=_cmd_schedule_set)

    # list
    pl = sub.add_parser("list", help="List all schedules")
    pl.add_argument("vault")
    pl.set_defaults(func=_cmd_schedule_list)

    # remove
    pr = sub.add_parser("remove", help="Remove a schedule")
    pr.add_argument("vault")
    pr.add_argument("action")
    pr.set_defaults(func=_cmd_schedule_remove)

    # due
    pd = sub.add_parser("due", help="Show overdue schedules")
    pd.add_argument("vault")
    pd.set_defaults(func=_cmd_schedule_due)

    return p
