"""Tests for envault.template."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from envault.template import TemplateError, render_template, _parse_env


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_ENV_TEXT = "DB_HOST=localhost\nDB_PORT=5432\n# comment\nSECRET=hunter2\n"


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _fake_unpack(vault_path, identity_path):  # noqa: ARG001
    return _ENV_TEXT


# ---------------------------------------------------------------------------
# _parse_env
# ---------------------------------------------------------------------------

def test_parse_env_basic():
    result = _parse_env(_ENV_TEXT)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "hunter2"}


def test_parse_env_skips_comments_and_blanks():
    result = _parse_env("# header\n\nFOO=bar\n")
    assert result == {"FOO": "bar"}


def test_parse_env_skips_lines_without_equals():
    result = _parse_env("NOEQUALS\nFOO=bar")
    assert result == {"FOO": "bar"}


# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------

def test_render_template_raises_when_template_missing(tmp_path):
    with pytest.raises(TemplateError, match="Template not found"):
        render_template(
            tmp_path / "missing.tmpl",
            tmp_path / "vault.age",
            tmp_path / "key.txt",
        )


def test_render_template_raises_when_vault_missing(tmp_path):
    tpl = _write(tmp_path, "app.tmpl", "HOST={{ DB_HOST }}")
    with pytest.raises(TemplateError, match="Vault not found"):
        render_template(tpl, tmp_path / "vault.age", tmp_path / "key.txt")


def test_render_template_substitutes_values(tmp_path):
    tpl = _write(tmp_path, "app.tmpl", "host={{ DB_HOST }} port={{ DB_PORT }}")
    vault = _write(tmp_path, "vault.age", "")
    with patch("envault.template.unpack", side_effect=_fake_unpack):
        result = render_template(tpl, vault, tmp_path / "key.txt")
    assert result == "host=localhost port=5432"


def test_render_template_strict_raises_on_unknown_key(tmp_path):
    tpl = _write(tmp_path, "app.tmpl", "x={{ UNKNOWN_KEY }}")
    vault = _write(tmp_path, "vault.age", "")
    with patch("envault.template.unpack", side_effect=_fake_unpack):
        with pytest.raises(TemplateError, match="UNKNOWN_KEY"):
            render_template(tpl, vault, tmp_path / "key.txt", strict=True)


def test_render_template_non_strict_preserves_unknown_key(tmp_path):
    tpl = _write(tmp_path, "app.tmpl", "x={{ UNKNOWN_KEY }}")
    vault = _write(tmp_path, "vault.age", "")
    with patch("envault.template.unpack", side_effect=_fake_unpack):
        result = render_template(tpl, vault, tmp_path / "key.txt", strict=False)
    assert result == "x={{ UNKNOWN_KEY }}"


def test_render_template_writes_output_file(tmp_path):
    tpl = _write(tmp_path, "app.tmpl", "SECRET={{ SECRET }}")
    vault = _write(tmp_path, "vault.age", "")
    out = tmp_path / "out" / "rendered.txt"
    with patch("envault.template.unpack", side_effect=_fake_unpack):
        render_template(tpl, vault, tmp_path / "key.txt", out)
    assert out.exists()
    assert out.read_text() == "SECRET=hunter2"
