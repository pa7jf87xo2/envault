"""Schedule periodic vault operations (e.g. auto-rotate, auto-pack)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

VALID_ACTIONS = ("rotate", "pack", "snapshot")


class ScheduleError(Exception):
    """Raised when a schedule operation fails."""


def schedule_path(vault: Path) -> Path:
    """Return the sidecar path for the schedule file."""
    return vault.with_suffix(".schedule.json")


def _now() -> datetime:
    return datetime.utcnow()


def set_schedule(
    vault: Path,
    action: str,
    interval_days: int,
    *,
    overwrite: bool = False,
) -> dict:
    """Persist a schedule entry for *action* on *vault*.

    Parameters
    ----------
    vault:          Path to the .vault file.
    action:         One of ``rotate``, ``pack``, or ``snapshot``.
    interval_days:  How many days between executions (must be >= 1).
    overwrite:      Replace an existing schedule if present.
    """
    if not vault.exists():
        raise ScheduleError(f"vault not found: {vault}")
    if action not in VALID_ACTIONS:
        raise ScheduleError(
            f"invalid action {action!r}; choose from {VALID_ACTIONS}"
        )
    if interval_days < 1:
        raise ScheduleError("interval_days must be >= 1")

    path = schedule_path(vault)
    schedules: dict = {}
    if path.exists():
        schedules = json.loads(path.read_text())

    if action in schedules and not overwrite:
        raise ScheduleError(
            f"schedule for {action!r} already exists; use overwrite=True"
        )

    entry = {
        "action": action,
        "interval_days": interval_days,
        "created_at": _now().isoformat(),
        "next_run": (_now() + timedelta(days=interval_days)).isoformat(),
    }
    schedules[action] = entry
    path.write_text(json.dumps(schedules, indent=2))
    return entry


def load_schedule(vault: Path) -> dict:
    """Return all schedules for *vault* as a dict keyed by action."""
    if not vault.exists():
        raise ScheduleError(f"vault not found: {vault}")
    path = schedule_path(vault)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ScheduleError(f"corrupt schedule file: {exc}") from exc


def remove_schedule(vault: Path, action: str) -> bool:
    """Remove the schedule for *action*. Returns True if removed, False if absent."""
    if not vault.exists():
        raise ScheduleError(f"vault not found: {vault}")
    path = schedule_path(vault)
    if not path.exists():
        return False
    schedules = json.loads(path.read_text())
    if action not in schedules:
        return False
    del schedules[action]
    path.write_text(json.dumps(schedules, indent=2))
    return True


def due_schedules(vault: Path) -> list[dict]:
    """Return schedules whose next_run is <= now."""
    schedules = load_schedule(vault)
    now = _now()
    return [
        entry
        for entry in schedules.values()
        if datetime.fromisoformat(entry["next_run"]) <= now
    ]
