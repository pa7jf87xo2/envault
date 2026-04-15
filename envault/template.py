"""Template rendering: substitute .env values into a template file."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional

from envault.vault import unpack


class TemplateError(Exception):
    """Raised when template rendering fails."""


_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def _parse_env(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines from decrypted env text."""
    env: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def render_template(
    template_path: Path,
    vault_path: Path,
    identity_path: Path,
    output_path: Optional[Path] = None,
    *,
    strict: bool = True,
) -> str:
    """Render *template_path* by substituting ``{{ KEY }}`` placeholders.

    Values are sourced from *vault_path* decrypted with *identity_path*.
    If *strict* is True (default) an error is raised for unknown keys.
    Returns the rendered string and optionally writes it to *output_path*.
    """
    if not template_path.exists():
        raise TemplateError(f"Template not found: {template_path}")
    if not vault_path.exists():
        raise TemplateError(f"Vault not found: {vault_path}")

    try:
        env_text = unpack(vault_path, identity_path)
    except Exception as exc:  # pragma: no cover
        raise TemplateError(f"Failed to decrypt vault: {exc}") from exc

    env = _parse_env(env_text)
    template = template_path.read_text()

    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key in env:
            return env[key]
        if strict:
            missing.append(key)
        return match.group(0)

    rendered = _PLACEHOLDER.sub(_replace, template)

    if missing:
        raise TemplateError(
            "Template references undefined keys: " + ", ".join(sorted(missing))
        )

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)

    return rendered
