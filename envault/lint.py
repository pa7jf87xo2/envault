"""Lint .env files for common issues before packing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


class LintError(Exception):
    """Raised when linting cannot be performed."""


@dataclass
class LintIssue:
    line_no: int
    message: str
    severity: str  # 'error' | 'warning'


@dataclass
class LintResult:
    path: Path
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_LINE_RE = re.compile(r'^([^=]+)=(.*)$')


def lint_file(env_path: Path) -> LintResult:
    """Lint *env_path* and return a :class:`LintResult`."""
    if not env_path.exists():
        raise LintError(f"File not found: {env_path}")

    result = LintResult(path=env_path)
    lines = env_path.read_text(encoding="utf-8").splitlines()
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        m = _LINE_RE.match(stripped)
        if not m:
            result.issues.append(LintIssue(lineno, "Line is not a valid KEY=VALUE pair", "error"))
            continue

        key, value = m.group(1).strip(), m.group(2)

        if not _KEY_RE.match(key):
            result.issues.append(LintIssue(lineno, f"Key '{key}' contains invalid characters or is lowercase", "warning"))

        if key in seen_keys:
            result.issues.append(LintIssue(lineno, f"Duplicate key '{key}' (first seen on line {seen_keys[key]})", "error"))
        else:
            seen_keys[key] = lineno

        if not value:
            result.issues.append(LintIssue(lineno, f"Key '{key}' has an empty value", "warning"))

    return result
