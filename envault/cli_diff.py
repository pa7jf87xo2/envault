"""CLI sub-command: ``envault diff`` — compare vault snapshot with live .env."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.config import load_config
from envault.diff import DiffError, diff_vault, summarise_diff


def _cmd_diff(args: argparse.Namespace) -> int:
    """Entry point for the ``diff`` sub-command.

    Returns an exit code: 0 = no differences, 1 = differences found, 2 = error.
    """
    try:
        cfg = load_config(Path(args.config))
    except Exception as exc:
        print(f"error: could not load config: {exc}", file=sys.stderr)
        return 2

    vault_path = Path(args.vault) if args.vault else Path(cfg.vault_path)
    live_path = Path(args.env) if args.env else Path(cfg.env_path)
    identity_path = Path(args.identity) if args.identity else Path(cfg.identity_path)

    try:
        changed, diff_text = diff_vault(vault_path, live_path, identity_path)
    except DiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not changed:
        print("No differences between vault and live .env file.")
        return 0

    additions, deletions = summarise_diff(diff_text)
    print(diff_text, end="")
    print(f"\n--- {additions} addition(s), {deletions} deletion(s) ---")
    return 1


def build_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``diff`` sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "diff",
        help="Show differences between the encrypted vault and the live .env file.",
    )
    p.add_argument("--vault", metavar="FILE", help="Path to the vault file (overrides config).")
    p.add_argument("--env", metavar="FILE", help="Path to the live .env file (overrides config).")
    p.add_argument("--identity", metavar="FILE", help="Path to the age identity file (overrides config).")
    p.add_argument("--config", metavar="FILE", default=".envault.toml", help="Config file path.")
    p.set_defaults(func=_cmd_diff)
