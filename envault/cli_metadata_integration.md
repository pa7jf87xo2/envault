# Vault Metadata — Integration Guide

The `metadata` sub-command lets you attach arbitrary key/value annotations to
any vault file without touching its encrypted contents.  Annotations are stored
in a JSON sidecar file alongside the vault (e.g. `my.vault.meta.json`).

## Quick start

```bash
# Attach metadata to a vault
envault metadata set secrets.vault env production
envault metadata set secrets.vault owner alice
envault metadata set secrets.vault priority 1          # JSON numbers work too
envault metadata set secrets.vault tags '["web","db"]' # JSON arrays work too

# List all metadata
envault metadata list secrets.vault
# env = "production"
# owner = "alice"
# priority = 1
# tags = ["web", "db"]

# Remove a single key
envault metadata remove secrets.vault owner

# Wipe all metadata
envault metadata clear secrets.vault
```

## Value encoding

Values are first attempted to be parsed as JSON.  If that fails the raw string
is stored as-is.  This means:

| Input            | Stored as         |
|------------------|-------------------|
| `42`             | integer `42`      |
| `true`           | boolean `true`    |
| `"hello world"`  | string (JSON str) |
| `hello world`    | string (plain)    |
| `["a","b"]`      | list              |

## Sidecar format

The sidecar is a pretty-printed JSON object:

```json
{
  "env": "production",
  "owner": "alice",
  "priority": 1
}
```

The sidecar is **not** encrypted.  Do not store sensitive information in
metadata — use the vault itself for secrets.

## Python API

```python
from pathlib import Path
from envault.metadata import load_metadata, set_metadata, remove_metadata, clear_metadata

vault = Path("secrets.vault")

set_metadata(vault, "env", "staging")
data = load_metadata(vault)   # {"env": "staging"}
remove_metadata(vault, "env")
clear_metadata(vault)
```

All functions raise `MetadataError` on failure.
