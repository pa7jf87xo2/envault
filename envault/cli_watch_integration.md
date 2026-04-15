# `envault watch` — Integration Notes

## Overview

The `watch` sub-command polls a plaintext `.env` file and automatically repacks
it into an encrypted vault whenever the file's modification time changes.  This
allows developers to edit their `.env` file normally while keeping the vault
always up to date without running `envault pack` manually.

## Usage

```
envault watch [OPTIONS] ENV_FILE
```

### Positional arguments

| Argument   | Description                              |
|------------|------------------------------------------|
| `ENV_FILE` | Path to the plaintext `.env` file to watch. |

### Options

| Flag                        | Default              | Description                                      |
|-----------------------------|----------------------|--------------------------------------------------|
| `-v`, `--vault VAULT`       | `<env_file>.vault`   | Destination vault file path.                     |
| `-k`, `--public-key KEY`    | from config/identity | age public key used for encryption.              |
| `-i`, `--interval SECONDS`  | `1.0`                | Polling interval in seconds.                     |

## Public key resolution order

1. `--public-key` CLI flag
2. `public_key` field in `envault.toml` (loaded via `load_config`)
3. Identity file managed by `envault.identity` (`load_public_key`)

If none of the above sources provide a key the command exits with status 1.

## Integration with the main CLI

Register the watcher in `envault/cli.py`:

```python
import envault.cli_watch as cli_watch
cli_watch.build_parser(subparsers)
```

## Audit log

Every successful repack triggered by a file-change event is recorded in the
envault audit log via `envault.audit.record` with the action `"watch"` and the
source env file path.  Use `envault audit tail` to stream recent events.

## Limitations

- The watcher uses **polling** (not `inotify`/`kqueue`) for broad platform
  compatibility.  The default 1-second interval is suitable for most
  development workflows.
- The watcher runs in the **foreground**.  For background operation wrap it in
  a process manager (e.g. `systemd`, `supervisord`, or a shell `&`).
- Only a single file is watched per invocation.  Run multiple instances to
  watch several files simultaneously.
