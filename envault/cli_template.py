"""CLI sub-commands for template rendering."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.template import TemplateError, render_template


def _cmd_template_render(args: argparse.Namespace) -> int:
    """Render a template file using decrypted vault values."""
    vault = Path(args.vault)
    identity = Path(args.identity)
    template = Path(args.template)
    output = Path(args.output) if args.output else None

    try:
        rendered = render_template(
            template,
            vault,
            identity,
            output,
            strict=not args.loose,
        )
    except TemplateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if output is None:
        print(rendered, end="")
    else:
        print(f"Rendered template written to {output}")

    return 0


def build_parser(
    parent: "argparse._SubParsersAction[argparse.ArgumentParser] | None" = None,
) -> argparse.ArgumentParser:
    desc = "Render a template by substituting {{ KEY }} placeholders from a vault."
    if parent is not None:
        parser = parent.add_parser("template", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="envault template", description=desc)

    sub = parser.add_subparsers(dest="template_cmd", metavar="COMMAND")

    render_p = sub.add_parser("render", help="Render a template file.")
    render_p.add_argument("template", help="Path to the template file.")
    render_p.add_argument(
        "-v", "--vault", default=".env.vault", help="Vault file (default: .env.vault)."
    )
    render_p.add_argument(
        "-i",
        "--identity",
        default="~/.config/envault/identity.txt",
        help="Age identity file.",
    )
    render_p.add_argument(
        "-o", "--output", default=None, help="Write rendered output to this file."
    )
    render_p.add_argument(
        "--loose",
        action="store_true",
        help="Do not raise an error for undefined keys; leave placeholders as-is.",
    )
    render_p.set_defaults(func=_cmd_template_render)

    return parser


if __name__ == "__main__":  # pragma: no cover
    _parser = build_parser()
    _args = _parser.parse_args()
    if hasattr(_args, "func"):
        sys.exit(_args.func(_args))
    else:
        _parser.print_help()
