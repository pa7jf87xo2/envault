"""envault notify — CLI subcommands for managing vault notifications."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.notify import NotifyError, load_config, set_webhook, save_config


def _cmd_notify_status(args: argparse.Namespace) -> None:
    """Show current notification configuration."""
    vault = Path(args.vault)
    try:
        cfg = load_config(vault)
    except NotifyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not cfg:
        print("no notification channels configured")
        return
    if "webhook" in cfg:
        print(f"webhook : {cfg['webhook']}")
    if cfg.get("desktop"):
        print("desktop : enabled")


def _cmd_notify_webhook(args: argparse.Namespace) -> None:
    """Set or clear the webhook URL."""
    vault = Path(args.vault)
    try:
        if args.url:
            set_webhook(vault, args.url)
            print(f"webhook set: {args.url}")
        else:
            cfg = load_config(vault)
            cfg.pop("webhook", None)
            save_config(vault, cfg)
            print("webhook cleared")
    except NotifyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_notify_desktop(args: argparse.Namespace) -> None:
    """Enable or disable desktop notifications."""
    vault = Path(args.vault)
    try:
        cfg = load_config(vault)
        if args.action == "enable":
            cfg["desktop"] = True
            save_config(vault, cfg)
            print("desktop notifications enabled")
        else:
            cfg.pop("desktop", None)
            save_config(vault, cfg)
            print("desktop notifications disabled")
    except NotifyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Manage vault event notifications"
    if parent is not None:
        p = parent.add_parser("notify", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envault notify", description=desc)

    p.add_argument("vault", help="path to .vault file")
    sub = p.add_subparsers(dest="notify_cmd", required=True)

    sub.add_parser("status", help="show notification config").set_defaults(func=_cmd_notify_status)

    wp = sub.add_parser("webhook", help="set or clear webhook URL")
    wp.add_argument("url", nargs="?", default="", help="webhook URL (omit to clear)")
    wp.set_defaults(func=_cmd_notify_webhook)

    dp = sub.add_parser("desktop", help="enable or disable desktop notifications")
    dp.add_argument("action", choices=["enable", "disable"])
    dp.set_defaults(func=_cmd_notify_desktop)

    return p
