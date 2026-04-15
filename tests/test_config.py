"""Tests for envault.config."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.config import (
    ConfigError,
    EnvaultConfig,
    config_path,
    init_config,
    load_config,
    save_config,
    CONFIG_FILENAME,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_toml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# config_path
# ---------------------------------------------------------------------------

def test_config_path_uses_filename(tmp_path):
    assert config_path(tmp_path) == tmp_path / CONFIG_FILENAME


# ---------------------------------------------------------------------------
# init_config
# ---------------------------------------------------------------------------

def test_init_config_creates_file(tmp_path):
    cfg = init_config(tmp_path)
    assert config_path(tmp_path).exists()
    assert isinstance(cfg, EnvaultConfig)


def test_init_config_raises_if_exists(tmp_path):
    init_config(tmp_path)
    with pytest.raises(ConfigError, match="already exists"):
        init_config(tmp_path)


def test_init_config_overwrites_when_requested(tmp_path):
    init_config(tmp_path)
    cfg = init_config(tmp_path, overwrite=True, vault_path="custom_vault")
    assert cfg.vault_path == "custom_vault"


def test_init_config_stores_recipients(tmp_path):
    recipients = ["age1abc", "age1def"]
    init_config(tmp_path, recipients=recipients)
    loaded = load_config(tmp_path)
    assert loaded.recipients == recipients


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

def test_load_config_raises_when_missing(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path)


def test_load_config_raises_on_invalid_toml(tmp_path):
    _write_toml(config_path(tmp_path), "[[[invalid toml")
    with pytest.raises(ConfigError, match="parse"):
        load_config(tmp_path)


def test_load_config_returns_defaults_for_missing_keys(tmp_path):
    _write_toml(config_path(tmp_path), "")
    cfg = load_config(tmp_path)
    assert cfg.identity_path == EnvaultConfig.identity_path
    assert cfg.vault_path == EnvaultConfig.vault_path
    assert cfg.recipients == []
    assert cfg.default_remote is None


# ---------------------------------------------------------------------------
# save_config / round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    original = EnvaultConfig(
        identity_path="~/.envault/id.txt",
        vault_path=".vault",
        default_remote="user@host:/backups",
        recipients=["age1xyz"],
    )
    save_config(original, tmp_path)
    loaded = load_config(tmp_path)
    assert loaded.identity_path == original.identity_path
    assert loaded.vault_path == original.vault_path
    assert loaded.default_remote == original.default_remote
    assert loaded.recipients == original.recipients


def test_save_omits_null_remote(tmp_path):
    cfg = EnvaultConfig()
    save_config(cfg, tmp_path)
    raw = config_path(tmp_path).read_text()
    assert "default_remote" not in raw
