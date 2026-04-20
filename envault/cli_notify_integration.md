# envault notify — integration guide

## Overview

`envault notify` lets you attach event notifications to a vault file.
Two channels are supported:

| Channel   | Description                                      |
|-----------|--------------------------------------------------|
| `webhook` | HTTP POST JSON payload to any URL                |
| `desktop` | OS desktop notification (macOS / Linux)          |

Configuration is stored alongside the vault as `<vault>.notify.json`.

---

## Subcommands

### `envault notify <vault> status`
Print the current notification configuration.

```
$ envault notify prod.vault status
webhook : https://hooks.slack.com/services/...
desktop : enabled
```

### `envault notify <vault> webhook <url>`
Set the webhook endpoint.

```bash
envault notify prod.vault webhook https://hooks.slack.com/services/T000/B000/xxx
```

Omit the URL to **clear** the webhook:

```bash
envault notify prod.vault webhook
```

### `envault notify <vault> desktop enable|disable`
Toggle desktop notifications.

```bash
envault notify prod.vault desktop enable
envault notify prod.vault desktop disable
```

---

## Webhook payload

```json
{
  "vault": "/home/user/project/prod.vault",
  "event": "pack",
  "detail": "packed by alice"
}
```

---

## Programmatic use

```python
from pathlib import Path
from envault.notify import send, set_webhook

vault = Path("prod.vault")
set_webhook(vault, "https://hooks.example.com/abc")

# Call after a pack/unpack/rotate operation:
sent = send(vault, "rotate", detail="re-keyed with new identity")
print("notified via:", sent)
```

---

## Notes

- Desktop notifications are best-effort; unsupported platforms silently skip them.
- The webhook call has a 5-second timeout; failures raise `NotifyError`.
- The `.notify.json` file should be added to `.gitignore` to avoid leaking URLs.
