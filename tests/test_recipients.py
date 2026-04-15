"""Tests for envault.recipients."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.recipients import (
    RecipientsError,
    recipients_path,
    load_recipients,
    add_recipient,
    remove_recipient,
    RECIPIENTS_FILENAME,
)

_VALID_KEY_A = "age1" + "a" * 58
_VALID_KEY_B = "age1" + "b" * 58
_INVALID_KEY = "ssh-rsa AAAAB3Nz"


def test_recipients_path_uses_filename(tmp_path):
    p = recipients_path(tmp_path)
    assert p == tmp_path / RECIPIENTS_FILENAME


def test_load_recipients_raises_when_missing(tmp_path):
    with pytest.raises(RecipientsError, match="not found"):
        load_recipients(tmp_path / RECIPIENTS_FILENAME)


def test_load_recipients_skips_comments_and_blanks(tmp_path):
    f = tmp_path / RECIPIENTS_FILENAME
    f.write_text(f"# comment\n\n{_VALID_KEY_A}\n")
    keys = load_recipients(f)
    assert keys == [_VALID_KEY_A]


def test_load_recipients_raises_on_invalid_key(tmp_path):
    f = tmp_path / RECIPIENTS_FILENAME
    f.write_text(_INVALID_KEY + "\n")
    with pytest.raises(RecipientsError, match="Invalid age public key"):
        load_recipients(f)


def test_add_recipient_creates_file(tmp_path):
    f = tmp_path / RECIPIENTS_FILENAME
    add_recipient(f, _VALID_KEY_A)
    assert f.exists()
    assert _VALID_KEY_A in f.read_text()


def test_add_recipient_appends_second_key(tmp_path):
    f = tmp_path / RECIPIENTS_FILENAME
    add_recipient(f, _VALID_KEY_A)
    add_recipient(f, _VALID_KEY_B)
    keys = load_recipients(f)
    assert keys == [_VALID_KEY_A, _VALID_KEY_B]


def test_add_recipient_raises_on_duplicate(tmp_path):
    f = tmp_path / RECIPIENTS_FILENAME
    add_recipient(f, _VALID_KEY_A)
    with pytest.raises(RecipientsError, match="already present"):
        add_recipient(f, _VALID_KEY_A)


def test_add_recipient_raises_on_invalid_key(tmp_path):
    f = tmp_path / RECIPIENTS_FILENAME
    with pytest.raises(RecipientsError, match="Invalid age public key"):
        add_recipient(f, _INVALID_KEY)


def test_remove_recipient_removes_key(tmp_path):
    f = tmp_path / RECIPIENTS_FILENAME
    add_recipient(f, _VALID_KEY_A)
    add_recipient(f, _VALID_KEY_B)
    remove_recipient(f, _VALID_KEY_A)
    keys = load_recipients(f)
    assert keys == [_VALID_KEY_B]


def test_remove_recipient_raises_when_missing_file(tmp_path):
    f = tmp_path / RECIPIENTS_FILENAME
    with pytest.raises(RecipientsError, match="not found"):
        remove_recipient(f, _VALID_KEY_A)


def test_remove_recipient_raises_when_key_absent(tmp_path):
    f = tmp_path / RECIPIENTS_FILENAME
    add_recipient(f, _VALID_KEY_A)
    with pytest.raises(RecipientsError, match="not found"):
        remove_recipient(f, _VALID_KEY_B)
