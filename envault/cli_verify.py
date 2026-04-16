"""CLI sub-commands for vault verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envault.verify import VerifyError, checksum, verify


def _cmd_checksum(args: argparse.Namespace) -> None:
    """Print the SHA-256 checksum of a vault file."""
    try:
        digest = checksum(Path(args.vault))
    except VerifyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps({"vault": args.vault, "sha256": digest}))
    else:
        print(f"{digest}  {args.vault}")


def _cmd_verify(args: argparse.Namespace) -> None:
    """Verify that a vault can be decrypted and report its contents summary."""
    try:
        result = verify(Path(args.vault), Path(args.identity))
    except VerifyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result))
        if not result["ok"]:
            sys.exit(1)
        return

    if result["ok"]:
        print(f"✓  vault verified  ({args.vault})")
        print(f"   checksum : {result['checksum']}")
        print(f"   keys     : {', '.join(result['keys']) or '(none)'}")
    else:
        print(f"✗  verification failed: {result['error']}", file=sys.stderr)
        sys.exit(1)


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    """Build (or attach) the *verify* sub-command parser."""
    if parent is not None:
        parser = parent.add_parser("verify", help="Verify and inspect a vault file")
    else:
        parser = argparse.ArgumentParser(prog="envault verify")

    sub = parser.add_subparsers(dest="verify_cmd", required=True)

    # --- checksum ---
    p_checksum = sub.add_parser("checksum", help="Print SHA-256 checksum of a vault")
    p_checksum.add_argument("vault", help="Path to the vault file")
    p_checksum.add_argument("--json", action="store_true", help="Output as JSON")
    p_checksum.set_defaults(func=_cmd_checksum)

    # --- verify ---
    p_verify = sub.add_parser("check", help="Decrypt and verify a vault")
    p_verify.add_argument("vault", help="Path to the vault file")
    p_verify.add_argument("--identity", default="~/.config/envault/identity.txt",
                          help="Path to age identity file (default: %(default)s)")
    p_verify.add_argument("--json", action="store_true", help="Output as JSON")
    p_verify.set_defaults(func=_cmd_verify)

    return parser
