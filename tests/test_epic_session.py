"""Tests for issue_flow.epic_session — epic_session.md I/O (issue #333)."""

from __future__ import annotations

from pathlib import Path

import pytest

from issue_flow import epic_session


def _current(tmp_path: Path) -> Path:
    path = tmp_path / ".issueflows" / "01-current-issues"
    path.mkdir(parents=True)
    return path


def test_missing_file_is_none(tmp_path: Path) -> None:
    assert epic_session.read_epic_session(_current(tmp_path)) is None


def test_round_trip(tmp_path: Path) -> None:
    current = _current(tmp_path)
    path = epic_session.write_epic_session(current, 269)
    assert path.name == "epic_session.md"
    session = epic_session.read_epic_session(current)
    assert session is not None
    assert session.epic == 269
    assert session.mode == epic_session.MODE_ONE_AND_ASK
    assert session.as_dict() == {"epic": 269, "mode": "one-and-ask"}


def test_unknown_mode_is_missing(tmp_path: Path) -> None:
    current = _current(tmp_path)
    (current / "epic_session.md").write_text(
        "epic: 9\nmode: manual\n", encoding="utf-8"
    )
    assert epic_session.read_epic_session(current) is None


def test_invalid_epic_is_missing(tmp_path: Path) -> None:
    current = _current(tmp_path)
    (current / "epic_session.md").write_text(
        "epic: nope\nmode: one-and-ask\n", encoding="utf-8"
    )
    assert epic_session.read_epic_session(current) is None


def test_missing_keys_is_missing(tmp_path: Path) -> None:
    current = _current(tmp_path)
    (current / "epic_session.md").write_text("epic: 9\n", encoding="utf-8")
    assert epic_session.read_epic_session(current) is None


def test_clear_removes_file(tmp_path: Path) -> None:
    current = _current(tmp_path)
    epic_session.write_epic_session(current, 3)
    assert epic_session.clear_epic_session(current) is True
    assert epic_session.read_epic_session(current) is None
    assert epic_session.clear_epic_session(current) is False


def test_write_rejects_unknown_mode(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown epic session mode"):
        epic_session.write_epic_session(_current(tmp_path), 1, mode="manual")
