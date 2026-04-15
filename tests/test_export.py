"""Tests for envault.export."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.export import ExportError, _parse_env, _to_dotenv, _to_json, _to_shell, export_vault


# ---------------------------------------------------------------------------
# _parse_env
# ---------------------------------------------------------------------------

def test_parse_env_basic():
    text = "FOO=bar\nBAZ=qux\n"
    result = _parse_env(text)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_skips_comments_and_blanks():
    text = "# comment\n\nKEY=value\n"
    result = _parse_env(text)
    assert result == {"KEY": "value"}


def test_parse_env_skips_lines_without_equals():
    result = _parse_env("INVALID\nGOOD=yes\n")
    assert result == {"GOOD": "yes"}


# ---------------------------------------------------------------------------
# format helpers
# ---------------------------------------------------------------------------

def test_to_shell_quotes_values():
    output = _to_shell({"MSG": "hello world"})
    assert output == "export MSG='hello world'"


def test_to_dotenv_format():
    output = _to_dotenv({"A": "1", "B": "2"})
    assert "A=1" in output
    assert "B=2" in output


def test_to_json_valid():
    output = _to_json({"X": "y"})
    parsed = json.loads(output)
    assert parsed == {"X": "y"}


# ---------------------------------------------------------------------------
# export_vault
# ---------------------------------------------------------------------------

def _fake_unpack(vault: Path, dest: Path, identity: Path) -> None:  # noqa: ARG001
    dest.write_text("KEY=secret\nOTHER=value\n")


def test_export_vault_raises_when_vault_missing(tmp_path):
    with pytest.raises(ExportError, match="Vault not found"):
        export_vault(tmp_path / "missing.vault", tmp_path / "id.txt")


def test_export_vault_dotenv(tmp_path):
    vault = tmp_path / "env.vault"
    vault.touch()
    with patch("envault.export.unpack", side_effect=_fake_unpack):
        result = export_vault(vault, tmp_path / "id.txt", fmt="dotenv")
    assert "KEY=secret" in result
    assert "OTHER=value" in result


def test_export_vault_shell(tmp_path):
    vault = tmp_path / "env.vault"
    vault.touch()
    with patch("envault.export.unpack", side_effect=_fake_unpack):
        result = export_vault(vault, tmp_path / "id.txt", fmt="shell")
    assert result.startswith("export ")
    assert "KEY" in result


def test_export_vault_json(tmp_path):
    vault = tmp_path / "env.vault"
    vault.touch()
    with patch("envault.export.unpack", side_effect=_fake_unpack):
        result = export_vault(vault, tmp_path / "id.txt", fmt="json")
    parsed = json.loads(result)
    assert parsed["KEY"] == "secret"


def test_export_vault_filters_keys(tmp_path):
    vault = tmp_path / "env.vault"
    vault.touch()
    with patch("envault.export.unpack", side_effect=_fake_unpack):
        result = export_vault(vault, tmp_path / "id.txt", fmt="json", keys=["KEY"])
    parsed = json.loads(result)
    assert "KEY" in parsed
    assert "OTHER" not in parsed


def test_export_vault_unknown_format_raises(tmp_path):
    vault = tmp_path / "env.vault"
    vault.touch()
    with patch("envault.export.unpack", side_effect=_fake_unpack):
        with pytest.raises(ExportError, match="Unknown export format"):
            export_vault(vault, tmp_path / "id.txt", fmt="xml")  # type: ignore[arg-type]


def test_export_vault_raises_on_decrypt_failure(tmp_path):
    vault = tmp_path / "env.vault"
    vault.touch()
    with patch("envault.export.unpack", side_effect=RuntimeError("bad key")):
        with pytest.raises(ExportError, match="Failed to decrypt"):
            export_vault(vault, tmp_path / "id.txt")
