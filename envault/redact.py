"""Redact sensitive values from .env content before display or logging."""

from __future__ import annotations

import re
from typing import Iterable

# Keys whose values should always be fully redacted
_SENSITIVE_PATTERNS = re.compile(
    r"(password|secret|token|key|api|auth|credential|private)",
    re.IGNORECASE,
)

_MASK = "***"


class RedactError(Exception):
    """Raised when redaction cannot be applied."""


def _is_sensitive(key: str) -> bool:
    return bool(_SENSITIVE_PATTERNS.search(key))


def redact_line(line: str, show_partial: bool = False) -> str:
    """Return the line with the value masked if the key looks sensitive.

    Non-assignment lines (comments, blanks) are returned unchanged.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return line
    if "=" not in stripped:
        return line
    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip()
    if not _is_sensitive(key):
        return line
    if show_partial and len(value) > 4:
        masked = value[:2] + _MASK + value[-2:]
    else:
        masked = _MASK
    return f"{key}={masked}\n"


def redact_lines(lines: Iterable[str], show_partial: bool = False) -> list[str]:
    """Apply :func:`redact_line` to each line and return the result list."""
    return [redact_line(line, show_partial=show_partial) for line in lines]


def redact_text(text: str, show_partial: bool = False) -> str:
    """Redact all sensitive values in a multi-line env string."""
    lines = text.splitlines(keepends=True)
    return "".join(redact_lines(lines, show_partial=show_partial))
