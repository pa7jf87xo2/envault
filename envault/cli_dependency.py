"""CLI sub-commands for managing vault dependencies."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.dependency import (
    DependencyError,
    add_dependency,
    clear_dependencies,
    load_dependencies,
    remove_dependency,
)


def _cmd_dependency_list(ns: argparse.Namespace) -> None:
    try:
        deps = load_dependencies(Path(ns.vault))
    except DependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not deps:
        print("No dependencies recorded.")
    else:
        for d in deps:
            print(d)


def _cmd_dependency_add(ns: argparse.Namespace) -> None:
    try:
        deps = add_dependency(Path(ns.vault), ns.dep)
    except DependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Added dependency '{ns.dep}'. Total: {len(deps)}.")


def _cmd_dependency_remove(ns: argparse.Namespace) -> None:
    try:
        remove_dependency(Path(ns.vault), ns.dep)
    except DependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Removed dependency '{ns.dep}'.")


def _cmd_dependency_clear(ns: argparse.Namespace) -> None:
    try:
        clear_dependencies(Path(ns.vault))
    except DependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print("All dependencies cleared.")


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Manage vault dependencies.")
    if parent is not None:
        p = parent.add_parser("dependency", **kwargs)
    else:
        p = argparse.ArgumentParser(prog="envault dependency", **kwargs)

    p.add_argument("--vault", default=".env.vault", help="Path to the vault file.")
    sub = p.add_subparsers(dest="dep_cmd", required=True)

    sub.add_parser("list", help="List dependencies.").set_defaults(func=_cmd_dependency_list)

    add_p = sub.add_parser("add", help="Add a dependency.")
    add_p.add_argument("dep", help="Path of the vault to depend on.")
    add_p.set_defaults(func=_cmd_dependency_add)

    rm_p = sub.add_parser("remove", help="Remove a dependency.")
    rm_p.add_argument("dep", help="Path of the dependency to remove.")
    rm_p.set_defaults(func=_cmd_dependency_remove)

    sub.add_parser("clear", help="Remove all dependencies.").set_defaults(func=_cmd_dependency_clear)

    return p
