"""Tests for envault.search."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from envault.search import SearchError, SearchMatch, search_vault
from envault.vault import VaultError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ENV_TEXT = "\n".join([
    "# comment",
    "DATABASE_URL=postgres://localhost/db",
    "SECRET_KEY=supersecret",
    "DEBUG=true",
    "API_KEY=abc123",
])


def _patch_unpack(text: str):
    return patch("envault.search.unpack", return_value=text)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_search_vault_raises_when_vault_missing(tmp_path):
    with pytest.raises(SearchError, match="Vault not found"):
        search_vault(tmp_path / "missing.vault", "KEY", tmp_path / "id.txt")


def test_search_vault_raises_on_decrypt_failure(tmp_path):
    vault = tmp_path / "test.vault"
    vault.write_bytes(b"data")
    with patch("envault.search.unpack", side_effect=VaultError("bad")):
        with pytest.raises(SearchError, match="Failed to decrypt"):
            search_vault(vault, "KEY", tmp_path / "id.txt")


def test_search_vault_raises_on_invalid_pattern(tmp_path):
    vault = tmp_path / "test.vault"
    vault.write_bytes(b"data")
    with _patch_unpack(ENV_TEXT):
        with pytest.raises(SearchError, match="Invalid search pattern"):
            search_vault(vault, "[invalid", tmp_path / "id.txt")


def test_search_vault_returns_matching_lines(tmp_path):
    vault = tmp_path / "test.vault"
    vault.write_bytes(b"data")
    with _patch_unpack(ENV_TEXT):
        results = search_vault(vault, "KEY", tmp_path / "id.txt")
    keys = [m.key for m in results]
    assert "SECRET_KEY" in keys
    assert "API_KEY" in keys
    assert "DATABASE_URL" not in keys


def test_search_vault_no_matches_returns_empty(tmp_path):
    vault = tmp_path / "test.vault"
    vault.write_bytes(b"data")
    with _patch_unpack(ENV_TEXT):
        results = search_vault(vault, "NONEXISTENT", tmp_path / "id.txt")
    assert results == []


def test_search_vault_keys_only_ignores_value(tmp_path):
    vault = tmp_path / "test.vault"
    vault.write_bytes(b"data")
    # 'postgres' appears only in the value of DATABASE_URL
    with _patch_unpack(ENV_TEXT):
        results = search_vault(vault, "postgres", tmp_path / "id.txt", keys_only=True)
    assert results == []


def test_search_vault_ignore_case(tmp_path):
    vault = tmp_path / "test.vault"
    vault.write_bytes(b"data")
    with _patch_unpack(ENV_TEXT):
        results = search_vault(vault, "debug", tmp_path / "id.txt", ignore_case=True)
    assert any(m.key == "DEBUG" for m in results)


def test_search_match_has_correct_line_number(tmp_path):
    vault = tmp_path / "test.vault"
    vault.write_bytes(b"data")
    with _patch_unpack(ENV_TEXT):
        results = search_vault(vault, "DATABASE_URL", tmp_path / "id.txt")
    assert len(results) == 1
    assert results[0].line_number == 2  # line 1 is the comment
    assert results[0].value == "postgres://localhost/db"
