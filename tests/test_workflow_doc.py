"""Structure of the scaffolded command reference, docs/issue-workflow.md (#358)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from issue_flow import modes
from issue_flow.init import run_init
from issue_flow.templating import COMMAND_NAMES

LABELS = (
    "**When to use:**",
    "**Arguments:**",
    "**What it asks you:**",
    "**Result:**",
    "**Related:**",
)


def _render(tmp_path: Path, editor: str = "cursor", mode: str | None = None) -> str:
    run_init(tmp_path, skip_dep_check=True, editors=[editor], mode=mode)
    return (tmp_path / "docs" / "issue-workflow.md").read_text(encoding="utf-8")


def _command_sections(doc: str) -> dict[str, str]:
    """Map ``/iflow-x`` → the text of its ``### `/iflow-x` …`` section."""
    parts = re.split(r"^### `(/iflow[a-z-]*)`.*$", doc, flags=re.MULTILINE)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


@pytest.mark.parametrize("editor", ["cursor", "claude", "opencode", "codex"])
def test_command_reference_structure_per_editor(tmp_path: Path, editor: str) -> None:
    doc = _render(tmp_path, editor)

    assert doc.startswith("# issue-flow command reference\n")
    assert "{{" not in doc and "{%" not in doc
    assert not re.search(r"^## \d", doc, flags=re.MULTILINE), "numbered headings"
    assert doc.count("| Command | What it does | Path | Modes |") == 1

    sections = _command_sections(doc)
    assert set(sections) == {f"/{name}" for name in COMMAND_NAMES}
    for command, body in sections.items():
        for label in LABELS:
            assert label in body, f"{command} is missing {label}"
        assert "**What it does" in body, f"{command} is missing What it does"


def test_command_reference_modes_column_matches_modes_toml(tmp_path: Path) -> None:
    doc = _render(tmp_path)
    membership = modes.command_mode_membership()
    for name in COMMAND_NAMES:
        row = next(
            line for line in doc.splitlines() if line.startswith(f"| `/{name}` |")
        )
        assert row.rstrip(" |").endswith(", ".join(membership[name])), row


def test_command_reference_marks_commands_missing_from_mode(tmp_path: Path) -> None:
    doc = _render(tmp_path, mode="novice")
    yolo = next(
        line for line in doc.splitlines() if line.startswith("| `/iflow-yolo` |")
    )
    plan = next(
        line for line in doc.splitlines() if line.startswith("| `/iflow-plan` |")
    )
    assert "*not installed here*" in yolo
    assert "*not installed here*" not in plan
    # Every command is still documented, as an upgrade guide.
    assert "### `/iflow-yolo`" in doc


@pytest.mark.essential
def test_command_mode_membership_lists_standard_first() -> None:
    membership = modes.command_mode_membership()
    assert set(membership) == set(COMMAND_NAMES)
    assert all(ids and ids[0] == "standard" for ids in membership.values())
    assert "novice" not in membership["iflow-yolo"]
    assert "novice" in membership["iflow-plan"]
