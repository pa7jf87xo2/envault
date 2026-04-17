"""CLI sub-commands for vault signing."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.sign import SignError, sign, verify_signature, clear_signature


def _cmd_sign(ns: argparse.Namespace) -> None:
    try:
        entry = sign(Path(ns.vault), ns.secret)
        print(f"signed: {entry['hmac_sha256']}")
    except SignError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def _cmd_verify(ns: argparse.Namespace) -> None:
    try:
        ok = verify_signature(Path(ns.vault), ns.secret)
    except SignError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if ok:
        print("signature ok")
    else:
        print("signature mismatch", file=sys.stderr)
        sys.exit(1)


def _cmd_clear(ns: argparse.Namespace) -> None:
    removed = clear_signature(Path(ns.vault))
    if removed:
        print("signature cleared")
    else:
        print("no signature file found")


def build_parser(sub: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    if sub is None:
        parser = argparse.ArgumentParser(prog="envault sign")
        sub = parser.add_subparsers(dest="sign_cmd")
    else:
        parser = sub.add_parser("sign", help="vault signing commands")
        sub = parser.add_subparsers(dest="sign_cmd")

    p_sign = sub.add_parser("create", help="sign a vault")
    p_sign.add_argument("vault")
    p_sign.add_argument("--secret", required=True)
    p_sign.set_defaults(func=_cmd_sign)

    p_verify = sub.add_parser("verify", help="verify vault signature")
    p_verify.add_argument("vault")
    p_verify.add_argument("--secret", required=True)
    p_verify.set_defaults(func=_cmd_verify)

    p_clear = sub.add_parser("clear", help="remove vault signature")
    p_clear.add_argument("vault")
    p_clear.set_defaults(func=_cmd_clear)

    return parser
