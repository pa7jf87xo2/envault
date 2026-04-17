"""Tests for envault.cli_quota."""
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from envault.cli_quota import build_parser, _cmd_quota_set, _cmd_quota_show, _cmd_quota_check, _cmd_quota_clear
from envault.quota import QuotaError


def _ns(**kw) -> argparse.Namespace:
    return argparse.Namespace(**kw)


def test_build_parser_returns_parser():
    p = build_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_build_parser_has_subcommands():
    p = build_parser()
    args = p.parse_args(["set", "my.vault", "2048"])
    assert args.max_bytes == 2048


def test_cmd_quota_set_prints_confirmation(capsys, tmp_path):
    v = tmp_path / "x.vault"
    v.write_bytes(b"data")
    ns = _ns(vault=str(v), max_bytes=4096)
    _cmd_quota_set(ns)
    out = capsys.readouterr().out
    assert "4096" in out


def test_cmd_quota_set_exits_on_error(capsys):
    ns = _ns(vault="/no/such/file.vault", max_bytes=100)
    with pytest.raises(SystemExit) as exc:
        _cmd_quota_set(ns)
    assert exc.value.code == 1


def test_cmd_quota_show_no_quota(capsys, tmp_path):
    v = tmp_path / "x.vault"
    v.write_bytes(b"data")
    ns = _ns(vault=str(v))
    _cmd_quota_show(ns)
    out = capsys.readouterr().out
    assert "default" in out.lower()


def test_cmd_quota_show_with_quota(capsys, tmp_path):
    v = tmp_path / "x.vault"
    v.write_bytes(b"data")
    from envault.quota import set_quota
    set_quota(v, 999)
    ns = _ns(vault=str(v))
    _cmd_quota_show(ns)
    out = capsys.readouterr().out
    assert "999" in out


def test_cmd_quota_check_ok(capsys, tmp_path):
    v = tmp_path / "x.vault"
    v.write_bytes(b"small")
    from envault.quota import set_quota
    set_quota(v, 1024)
    ns = _ns(vault=str(v))
    _cmd_quota_check(ns)
    out = capsys.readouterr().out
    assert "ok" in out


def test_cmd_quota_check_exits_when_exceeded(capsys, tmp_path):
    v = tmp_path / "x.vault"
    v.write_bytes(b"x" * 200)
    from envault.quota import set_quota
    set_quota(v, 10)
    ns = _ns(vault=str(v))
    with pytest.raises(SystemExit) as exc:
        _cmd_quota_check(ns)
    assert exc.value.code == 1


def test_cmd_quota_clear_removes_quota(capsys, tmp_path):
    v = tmp_path / "x.vault"
    v.write_bytes(b"data")
    from envault.quota import set_quota, quota_path
    set_quota(v, 512)
    ns = _ns(vault=str(v))
    _cmd_quota_clear(ns)
    assert not quota_path(v).exists()
    out = capsys.readouterr().out
    assert "cleared" in out.lower()
