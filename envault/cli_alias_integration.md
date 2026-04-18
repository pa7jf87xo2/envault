# Vault Alias Integration

The `alias` sub-command lets you assign short, memorable names to vault paths
so you don't have to remember full file-system paths.

## Storage

Aliases are stored as a JSON object in a sidecar file next to the vault:

```
my.vault
my.aliases.json   ← { "prod": "/envs/prod.vault", ... }
```

## Commands

```bash
# List all aliases for the default vault
envault alias list

# Add or update an alias
envault alias set prod /envs/production.vault

# Remove an alias
envault alias remove prod

# Print the resolved path for an alias (useful in scripts)
envault alias resolve prod
```

## Scripting example

```bash
VAULT=$(envault alias resolve prod)
envault unpack --vault "$VAULT" --identity ~/.config/envault/identity.age
```

## Using a non-default vault

All sub-commands accept `--vault PATH`:

```bash
envault alias --vault /shared/team.vault list
```

## Error handling

| Situation | Exit code |
|---|---|
| Vault file missing | 1 |
| Corrupt aliases file | 1 |
| Alias not found | 1 |
| Empty name or target | 1 |
