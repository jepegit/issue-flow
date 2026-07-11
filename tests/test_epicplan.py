"""Tests for issue_flow.epicplan — the epic plan-file parser."""

from __future__ import annotations

from pathlib import Path

from issue_flow.epicplan import parse_epic_plan

_PLAN = """# Epic #144: Staged planning mode

Anchor: https://github.com/octo/repo/issues/144
Status: confirmed

## Goal

Make big changes manageable.

## Constraints

None worth noting.

## Stage 1 — foundation

Prove the scaffold.

### Issue: Add the epic skill

- Spec: Draft-only skill plus the folder.
- Depends on: none
- yolo: no — design work
- Published: #136

### Issue: Publish the plan

- Spec: Turn a confirmed plan into GitHub issues.
- Depends on: #136
- yolo: no — outward-facing writes
- Published: #137

## Stage 2 — navigation

Make daily commands epic-aware.

### Issue: Deterministic epic-status CLI

- Spec: Read-only progress command.
- Depends on: #136, #137
- yolo: yes — additive CLI following a proven pattern

### Issue: Pick integration

- Spec: /iflow-pick prefers the active epic.
- Depends on: stage 2 issue 1
- yolo: no

## Later (unstaged)

- Some sketchy future idea that must not parse as a stage.

### Issue: Not a real spec

- Spec: must be ignored.
"""


def _write_plan(tmp_path: Path, text: str = _PLAN) -> Path:
    path = tmp_path / "epic144_plan.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_header_and_status(tmp_path: Path) -> None:
    plan = parse_epic_plan(_write_plan(tmp_path))
    assert plan is not None
    assert plan.number == 144
    assert plan.title == "Staged planning mode"
    assert plan.status == "confirmed"


def test_parse_stages_and_specs(tmp_path: Path) -> None:
    plan = parse_epic_plan(_write_plan(tmp_path))
    assert plan is not None
    assert [stage.index for stage in plan.stages] == [1, 2]
    assert plan.stages[0].title == "foundation"
    stage1 = plan.stages[0].issues
    assert [spec.title for spec in stage1] == [
        "Add the epic skill",
        "Publish the plan",
    ]
    assert stage1[0].published == 136
    assert stage1[0].depends_on == []
    assert stage1[1].depends_on == [136]
    assert stage1[1].yolo is False


def test_parse_yolo_flag_and_unpublished(tmp_path: Path) -> None:
    plan = parse_epic_plan(_write_plan(tmp_path))
    assert plan is not None
    stage2 = plan.stages[1].issues
    assert stage2[0].published is None
    assert stage2[0].yolo is True
    assert stage2[0].depends_on == [136, 137]


def test_placeholder_stays_until_target_published(tmp_path: Path) -> None:
    plan = parse_epic_plan(_write_plan(tmp_path))
    assert plan is not None
    pick = plan.stages[1].issues[1]
    # "stage 2 issue 1" is unpublished, so the placeholder remains.
    assert pick.placeholder_deps == [(2, 1)]
    assert pick.depends_on == []


def test_placeholder_resolves_to_published_number(tmp_path: Path) -> None:
    text = _PLAN.replace(
        "- Spec: Read-only progress command.\n- Depends on: #136, #137\n"
        "- yolo: yes — additive CLI following a proven pattern",
        "- Spec: Read-only progress command.\n- Depends on: #136, #137\n"
        "- yolo: yes — additive CLI following a proven pattern\n- Published: #138",
    )
    plan = parse_epic_plan(_write_plan(tmp_path, text))
    assert plan is not None
    pick = plan.stages[1].issues[1]
    assert pick.placeholder_deps == []
    assert pick.depends_on == [138]


def test_later_section_is_ignored(tmp_path: Path) -> None:
    plan = parse_epic_plan(_write_plan(tmp_path))
    assert plan is not None
    all_titles = [spec.title for stage in plan.stages for spec in stage.issues]
    assert "Not a real spec" not in all_titles


def test_missing_file_returns_none(tmp_path: Path) -> None:
    assert parse_epic_plan(tmp_path / "epic1_plan.md") is None
