"""Tests for envault.comment."""
from pathlib import Path
import pytest
from envault.comment import (
    CommentError,
    comments_path,
    load_comments,
    set_comment,
    remove_comment,
    get_comment,
)


def _make_vault(tmp_path: Path) -> Path:
    v = tmp_path / "test.vault"
    v.write_bytes(b"data")
    return v


def test_comments_path_uses_suffix(tmp_path):
    v = tmp_path / "my.vault"
    assert comments_path(v) == tmp_path / "my.comments.json"


def test_load_comments_raises_when_vault_missing(tmp_path):
    with pytest.raises(CommentError, match="vault not found"):
        load_comments(tmp_path / "missing.vault")


def test_load_comments_returns_empty_when_no_file(tmp_path):
    v = _make_vault(tmp_path)
    assert load_comments(v) == {}


def test_load_comments_raises_on_corrupt_file(tmp_path):
    v = _make_vault(tmp_path)
    comments_path(v).write_text("not json")
    with pytest.raises(CommentError, match="corrupt"):
        load_comments(v)


def test_set_comment_creates_file(tmp_path):
    v = _make_vault(tmp_path)
    set_comment(v, "DB_URL", "primary database")
    assert comments_path(v).exists()


def test_set_comment_persists_value(tmp_path):
    v = _make_vault(tmp_path)
    set_comment(v, "API_KEY", "third-party key")
    assert load_comments(v)["API_KEY"] == "third-party key"


def test_set_comment_raises_on_empty_key(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(CommentError, match="key must not be empty"):
        set_comment(v, "  ", "oops")


def test_set_comment_raises_when_vault_missing(tmp_path):
    with pytest.raises(CommentError, match="vault not found"):
        set_comment(tmp_path / "no.vault", "K", "v")


def test_remove_comment_deletes_key(tmp_path):
    v = _make_vault(tmp_path)
    set_comment(v, "X", "hello")
    remove_comment(v, "X")
    assert get_comment(v, "X") is None


def test_remove_comment_removes_file_when_empty(tmp_path):
    v = _make_vault(tmp_path)
    set_comment(v, "X", "hello")
    remove_comment(v, "X")
    assert not comments_path(v).exists()


def test_remove_comment_raises_when_key_missing(tmp_path):
    v = _make_vault(tmp_path)
    with pytest.raises(CommentError, match="no comment for key"):
        remove_comment(v, "GHOST")


def test_get_comment_returns_none_when_absent(tmp_path):
    v = _make_vault(tmp_path)
    assert get_comment(v, "MISSING") is None
