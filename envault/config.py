"""envault configuration management.

Stores and loads per-project settings in a .envault.toml file.
"""

from __future__ import annotations

import tomllib
import tomli_w
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

CONFIG_FILENAME = ".envault.toml"


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""


@dataclass
class EnvaultConfig:
    identity_path: str = "~/.envault/identity.txt"
    vault_path: str = ".envault"
    default_remote: Optional[str] = None
    recipients: list[str] = field(default_factory=list)


def config_path(project_dir: Path = Path(".")) -> Path:
    return project_dir / CONFIG_FILENAME


def load_config(project_dir: Path = Path(".")) -> EnvaultConfig:
    """Load config from .envault.toml in project_dir."""
    path = config_path(project_dir)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except Exception as exc:
        raise ConfigError(f"Failed to parse config: {exc}") from exc
    return EnvaultConfig(
        identity_path=data.get("identity_path", EnvaultConfig.identity_path),
        vault_path=data.get("vault_path", EnvaultConfig.vault_path),
        default_remote=data.get("default_remote"),
        recipients=data.get("recipients", []),
    )


def save_config(cfg: EnvaultConfig, project_dir: Path = Path(".")) -> Path:
    """Write config to .envault.toml; return the path written."""
    path = config_path(project_dir)
    raw = {
        "identity_path": cfg.identity_path,
        "vault_path": cfg.vault_path,
        "recipients": cfg.recipients,
    }
    if cfg.default_remote is not None:
        raw["default_remote"] = cfg.default_remote
    try:
        with path.open("wb") as fh:
            tomli_w.dump(raw, fh)
    except Exception as exc:
        raise ConfigError(f"Failed to write config: {exc}") from exc
    return path


def init_config(
    project_dir: Path = Path("."),
    *,
    overwrite: bool = False,
    **kwargs,
) -> EnvaultConfig:
    """Create a default config file; raise ConfigError if it already exists."""
    path = config_path(project_dir)
    if path.exists() and not overwrite:
        raise ConfigError(f"Config already exists: {path}. Use overwrite=True to replace.")
    cfg = EnvaultConfig(**kwargs)
    save_config(cfg, project_dir)
    return cfg
