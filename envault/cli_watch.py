"""cli_watch.py — CLI sub-commands for the watch feature."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.watch import watch, WatchError
from envault.identity import load_public_key, IdentityError
from envault.config import load_config, ConfigError


def _cmd_watch(ns: argparse.Namespace) -> None:
    """Start watching an env file and repack on every change."""
    env_file = Path(ns.env_file)
    vault_file = Path(ns.vault) if ns.vault else env_file.with_suffix(".vault")

    # Resolve public key: CLI flag > config > identity file
    public_key: str | None = ns.public_key

    if public_key is None:
        try:
            cfg = load_config()
            public_key = cfg.public_key
        except (ConfigError, AttributeError):
            pass

    if public_key is None:
        try:
            public_key = load_public_key()
        except IdentityError as exc:
            print(f"error: cannot determine public key — {exc}", file=sys.stderr)
            sys.exit(1)

    interval: float = ns.interval
    print(
        f"Watching {env_file} (interval={interval}s) — press Ctrl-C to stop.",
        flush=True,
    )

    def _on_change(vault: Path) -> None:
        print(f"  repacked → {vault}", flush=True)

    try:
        watch(
            env_file,
            vault_file,
            public_key,
            interval=interval,
            on_change=_on_change,
        )
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    except WatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    desc = "Watch a .env file and repack the vault on every change."
    if parent is not None:
        p = parent.add_parser("watch", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="envault watch", description=desc)

    p.add_argument("env_file", metavar="ENV_FILE", help="Path to the .env file to monitor.")
    p.add_argument("-v", "--vault", metavar="VAULT", default=None, help="Vault output path (default: <env_file>.vault).")
    p.add_argument("-k", "--public-key", metavar="KEY", default=None, dest="public_key", help="age public key for encryption.")
    p.add_argument("-i", "--interval", metavar="SECONDS", type=float, default=1.0, help="Polling interval in seconds (default: 1.0).")
    p.set_defaults(func=_cmd_watch)
    return p
