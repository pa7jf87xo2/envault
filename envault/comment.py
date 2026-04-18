"""Inline comments attached to vault keys."""
from __future__ import annotations

import json
from pathlib import Path

COMMENT_SUFFIX = ".comments.json"


class CommentError(Exception):
    pass


def comments_path(vault: Path) -> Path:
    return vault.with_suffix(COMMENT_SUFFIX)


def load_comments(vault: Path) -> dict[str, str]:
    if not vault.exists():
        raise CommentError(f"vault not found: {vault}")
    cp = comments_path(vault)
    if not cp.exists():
        return {}
    try:
        return json.loads(cp.read_text())
    except json.JSONDecodeError as exc:
        raise CommentError(f"corrupt comments file: {exc}") from exc


def set_comment(vault: Path, key: str, comment: str) -> None:
    if not vault.exists():
        raise CommentError(f"vault not found: {vault}")
    if not key.strip():
        raise CommentError("key must not be empty")
    data = load_comments(vault)
    data[key] = comment
    comments_path(vault).write_text(json.dumps(data, indent=2))


def remove_comment(vault: Path, key: str) -> None:
    if not vault.exists():
        raise CommentError(f"vault not found: {vault}")
    data = load_comments(vault)
    if key not in data:
        raise CommentError(f"no comment for key: {key}")
    del data[key]
    cp = comments_path(vault)
    if data:
        cp.write_text(json.dumps(data, indent=2))
    else:
        cp.unlink(missing_ok=True)


def get_comment(vault: Path, key: str) -> str | None:
    return load_comments(vault).get(key)
