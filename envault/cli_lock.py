"""CLI sub-commands for vault locking."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.lock import LockError, acquire, is_locked, release


def _cmd_lock_acquire(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        lp = acquire(vault, timeout=args.timeout)
        print(f"Lock acquired: {lp}")
    except LockError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_lock_release(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    try:
        release(vault)
        print(f"Lock released for {vault}")
    except LockError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_lock_status(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    if is_locked(vault):
        print(f"locked")
    else:
        print(f"unlocked")


def build_parser(sub: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    if sub is not None:
        p = sub.add_parser("lock", help="manage vault locks")
    else:
        p = argparse.ArgumentParser(prog="envault lock")

    sp = p.add_subparsers(dest="lock_cmd", required=True)

    acq = sp.add_parser("acquire", help="acquire lock on a vault")
    acq.add_argument("vault", help="path to vault file")
    acq.add_argument("--timeout", type=float, default=5.0, help="seconds to wait")
    acq.set_defaults(func=_cmd_lock_acquire)

    rel = sp.add_parser("release", help="release lock on a vault")
    rel.add_argument("vault", help="path to vault file")
    rel.set_defaults(func=_cmd_lock_release)

    st = sp.add_parser("status", help="show lock status of a vault")
    st.add_argument("vault", help="path to vault file")
    st.set_defaults(func=_cmd_lock_status)

    return p
