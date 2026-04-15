# Hooks Integration Guide

envault supports lightweight shell hooks that run before or after `pack` and
`unpack` operations.  Use them to validate secrets, notify teammates, or
trigger downstream tooling.

## Available hooks

| Hook name    | Triggered                          |
|--------------|------------------------------------|
| `pre-pack`   | Before `.env` is encrypted         |
| `post-pack`  | After vault file is written        |
| `pre-unpack` | Before vault file is decrypted     |
| `post-unpack`| After `.env` is written to disk    |

Hook scripts live in `.envault/hooks/<name>` and must be executable.

## Quick start

```bash
# Install a stub hook (edit the generated file afterwards)
envault hooks install post-pack

# List all hooks and their status
envault hooks list

# Remove a hook
envault hooks remove post-pack
```

## Environment variables passed to hooks

All hooks inherit the calling process environment.  envault additionally sets:

- `ENVAULT_HOOK` — name of the running hook (e.g. `post-pack`)
- `ENVAULT_VAULT` — path to the vault file being operated on

## Exit codes

A non-zero exit from any hook **aborts** the envault operation and prints the
hook's stderr.  Use this to enforce pre-conditions (e.g. lint checks, secret
scanning).

## Example: block packing if a secret is missing

```sh
#!/bin/sh
# .envault/hooks/pre-pack
if ! grep -q '^DATABASE_URL=' .env 2>/dev/null; then
  echo "ERROR: DATABASE_URL is required in .env" >&2
  exit 1
fi
```
