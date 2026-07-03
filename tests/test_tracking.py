"""Tests for issue_flow.tracking — the read-only .issueflows/ reader."""

from __future__ import annotations

from pathlib import Path

from issue_flow import tracking


def _write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _current(tmp_path: Path) -> Path:
    return tmp_path / ".issueflows" / "01-current-issues"


def _partly(tmp_path: Path) -> Path:
    return tmp_path / ".issueflows" / "02-partly-solved-issues"


def _solved(tmp_path: Path) -> Path:
    return tmp_path / ".issueflows" / "03-solved-issues"


# ---------------------------------------------------------------------------
# done detection
# ---------------------------------------------------------------------------


def test_file_marks_done_checked(tmp_path: Path) -> None:
    p = _write(tmp_path / "issue1_status.md", "Progress notes\n\n- [x] Done\n")
    assert tracking.file_marks_done(p) is True


def test_file_marks_done_unchecked(tmp_path: Path) -> None:
    p = _write(tmp_path / "issue1_status.md", "- [ ] Done\n")
    assert tracking.file_marks_done(p) is False


def test_file_marks_done_case_insensitive(tmp_path: Path) -> None:
    p = _write(tmp_path / "issue1_status.md", "- [X] DONE everything\n")
    assert tracking.file_marks_done(p) is True


def test_file_marks_done_missing_file(tmp_path: Path) -> None:
    assert tracking.file_marks_done(tmp_path / "nope.md") is False


# ---------------------------------------------------------------------------
# grouping + stage
# ---------------------------------------------------------------------------


def test_group_issue_files_groups_by_number(tmp_path: Path) -> None:
    cur = _current(tmp_path)
    _write(cur / "issue42_original.md", "# Issue #42: Foo\n")
    _write(cur / "issue42_plan.md")
    _write(cur / "issue7_original.md")
    _write(cur / "notes.md")  # ignored: not an issue file

    groups = tracking.group_issue_files(cur)

    assert set(groups) == {42, 7}
    assert len(groups[42].files) == 2
    assert groups[42].original is not None
    assert groups[42].plan is not None


def test_group_issue_files_missing_folder(tmp_path: Path) -> None:
    assert tracking.group_issue_files(tmp_path / "does-not-exist") == {}


def test_stage_init_when_no_original(tmp_path: Path) -> None:
    group = tracking.IssueGroup(number=1, location="01-current-issues")
    assert group.stage == tracking.STAGE_INIT


def test_stage_plan_when_only_original(tmp_path: Path) -> None:
    cur = _current(tmp_path)
    _write(cur / "issue5_original.md")
    group = tracking.group_issue_files(cur)[5]
    assert group.stage == tracking.STAGE_PLAN
    assert group.next_command == "/iflow-plan"


def test_stage_start_when_plan_but_not_done(tmp_path: Path) -> None:
    cur = _current(tmp_path)
    _write(cur / "issue5_original.md")
    _write(cur / "issue5_plan.md")
    _write(cur / "issue5_status.md", "- [ ] Done\n")
    group = tracking.group_issue_files(cur)[5]
    assert group.stage == tracking.STAGE_START


def test_stage_close_when_done(tmp_path: Path) -> None:
    cur = _current(tmp_path)
    _write(cur / "issue5_original.md")
    _write(cur / "issue5_plan.md")
    _write(cur / "issue5_status.md", "- [x] Done\n")
    group = tracking.group_issue_files(cur)[5]
    assert group.stage == tracking.STAGE_CLOSE
    assert group.next_command == "/iflow-close"


def test_title_parsed_from_heading(tmp_path: Path) -> None:
    cur = _current(tmp_path)
    _write(cur / "issue5_original.md", "# Issue #5: Make it faster\n\nbody\n")
    group = tracking.group_issue_files(cur)[5]
    assert group.title() == "Make it faster"


# ---------------------------------------------------------------------------
# focus resolution
# ---------------------------------------------------------------------------


def test_issue_number_from_branch() -> None:
    assert tracking.issue_number_from_branch("42-fix-login") == 42
    assert tracking.issue_number_from_branch("main") is None
    assert tracking.issue_number_from_branch("") is None
    assert tracking.issue_number_from_branch(None) is None


def test_resolve_focus_branch_wins(tmp_path: Path) -> None:
    cur = _current(tmp_path)
    _write(cur / "issue9_original.md")
    focus = tracking.resolve_focus(cur, "42-something")
    assert focus.number == 42
    assert focus.resolved_via == "branch"


def test_resolve_focus_single_group(tmp_path: Path) -> None:
    cur = _current(tmp_path)
    _write(cur / "issue9_original.md")
    focus = tracking.resolve_focus(cur, "main")
    assert focus.number == 9
    assert focus.resolved_via == "single-group"


def test_resolve_focus_none(tmp_path: Path) -> None:
    cur = _current(tmp_path)
    cur.mkdir(parents=True)
    focus = tracking.resolve_focus(cur, "main")
    assert focus.number is None
    assert focus.resolved_via == "none"


def test_resolve_focus_ambiguous(tmp_path: Path) -> None:
    cur = _current(tmp_path)
    _write(cur / "issue1_original.md")
    _write(cur / "issue2_original.md")
    focus = tracking.resolve_focus(cur, "feature-branch")
    assert focus.number is None
    assert focus.resolved_via == "ambiguous"
    assert focus.candidates == [1, 2]


# ---------------------------------------------------------------------------
# sweep
# ---------------------------------------------------------------------------


def test_plan_sweep_routes_by_done(tmp_path: Path) -> None:
    cur, partly, solved = _current(tmp_path), _partly(tmp_path), _solved(tmp_path)
    _write(cur / "issue1_original.md")
    _write(cur / "issue1_status.md", "- [x] Done\n")
    _write(cur / "issue2_original.md")
    _write(cur / "issue2_status.md", "- [ ] Done\n")
    _write(cur / "issue3_original.md")  # focus, excepted

    moves = tracking.plan_sweep(cur, partly, solved, except_number=3)

    by_number = {m.number: m for m in moves}
    assert set(by_number) == {1, 2}
    assert by_number[1].destination == solved.name
    assert by_number[2].destination == partly.name


def test_apply_sweep_moves_files(tmp_path: Path) -> None:
    cur, partly, solved = _current(tmp_path), _partly(tmp_path), _solved(tmp_path)
    _write(cur / "issue1_original.md")
    _write(cur / "issue1_status.md", "- [x] Done\n")
    _write(cur / "issue2_original.md")

    moves = tracking.plan_sweep(cur, partly, solved, except_number=None)
    tracking.apply_sweep(moves, partly, solved)

    assert not (cur / "issue1_original.md").exists()
    assert (solved / "issue1_original.md").exists()
    assert (solved / "issue1_status.md").exists()
    assert (partly / "issue2_original.md").exists()


def test_plan_sweep_excepts_focus(tmp_path: Path) -> None:
    cur, partly, solved = _current(tmp_path), _partly(tmp_path), _solved(tmp_path)
    _write(cur / "issue5_original.md")
    moves = tracking.plan_sweep(cur, partly, solved, except_number=5)
    assert moves == []


# ---------------------------------------------------------------------------
# archive
# ---------------------------------------------------------------------------


def test_plan_archive_collects_groups_and_titles(tmp_path: Path) -> None:
    solved = _solved(tmp_path)
    _write(solved / "issue1_original.md", "# Issue #1: First thing\n")
    _write(solved / "issue1_status.md", "- [x] Done\n")
    _write(solved / "issue2_original.md", "# Issue #2: Second thing\n")

    moves, missing = tracking.plan_archive(solved, [1, 2])

    assert missing == []
    by_number = {m.number: m for m in moves}
    assert set(by_number) == {1, 2}
    assert by_number[1].title == "First thing"
    assert len(by_number[1].files) == 2


def test_plan_archive_reports_missing(tmp_path: Path) -> None:
    solved = _solved(tmp_path)
    _write(solved / "issue1_original.md")

    moves, missing = tracking.plan_archive(solved, [1, 99])

    assert [m.number for m in moves] == [1]
    assert missing == [99]


def test_plan_archive_deduplicates_requests(tmp_path: Path) -> None:
    solved = _solved(tmp_path)
    _write(solved / "issue1_original.md")

    moves, missing = tracking.plan_archive(solved, [1, 1, 1])

    assert [m.number for m in moves] == [1]
    assert missing == []


def test_apply_archive_deletes_files(tmp_path: Path) -> None:
    solved = _solved(tmp_path)
    _write(solved / "issue1_original.md")
    _write(solved / "issue1_status.md", "- [x] Done\n")
    _write(solved / "issue2_original.md")  # not archived

    moves, _ = tracking.plan_archive(solved, [1])
    removed = tracking.apply_archive(moves)

    assert sorted(p.name for p in removed) == [
        "issue1_original.md",
        "issue1_status.md",
    ]
    assert not (solved / "issue1_original.md").exists()
    assert not (solved / "issue1_status.md").exists()
    assert (solved / "issue2_original.md").exists()


def test_apply_archive_skips_already_gone(tmp_path: Path) -> None:
    solved = _solved(tmp_path)
    _write(solved / "issue1_original.md")

    moves, _ = tracking.plan_archive(solved, [1])
    (solved / "issue1_original.md").unlink()
    removed = tracking.apply_archive(moves)

    assert removed == []


def test_dated_archive_file_is_not_grouped(tmp_path: Path) -> None:
    """The summary file's dated name must never join an issue group."""
    solved = _solved(tmp_path)
    _write(solved / "2026-07-03_archived_issues.md", "# Archived issues\n")
    _write(solved / "issue1_original.md")

    assert set(tracking.group_issue_files(solved)) == {1}
