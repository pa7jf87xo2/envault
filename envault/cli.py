"""cli.py — Command-line interface for envault.

Entry-point commands
--------------------
  envault init          Initialise a local age identity.
  envault pack          Encrypt a .env file into a vault archive.
  envault unpack        Decrypt a vault archive back to a .env file.
  envault push          Push the vault file to a destination.
  envault pull          Pull a vault file from a source.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.identity import IdentityError, init_identity, load_public_key
from envault.sync import SyncError, pull, push
from envault.vault import VaultError, pack, unpack


def _cmd_init(args: argparse.Namespace) -> int:
    try:
        init_identity(Path(args.identity), overwrite=args.force)
        pub = load_public_key(Path(args.identity))
        print(f"Identity initialised.\nPublic key: {pub}")
    except IdentityError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_pack(args: argparse.Namespace) -> int:
    try:
        pub = load_public_key(Path(args.identity))
        vault_path = pack(
            source=Path(args.env_file),
            recipient=pub,
            vault_path=Path(args.output) if args.output else None,
        )
        print(f"Packed → {vault_path}")
    except (IdentityError, VaultError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_unpack(args: argparse.Namespace) -> int:
    try:
        env_path = unpack(
            vault_path=Path(args.vault_file),
            identity_path=Path(args.identity),
            dest=Path(args.output) if args.output else None,
        )
        print(f"Unpacked → {env_path}")
    except VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_push(args: argparse.Namespace) -> int:
    try:
        push(Path(args.vault_file), args.destination)
        print(f"Pushed {args.vault_file} → {args.destination}")
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_pull(args: argparse.Namespace) -> int:
    try:
        pull(args.source, Path(args.output))
        print(f"Pulled {args.source} → {args.output}")
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Securely encrypt and sync .env files using age encryption.",
    )
    parser.add_argument(
        "--identity",
        default="~/.config/envault/identity.txt",
        help="Path to age identity file (default: %(default)s)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialise a local age identity.")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing identity.")

    # pack
    p_pack = sub.add_parser("pack", help="Encrypt a .env file into a vault archive.")
    p_pack.add_argument("env_file", help="Path to the .env file to encrypt.")
    p_pack.add_argument("-o", "--output", help="Output vault file path.")

    # unpack
    p_unpack = sub.add_parser("unpack", help="Decrypt a vault archive.")
    p_unpack.add_argument("vault_file", help="Path to the .vault file.")
    p_unpack.add_argument("-o", "--output", help="Output .env file path.")

    # push
    p_push = sub.add_parser("push", help="Push vault file to a destination.")
    p_push.add_argument("vault_file", help="Local vault file to push.")
    p_push.add_argument("destination", help="Local directory or scp-style remote.")

    # pull
    p_pull = sub.add_parser("pull", help="Pull a vault file from a source.")
    p_pull.add_argument("source", help="Local path or scp-style remote file.")
    p_pull.add_argument("output", help="Local path to write the vault file.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "init": _cmd_init,
        "pack": _cmd_pack,
        "unpack": _cmd_unpack,
        "push": _cmd_push,
        "pull": _cmd_pull,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
