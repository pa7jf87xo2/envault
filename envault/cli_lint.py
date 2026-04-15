"""CLI sub-command: envault lint"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.lint import LintError, lint_file


def _cmd_lint(args: argparse.Namespace) -> None:
    env_path = Path(args.env_file)
    try:
        result = lint_file(env_path)
    except LintError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not result.issues:
        print(f"✓ {env_path}: no issues found")
        return

    for issue in result.issues:
        icon = "✗" if issue.severity == "error" else "⚠"
        print(f"{icon} line {issue.line_no}: [{issue.severity}] {issue.message}")

    summary = f"{result.error_count} error(s), {result.warning_count} warning(s)"
    if result.ok:
        print(f"\n{env_path}: {summary} (warnings only)")
    else:
        print(f"\n{env_path}: {summary}", file=sys.stderr)
        sys.exit(2)


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Lint a .env file for common issues."
    if subparsers is not None:
        parser = subparsers.add_parser("lint", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="envault lint", description=desc)

    parser.add_argument(
        "env_file",
        nargs="?",
        default=".env",
        help="Path to the .env file to lint (default: .env)",
    )
    parser.set_defaults(func=_cmd_lint)
    return parser
