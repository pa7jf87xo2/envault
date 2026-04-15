"""envault audit log.

Appends structured JSON-lines entries to ~/.envault/audit.log so users can
review which vaults were packed, unpacked, pushed, or pulled and when.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

Operation = Literal["pack", "unpack", "push", "pull", "init"]

DEFAULT_LOG_PATH = Path(os.environ.get("ENVAULT_AUDIT_LOG", "~/.envault/audit.log")).expanduser()


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def record(
    operation: Operation,
    *,
    vault: str | None = None,
    source: str | None = None,
    destination: str | None = None,
    extra: dict | None = None,
    log_path: Path = DEFAULT_LOG_PATH,
) -> dict:
    """Append one audit entry and return it."""
    entry: dict = {
        "ts": _now_iso(),
        "op": operation,
    }
    if vault is not None:
        entry["vault"] = vault
    if source is not None:
        entry["source"] = source
    if destination is not None:
        entry["destination"] = destination
    if extra:
        entry.update(extra)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

    return entry


def read_log(log_path: Path = DEFAULT_LOG_PATH) -> list[dict]:
    """Return all audit entries as a list of dicts (oldest first)."""
    if not log_path.exists():
        return []
    entries: list[dict] = []
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # skip corrupted lines
    return entries


def tail_log(n: int = 20, log_path: Path = DEFAULT_LOG_PATH) -> list[dict]:
    """Return the last *n* entries."""
    return read_log(log_path)[-n:]
