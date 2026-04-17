"""Tests for envault.cli_sign."""
from pathlib import Path
import argparse
import pytest
from unittest.mock import patch, MagicMock

from envault.cli_sign import _cmd_sign, _cmd_verify, _cmd_clear, build_parser
from envault.sign import SignError


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"vault": "env.vault", "secret": "s3cr3t"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_cmd_sign_prints_hmac(tmp_path, capsys):
    vault = tmp_path / "env.vault"
    vault.write_bytes(b"KEY=val")
    _cmd_sign(_ns(vault=str(vault)))
    out = capsys.readouterr().out
    assert "signed:" in out


def test_cmd_sign_exits_on_error(tmp_path):
    with pytest.raises(SystemExit) as exc:
        _cmd_sign(_ns(vault=str(tmp_path / "missing.vault")))
    assert exc.value.code == 1


def test_cmd_verify_ok(tmp_path, capsys):
    vault = tmp_path / "env.vault"
    vault.write_bytes(b"KEY=val")
    _cmd_sign(_ns(vault=str(vault(_ns(vault=str(vault)))
    assert "ok" in capsys.readouterr().out


def test_cmd_verify_mismatch_exits(tmp_path):
    vault = tmp_path / "env.vault"
    vault.write_bytes(b"KEY=val")
    _cmd_sign(_ns(vault=str(vault), secret="right"))
    with pytest.raises(SystemExit) as exc:
        _cmd_verify(_ns(vault=str(vault), secret="wrong"))
    assert exc.value.code == 1


def test_cmd_verify_exits_on_sign_error(tmp_path):
    with pytest.raises(SystemExit):
        _cmd_verify(_ns(vault=str(tmp_path / "missing.vault")))


def test_cmd_clear_removes_sig(tmp_path, capsys):
    vault = tmp_path / "env.vault"
    vault.write_bytes(b"KEY=val")
    _cmd_sign(_ns(vault=str(vault)))
    _cmd_clear(_ns(vault=str(vault)))
    assert "cleared" in capsys.readouterr().out


def test_cmd_clear_reports_missing(tmp_path, capsys):
    vault = tmp_path / "env.vault"
    vault.write_bytes(b"KEY=val")
    _cmd_clear(_ns(vault=str(vault)))
    assert "no signature" in capsys.readouterr().out
