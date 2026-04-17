"""archive.py – bundle multiple vault snapshots into a single tar archive."""
from __future__ import annotations

import tarfile
import time
from pathlib import Path
from typing import List


class ArchiveError(Exception):
    """Raised when archiving or extracting fails."""


def archives_dir(base: Path) -> Path:
    """Return the directory used to store vault archives."""
    return base / ".envault" / "archives"


def _ts() -> str:
    return time.strftime("%Y%m%dT%H%M%S")


def create_archive(
    vault: Path,
    sources: List[Path],
    *,
    name: str | None = None,
    dest_dir: Path | None = None,
) -> Path:
    """Pack *sources* into a .tar.gz archive next to *vault*.

    Parameters
    ----------
    vault:      Reference vault path (used to anchor the archive directory).
    sources:    Files to include in the archive.
    name:       Optional archive stem; defaults to a timestamp.
    dest_dir:   Override destination directory.
    """
    if not vault.exists():
        raise ArchiveError(f"Vault not found: {vault}")

    missing = [str(p) for p in sources if not p.exists()]
    if missing:
        raise ArchiveError("Source files not found: " + ", ".join(missing))

    out_dir = dest_dir if dest_dir is not None else archives_dir(vault.parent)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = name if name else _ts()
    archive_path = out_dir / f"{stem}.tar.gz"

    with tarfile.open(archive_path, "w:gz") as tar:
        for src in sources:
            tar.add(src, arcname=src.name)

    return archive_path


def list_archives(vault: Path, *, dest_dir: Path | None = None) -> List[Path]:
    """Return sorted list of .tar.gz archives for *vault*."""
    out_dir = dest_dir if dest_dir is not None else archives_dir(vault.parent)
    if not out_dir.exists():
        return []
    return sorted(out_dir.glob("*.tar.gz"))


def extract_archive(archive: Path, dest: Path) -> List[Path]:
    """Extract *archive* into *dest*, returning extracted paths."""
    if not archive.exists():
        raise ArchiveError(f"Archive not found: {archive}")
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(dest)
        return [dest / m.name for m in tar.getmembers()]
