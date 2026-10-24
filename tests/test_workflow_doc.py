"""Structure of the scaffolded command reference, docs/issue-workflow.md (#358, #406)."""

from __future__ import annotations

from pathlib import Path

import pytest

from issue_flow import modes
from issue_flow.init import run_init
from issue_flow.templating import COMMAND_NAMES, COMMANDS


def _render(tmp_path: Path, editor: str = "cursor", mode: str | None = None) -> str:
    run_init(tmp_path, skip_dep_check=True, editors=[editor], mode=mode)
    return (tmp_path / "docs" / "issue-workflow.md").read_text(encoding="utf-8")


def _row(doc: str, name: str) -> str:
    return next(line for line in doc.splitlines() if line.startswith(f"| `/{name}` |"))


@pytest.mark.parametrize("editor", ["cursor", "claude", "opencode", "codex"])
def test_command_reference_structure_per_editor(tmp_path: Path, editor: str) -> None:
    doc = _render(tmp_path, editor)

    assert doc.startswith("# issue-flow command reference\n")
    assert "{{" not in doc and "{%" not in doc
    assert doc.count("| Command | Modes | What it does | Installed in |") == 1
    for name, _purpose, modes_text in COMMANDS:
        assert modes_text in _row(doc, name), name
    assert "## The core loop" in doc
    assert "## Where the agent stops to ask" in doc


def test_command_reference_modes_column_matches_modes_toml(tmp_path: Path) -> None:
    doc = _render(tmp_path)
    membership = modes.command_mode_membership()
    for name in COMMAND_NAMES:
        assert _row(doc, name).rstrip(" |").endswith(", ".join(membership[name]))


def test_command_reference_marks_commands_missing_from_mode(tmp_path: Path) -> None:
    doc = _render(tmp_path, mode="novice")
    assert "*(not installed here)*" in _row(doc, "iflow-run")
    assert "*(not installed here)*" not in _row(doc, "iflow-plan")


@pytest.mark.essential
def test_command_mode_membership_lists_standard_first() -> None:
    membership = modes.command_mode_membership()
    assert set(membership) == set(COMMAND_NAMES)
    assert all(ids and ids[0] == "standard" for ids in membership.values())
    assert "novice" not in membership["iflow-run"]
    assert "novice" in membership["iflow-plan"]
