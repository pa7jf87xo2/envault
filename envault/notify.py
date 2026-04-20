"""envault.notify — desktop/webhook notifications for vault events."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


class NotifyError(Exception):
    """Raised when a notification cannot be delivered."""


_CHANNELS = ("webhook", "desktop")


def notify_path(vault: Path) -> Path:
    """Return the path to the notifications config file for *vault*."""
    return vault.with_suffix(".notify.json")


def load_config(vault: Path) -> dict:
    """Load notification config for *vault*.  Returns {} when no file exists."""
    if not vault.exists():
        raise NotifyError(f"vault not found: {vault}")
    p = notify_path(vault)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise NotifyError(f"corrupt notify config: {exc}") from exc


def save_config(vault: Path, cfg: dict) -> None:
    """Persist notification config for *vault*."""
    if not vault.exists():
        raise NotifyError(f"vault not found: {vault}")
    notify_path(vault).write_text(json.dumps(cfg, indent=2))


def set_webhook(vault: Path, url: str) -> None:
    """Configure a webhook URL for *vault* notifications."""
    if not url.startswith(("http://", "https://")):
        raise NotifyError(f"invalid webhook URL: {url}")
    cfg = load_config(vault)
    cfg["webhook"] = url
    save_config(vault, cfg)


def send(
    vault: Path,
    event: str,
    detail: Optional[str] = None,
) -> list[str]:
    """Send notifications for *event* using the channels configured for *vault*.

    Returns a list of channel names that were successfully notified.
    """
    cfg = load_config(vault)
    sent: list[str] = []

    webhook_url = cfg.get("webhook")
    if webhook_url:
        payload = json.dumps({"vault": str(vault), "event": event, "detail": detail}).encode()
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5):
                pass
            sent.append("webhook")
        except urllib.error.URLError as exc:
            raise NotifyError(f"webhook delivery failed: {exc}") from exc

    if cfg.get("desktop"):
        _send_desktop(event, detail or str(vault))
        sent.append("desktop")

    return sent


def _send_desktop(event: str, body: str) -> None:  # pragma: no cover
    """Best-effort desktop notification (no-op on unsupported platforms)."""
    import shutil, subprocess, sys
    if sys.platform == "darwin" and shutil.which("osascript"):
        msg = f"envault: {event} — {body}"
        subprocess.run(["osascript", "-e", f'display notification "{msg}"'], check=False)
    elif shutil.which("notify-send"):
        subprocess.run(["notify-send", "envault", f"{event}: {body}"], check=False)
