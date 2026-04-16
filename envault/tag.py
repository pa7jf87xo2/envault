"""Vault tagging — attach and query freeform tags on vault files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

TAGS_SUFFIX = ".tags.json"


class TagError(Exception):
    """Raised when a tagging operation fails."""


def tags_path(vault: Path) -> Path:
    return vault.parent / (vault.name + TAGS_SUFFIX)


def load_tags(vault: Path) -> List[str]:
    if not vault.exists():
        raise TagError(f"Vault not found: {vault}")
    tp = tags_path(vault)
    if not tp.exists():
        return []
    try:
        data = json.loads(tp.read_text())
    except json.JSONDecodeError as exc:
        raise TagError(f"Corrupt tags file: {exc}") from exc
    if not isinstance(data, list):
        raise TagError("Tags file must contain a JSON array")
    return [str(t) for t in data]


def add_tag(vault: Path, tag: str) -> List[str]:
    tag = tag.strip()
    if not tag:
        raise TagError("Tag must not be empty")
    current = load_tags(vault)
    if tag in current:
        return current
    current.append(tag)
    tags_path(vault).write_text(json.dumps(current, indent=2))
    return current


def remove_tag(vault: Path, tag: str) -> List[str]:
    current = load_tags(vault)
    if tag not in current:
        raise TagError(f"Tag not found: {tag!r}")
    current.remove(tag)
    tags_path(vault).write_text(json.dumps(current, indent=2))
    return current


def list_tags(vault: Path) -> List[str]:
    return load_tags(vault)
