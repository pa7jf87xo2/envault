"""history.py – track pack/unpack operations for a vault."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HistoryError(Exception):
    pass


def history_path(vault: Path) -> Path:
    return vault.with_suffix(vault.suffix + ".history.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_event(
    vault: Path,
    action: str,
    *,
    user: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    if not vault.exists():
        raise HistoryError(f"vault not found: {vault}")
    entry: dict[str, Any] = {"ts": _now_iso(), "action": action}
    if user:
        entry["user"] = user
    if note:
        entry["note"] = note
    hp = history_path(vault)
    with hp.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def load_history(vault: Path) -> list[dict[str, Any]]:
    if not vault.exists():
        raise HistoryError(f"vault not found: {vault}")
    hp = history_path(vault)
    if not hp.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in hp.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise HistoryError(f"corrupt history file: {exc}") from exc
    return entries


def clear_history(vault: Path) -> None:
    if not vault.exists():
        raise HistoryError(f"vault not found: {vault}")
    hp = history_path(vault)
    if hp.exists():
        hp.unlink()
