"""Trailer parse, release render, and changelog CLI guards (issue #404)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from issue_flow import history
from issue_flow.changelog import check_history_diff, list_notes, release
from issue_flow.cli import app

_ID_A = "aaaaaaaaaaaa"
_ID_B = "bbbbbbbbbbbb"
_ID_C = "cccccccccccc"
_ID_D = "dddddddddddd"


def _trailer(text: str, day: str, note_id: str) -> str:
    return f"Changelog: {text}\nChangelog-Date: {day}\nChangelog-Id: {note_id}\n"


def test_parse_collapses_repeated_id_inside_one_message() -> None:
    message = (
        "squash body\n\n"
        + _trailer("first in body. (#3)", "2026-04-01", _ID_C)
        + "\n"
        + _trailer("second in body. (#3)", "2026-04-02", _ID_C)
    )
    notes = history.parse_message_notes(message)
    assert len(notes) == 1
    assert notes[0].text == "second in body. (#3)"
    assert notes[0].note_date == "2026-04-02"
    assert notes[0].note_id == _ID_C


def test_merge_keeps_newest_text_for_an_id_and_sorts_by_date() -> None:
    older = history.parse_message_notes(_trailer("old text. (#2)", "2026-03-01", _ID_B))
    newer = history.parse_message_notes(_trailer("new text. (#2)", "2026-02-01", _ID_B))
    other = history.parse_message_notes(_trailer("other. (#4)", "2026-05-01", _ID_A))
    merged = history.merge_commit_notes([older, newer, other])
    assert [note.note_id for note in merged] == [_ID_B, _ID_A]
    assert merged[0].text == "new text. (#2)"
    assert merged[0].note_date == "2026-02-01"


def test_apply_release_folds_unreleased_and_leaves_older_section() -> None:
    original = (
        "# History\n\n"
        "## [Unreleased]\n\n"
        "- legacy bullet. (#9)\n\n"
        "## [0.1.0] - 2026-01-01\n\n"
        "- First. Unique old sentence.\n"
    )
    notes = [history.ChangelogNote("from trailer. (#2)", "2026-03-01", _ID_B, order=1)]
    section = history.render_release_section(
        "0.2.0", "2026-10-23", ["- legacy bullet. (#9)"], notes
    )
    updated = history.apply_release(original, section)
    assert "## [Unreleased]" not in updated
    assert "## [0.2.0] - 2026-10-23" in updated
    assert updated.index("legacy bullet") < updated.index("from trailer")
    assert f"<!-- changelog-ids: {_ID_B} -->" in updated
    assert "- First. Unique old sentence." in updated
    assert updated.index("## [0.2.0]") < updated.index("## [0.1.0]")


def test_recorded_ids_are_case_insensitive() -> None:
    text = f"<!-- changelog-ids: {_ID_D.upper()} -->\n"
    assert history.recorded_changelog_ids(text) == {_ID_D}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    return repo


def _commit(repo: Path, message: str, *paths: str) -> None:
    if paths:
        _git(repo, "add", *paths)
        _git(repo, "commit", "-m", message)
        return
    _git(repo, "commit", "--allow-empty", "-m", message)


def _write_history(repo: Path, body: str) -> None:
    (repo / "HISTORY.md").write_text(body, encoding="utf-8")


def test_list_skips_anchor_commit_and_recorded_ids_and_does_not_write(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    _write_history(
        repo,
        "# History\n\n"
        "## [0.1.0] - 2026-01-01\n\n"
        f"<!-- changelog-ids: {_ID_D} -->\n\n"
        "- First.\n",
    )
    _commit(
        repo,
        "seed\n\n" + _trailer("on the anchor. (#1)", "2026-01-01", _ID_A),
        "HISTORY.md",
    )
    before = (repo / "HISTORY.md").read_text(encoding="utf-8")
    _commit(repo, "replace\n\n" + _trailer("old text. (#2)", "2026-02-01", _ID_B))
    _commit(repo, "replace again\n\n" + _trailer("new text. (#2)", "2026-03-01", _ID_B))
    _commit(
        repo,
        "squash\n\n"
        + _trailer("first in body. (#3)", "2026-04-01", _ID_C)
        + "\n"
        + _trailer("second in body. (#3)", "2026-04-02", _ID_C),
    )
    _commit(
        repo, "already shipped\n\n" + _trailer("shipped. (#8)", "2026-04-03", _ID_D)
    )
    notes = list_notes(repo, "HISTORY.md")
    assert (repo / "HISTORY.md").read_text(encoding="utf-8") == before
    by_id = {note.note_id: note for note in notes}
    assert _ID_A not in by_id
    assert _ID_D not in by_id
    assert by_id[_ID_B].text == "new text. (#2)"
    assert by_id[_ID_C].text == "second in body. (#3)"
    assert [note.note_id for note in notes] == [_ID_B, _ID_C]


def test_release_refuses_empty_dirty_wrong_branch_and_repeat(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_history(repo, "# History\n\n## [0.1.0] - 2026-01-01\n\n- First.\n")
    _commit(repo, "seed", "HISTORY.md")
    original = (repo / "HISTORY.md").read_text(encoding="utf-8")

    empty = release(repo, "0.2.0", history_file="HISTORY.md", today="2026-10-23")
    assert empty.ok is False
    assert empty.reason == history.EMPTY_LIST
    assert (repo / "HISTORY.md").read_text(encoding="utf-8") == original

    (repo / "scratch.txt").write_text("x", encoding="utf-8")
    dirty = release(repo, "0.2.0", history_file="HISTORY.md", today="2026-10-23")
    assert dirty.reason == history.DIRTY_TREE
    (repo / "scratch.txt").unlink()

    _git(repo, "switch", "-c", "topic")
    wrong = release(repo, "0.2.0", history_file="HISTORY.md", today="2026-10-23")
    assert wrong.reason == history.NOT_DEFAULT_BRANCH
    _git(repo, "switch", "main")

    exists = release(repo, "v0.1.0", history_file="HISTORY.md", today="2026-10-23")
    assert exists.reason == history.VERSION_EXISTS
    assert (repo / "HISTORY.md").read_text(encoding="utf-8") == original


def test_release_prepends_section_and_drops_unreleased(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_history(
        repo, "# History\n\n## [0.1.0] - 2026-01-01\n\n- First. Unique old sentence.\n"
    )
    _commit(repo, "seed", "HISTORY.md")
    _commit(repo, "note\n\n" + _trailer("from trailer. (#2)", "2026-03-01", _ID_B))
    _write_history(
        repo,
        "# History\n\n"
        "## [Unreleased]\n\n"
        "- legacy bullet. (#9)\n\n"
        "## [0.1.0] - 2026-01-01\n\n"
        "- First. Unique old sentence.\n",
    )
    _commit(repo, "fold me", "HISTORY.md")
    result = release(repo, "0.2.0", history_file="HISTORY.md", today="2026-10-23")
    assert result.ok is True
    assert result.bullet_count == 2
    text = (repo / "HISTORY.md").read_text(encoding="utf-8")
    assert "## [Unreleased]" not in text
    assert "## [0.2.0] - 2026-10-23" in text
    assert text.index("- legacy bullet. (#9)") < text.index("- from trailer. (#2)")
    assert "- First. Unique old sentence." in text
    assert _ID_B in text


def test_release_refuses_when_head_moves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path)
    _write_history(repo, "# History\n\n## [Unreleased]\n\n- legacy. (#1)\n")
    _commit(repo, "seed", "HISTORY.md")
    calls = {"n": 0}

    def moving(_root: Path) -> str:
        calls["n"] += 1
        return "aaa" if calls["n"] == 1 else "bbb"

    monkeypatch.setattr("issue_flow.changelog.head_sha", moving)
    before = (repo / "HISTORY.md").read_text(encoding="utf-8")
    result = release(repo, "0.2.0", history_file="HISTORY.md", today="2026-10-23")
    assert result.reason == history.HEAD_MOVED
    assert (repo / "HISTORY.md").read_text(encoding="utf-8") == before


def test_check_rejects_feature_history_diff_and_allows_release(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_history(repo, "# History\n\n## [0.1.0] - 2026-01-01\n\n- First.\n")
    _commit(repo, "base", "HISTORY.md")
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    untouched = check_history_diff(repo, "HISTORY.md", base)
    assert untouched.ok is True
    assert untouched.changed is False

    _write_history(
        repo, "# History\n\n## [0.1.0] - 2026-01-01\n\n- Edited by a feature.\n"
    )
    _commit(repo, "feature edit", "HISTORY.md")
    refused = check_history_diff(repo, "HISTORY.md", base)
    assert refused.ok is False
    assert refused.changed is True

    _git(repo, "reset", "--hard", base)
    _write_history(repo, "# History\n\n## [0.2.0] - 2026-10-23\n\n- Cut.\n")
    _commit(repo, "Release 0.2.0\n\nChangelog-Release: 0.2.0\n", "HISTORY.md")
    allowed = check_history_diff(repo, "HISTORY.md", base)
    assert allowed.ok is True
    assert allowed.changed is True


def test_cli_list_release_and_check(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write_history(repo, "# History\n\n## [0.1.0] - 2026-01-01\n\n- First.\n")
    _commit(repo, "seed", "HISTORY.md")
    _commit(repo, "note\n\n" + _trailer("cli bullet. (#7)", "2026-06-01", _ID_A))
    runner = CliRunner()
    listed = runner.invoke(app, ["changelog", "list", str(repo), "--json"])
    assert listed.exit_code == 0, listed.output
    assert "cli bullet. (#7)" in listed.stdout
    released = runner.invoke(
        app,
        ["changelog", "release", "0.2.0", str(repo), "--date", "2026-10-23", "--json"],
    )
    assert released.exit_code == 0, released.output
    text = (repo / "HISTORY.md").read_text(encoding="utf-8")
    assert "## [0.2.0] - 2026-10-23" in text
    assert "cli bullet. (#7)" in text
    again = runner.invoke(app, ["changelog", "release", "0.3.0", str(repo)])
    assert again.exit_code == 1
    assert "dirty_tree" in again.stdout
