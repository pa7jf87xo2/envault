"""Tests for envault.notify."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from envault.notify import (
    NotifyError,
    notify_path,
    load_config,
    save_config,
    set_webhook,
    send,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"data")
    return v


def test_notify_path_uses_suffix(tmp_path):
    v = tmp_path / "my.vault"
    assert notify_path(v) == tmp_path / "my.notify.json"


def test_load_config_raises_when_vault_missing(tmp_path):
    with pytest.raises(NotifyError, match="vault not found"):
        load_config(tmp_path / "ghost.vault")


def test_load_config_returns_empty_when_no_file(tmp_path):
    v = _make_vault(tmp_path)
    assert load_config(v) == {}


def test_load_config_raises_on_corrupt_file(tmp_path):
    v = _make_vault(tmp_path)
    notify_path(v).write_text("not json")
    with pytest.raises(NotifyError, match="corrupt"):
        load_config(v)


def test_save_config_raises_when_vault_missing(tmp_path):
    with pytest.raises(NotifyError, match="vault not found"):
        save_config(tmp_path / "ghost.vault", {})


def test_save_config_persists_data(tmp_path):
    v = _make_vault(tmp_path)
    save_config(v, {"webhook": "https://example.com/hook"})
    data = json.loads(notify_path(v).read_text())
    assert data["webhook"] == "https://example.com/hook"


def test_set_webhook_rejects_invalid_url(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(NotifyError, match="invalid webhook URL"):
        set_webhook(v, "ftp://bad")


def test_set_webhook_saves_url(tmp_path):
    v = _make_vault(tmp_path)
    set_webhook(v, "https://hooks.example.com/abc")
    cfg = load_config(v)
    assert cfg["webhook"] == "https://hooks.example.com/abc"


def test_send_returns_empty_when_no_channels(tmp_path):
    v = _make_vault(tmp_path)
    result = send(v, "pack")
    assert result == []


def test_send_webhook_success(tmp_path):
    v = _make_vault(tmp_path)
    set_webhook(v, "https://hooks.example.com/x")
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_cm)
    mock_cm.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_cm):
        result = send(v, "pack", detail="env packed")
    assert "webhook" in result


def test_send_webhook_raises_on_failure(tmp_path):
    v = _make_vault(tmp_path)
    set_webhook(v, "https://hooks.example.com/x")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        with pytest.raises(NotifyError, match="webhook delivery failed"):
            send(v, "pack")


def test_send_desktop_channel(tmp_path):
    v = _make_vault(tmp_path)
    save_config(v, {"desktop": True})
    with patch("envault.notify._send_desktop") as mock_desk:
        result = send(v, "unpack", detail="done")
    mock_desk.assert_called_once_with("unpack", "done")
    assert "desktop" in result
