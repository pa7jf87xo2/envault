"""Tests for envault.archive."""
from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from envault.archive import (
    ArchiveError,
    archives_dir,
    create_archive,
    extract_archive,
    list_archives,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "secrets.age"
    v.write_bytes(b"encrypted")
    return v


def _make_sources(tmp_path: Path) -> list[Path]:
    files = []
    for name in ("snap1.age", "snap2.age"):
        p = tmp_path / name
        p.write_bytes(b"data-" + name.encode())
        files.append(p)
    return files


def test_archives_dir_returns_correct_path(tmp_path):
    vault = tmp_path / "secrets.age"
    assert archives_dir(tmp_path) == tmp_path / ".envault" / "archives"


def test_create_archive_raises_when_vault_missing(tmp_path):
    vault = tmp_path / "missing.age"
    with pytest.raises(ArchiveError, match="Vault not found"):
        create_archive(vault, [], dest_dir=tmp_path)


def test_create_archive_raises_when_source_missing(tmp_path):
    vault = _make_vault(tmp_path)
    ghost = tmp_path / "ghost.age"
    with pytest.raises(ArchiveError, match="Source files not found"):
        create_archive(vault, [ghost], dest_dir=tmp_path / "out")


def test_create_archive_creates_tar_gz(tmp_path):
    vault = _make_vault(tmp_path)
    sources = _make_sources(tmp_path)
    out = tmp_path / "out"
    archive = create_archive(vault, sources, dest_dir=out)
    assert archive.exists()
    assert archive.suffix == ".gz"
    assert tarfile.is_tarfile(archive)


def test_create_archive_custom_name(tmp_path):
    vault = _make_vault(tmp_path)
    sources = _make_sources(tmp_path)
    out = tmp_path / "out"
    archive = create_archive(vault, sources, name="mybackup", dest_dir=out)
    assert archive.name == "mybackup.tar.gz"


def test_create_archive_contains_sources(tmp_path):
    vault = _make_vault(tmp_path)
    sources = _make_sources(tmp_path)
    out = tmp_path / "out"
    archive = create_archive(vault, sources, dest_dir=out)
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
    assert "snap1.age" in names
    assert "snap2.age" in names


def test_create_archive_contains_vault(tmp_path):
    """The vault file itself should be included in the archive."""
    vault = _make_vault(tmp_path)
    sources = _make_sources(tmp_path)
    out = tmp_path / "out"
    archive = create_archive(vault, sources, dest_dir=out)
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
    assert vault.name in names


def test_list_archives_returns_empty_when_no_dir(tmp_path):
    vault = _make_vault(tmp_path)
    assert list_archives(vault) == []


def test_list_archives_returns_sorted(tmp_path):
    vault = _make_vault(tmp_path)
    sources = _make_sources(tmp_path)
    out = tmp_path / "out"
    a1 = create_archive(vault, sources, name="aaa", dest_dir=out)
    a2 = create_archive(vault, sources, name="zzz", dest_dir=out)
    result = list_archives(vault, dest_dir=out)
    assert result == [a1, a2]


def test_extract_archive_raises_when_missing(tmp_path):
    ghost = tmp_path / "ghost.tar.gz"
    with pytest.raises(ArchiveError, match="Archive not found"):
        extract_archive(ghost, tmp_path / "dest")


def test_extract_archive_restores_files(tmp_path):
    vault = _make_vault(tmp_path)
    sources = _make_sources(tmp_path)
