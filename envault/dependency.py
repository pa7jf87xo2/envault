"""Track inter-vault dependencies (one vault depends on another)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


class DependencyError(Exception):
    """Raised when a dependency operation fails."""


def dependency_path(vault: Path) -> Path:
    """Return the sidecar path for a vault's dependency list."""
    return vault.with_suffix(".deps.json")


def load_dependencies(vault: Path) -> List[str]:
    """Return the list of vault paths this vault depends on."""
    if not vault.exists():
        raise DependencyError(f"vault not found: {vault}")
    dep_file = dependency_path(vault)
    if not dep_file.exists():
        return []
    try:
        data = json.loads(dep_file.read_text())
    except json.JSONDecodeError as exc:
        raise DependencyError(f"corrupt dependency file: {exc}") from exc
    if not isinstance(data, list):
        raise DependencyError("dependency file must contain a JSON array")
    return [str(d) for d in data]


def add_dependency(vault: Path, dep: str) -> List[str]:
    """Add *dep* as a dependency of *vault*. No-op if already present."""
    if not vault.exists():
        raise DependencyError(f"vault not found: {vault}")
    if not dep.strip():
        raise DependencyError("dependency path must not be empty")
    deps = load_dependencies(vault)
    if dep not in deps:
        deps.append(dep)
        dependency_path(vault).write_text(json.dumps(deps, indent=2))
    return deps


def remove_dependency(vault: Path, dep: str) -> List[str]:
    """Remove *dep* from the dependency list of *vault*."""
    if not vault.exists():
        raise DependencyError(f"vault not found: {vault}")
    deps = load_dependencies(vault)
    if dep not in deps:
        raise DependencyError(f"dependency not found: {dep}")
    deps = [d for d in deps if d != dep]
    dependency_path(vault).write_text(json.dumps(deps, indent=2))
    return deps


def clear_dependencies(vault: Path) -> None:
    """Remove the dependency sidecar file entirely."""
    if not vault.exists():
        raise DependencyError(f"vault not found: {vault}")
    dep_file = dependency_path(vault)
    if dep_file.exists():
        dep_file.unlink()
