"""Tests for envault.diff."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from envault.diff import DiffError, diff_vault, summarise_diff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _fake_unpack(vault_path: Path, dest: Path, identity_path: Path) -> None:
    """Simulate unpack by writing fixed content to dest."""
    dest.write_text("KEY=vault_value\nSECRET=abc\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# diff_vault
# ---------------------------------------------------------------------------

def test_diff_vault_raises_when_vault_missing(tmp_path: Path) -> None:
    live = _write(tmp_path / ".env", "KEY=live\n")
    with pytest.raises(DiffError, match="Vault file not found"):
        diff_vault(tmp_path / "missing.vault", live, tmp_path / "id.txt")


def test_diff_vault_raises_when_live_missing(tmp_path: Path) -> None:
    vault = _write(tmp_path / "env.vault", "dummy")
    with pytest.raises(DiffError, match="Live .env file not found"):
        diff_vault(vault, tmp_path / ".env", tmp_path / "id.txt")


def test_diff_vault_no_changes(tmp_path: Path) -> None:
    vault = _write(tmp_path / "env.vault", "dummy")
    live = _write(tmp_path / ".env", "KEY=vault_value\nSECRET=abc\n")
    identity = tmp_path / "id.txt"

    with patch("envault.diff.unpack", side_effect=_fake_unpack):
        changed, diff_text = diff_vault(vault, live, identity)

    assert changed is False
    assert diff_text == ""


def test_diff_vault_detects_changes(tmp_path: Path) -> None:
    vault = _write(tmp_path / "env.vault", "dummy")
    live = _write(tmp_path / ".env", "KEY=different_value\nSECRET=abc\n")
    identity = tmp_path / "id.txt"

    with patch("envault.diff.unpack", side_effect=_fake_unpack):
        changed, diff_text = diff_vault(vault, live, identity)

    assert changed is True
    assert "-KEY=vault_value" in diff_text
    assert "+KEY=different_value" in diff_text


def test_diff_vault_fromfile_tofile_labels(tmp_path: Path) -> None:
    vault = _write(tmp_path / "env.vault", "dummy")
    live = _write(tmp_path / ".env", "KEY=other\n")
    identity = tmp_path / "id.txt"

    with patch("envault.diff.unpack", side_effect=_fake_unpack):
        _, diff_text = diff_vault(vault, live, identity)

    assert "vault:env.vault" in diff_text
    assert "live:.env" in diff_text


# ---------------------------------------------------------------------------
# summarise_diff
# ---------------------------------------------------------------------------

def test_summarise_diff_empty() -> None:
    assert summarise_diff("") == (0, 0)


def test_summarise_diff_counts() -> None:
    diff = (
        "--- a\n"
        "+++ b\n"
        "@@ -1,2 +1,3 @@\n"
        "-OLD=1\n"
        "+NEW=1\n"
        "+EXTRA=2\n"
        " SAME=3\n"
    )
    additions, deletions = summarise_diff(diff)
    assert additions == 2
    assert deletions == 1
