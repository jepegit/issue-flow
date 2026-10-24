"""Agent Skills lint (issue #268): parser, checks, doctor wiring, and a guard
that every packaged skill renders spec-clean for every editor."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from issue_flow.cli import app
from issue_flow.editors import EDITORS
from issue_flow.init import run_init
from issue_flow.skill_lint import (
    LINT_ERROR,
    LINT_INFO,
    LINT_WARN,
    lint_skill,
    parse_frontmatter,
)
from issue_flow.templating import skill_side_templates

LIFECYCLE_SIDE_FILES = {
    "iflow-" + stem.removeprefix("iflow_"): [s.removesuffix(".j2") for s in sides]
    for stem in (
        "iflow_setup",
        "iflow_pick",
        "iflow_run",
        "iflow_issue",
        "iflow_status",
        "iflow_close",
        "iflow_cleanup",
    )
    if (sides := skill_side_templates(stem))
}


def _skill(tmp_path: Path, name: str, frontmatter: str, body: str = "# Body\n") -> Path:
    folder = tmp_path / name
    folder.mkdir()
    (folder / "SKILL.md").write_text(
        f"---\n{frontmatter}---\n\n{body}", encoding="utf-8"
    )
    return folder


def _checks(findings: list) -> set[tuple[str, str]]:
    return {(f.check, f.severity) for f in findings}


# --- parser -----------------------------------------------------------------


@pytest.mark.essential
def test_parse_plain_quoted_and_folded() -> None:
    text = (
        "---\n"
        "name: demo\n"
        "description: >-\n"
        "  First line\n"
        "  second line.\n"
        "license: 'It''s MIT'\n"
        'compatibility: "Needs \\"uv\\""\n'
        "metadata:\n"
        "  author: me\n"
        "---\n"
        "# Body\n"
    )
    assert parse_frontmatter(text) == {
        "name": "demo",
        "description": "First line second line.",
        "license": "It's MIT",
        "compatibility": 'Needs "uv"',
        "metadata": "",
    }


@pytest.mark.essential
def test_parse_literal_block_and_crlf() -> None:
    text = "---\r\nname: demo\r\ndescription: |\r\n  a\r\n  b\r\n---\r\n"
    assert parse_frontmatter(text) == {"name": "demo", "description": "a\nb"}


@pytest.mark.essential
def test_parse_without_frontmatter_returns_none() -> None:
    assert parse_frontmatter("# Just a heading\n") is None
    assert parse_frontmatter("---\nname: demo\n") is None


# --- checks -----------------------------------------------------------------


@pytest.mark.essential
def test_clean_skill_with_issue_flow_keys_has_no_findings(tmp_path: Path) -> None:
    folder = _skill(
        tmp_path,
        "iflow-plan",
        "name: iflow-plan\n"
        "description: >-\n  Drafts a plan.\n"
        "disable-model-invocation: true\n"
        "issue-flow-version: 0.7.0\n",
    )
    assert lint_skill(folder) == []


@pytest.mark.essential
@pytest.mark.parametrize(
    "name",
    ["Demo", "-demo", "demo-", "de--mo", "de_mo", "a" * 65],
)
def test_invalid_names_are_errors(tmp_path: Path, name: str) -> None:
    folder = tmp_path / "x"
    folder.mkdir()
    (folder / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Does a thing.\n---\n", encoding="utf-8"
    )
    assert ("name", LINT_ERROR) in _checks(lint_skill(folder))


@pytest.mark.essential
def test_name_must_match_folder(tmp_path: Path) -> None:
    folder = _skill(tmp_path, "plan", "name: iflow-plan\ndescription: Drafts a plan.\n")
    assert _checks(lint_skill(folder)) == {("name_dir_mismatch", LINT_ERROR)}


@pytest.mark.essential
def test_missing_name_and_description(tmp_path: Path) -> None:
    folder = _skill(tmp_path, "demo", "license: MIT\n")
    assert _checks(lint_skill(folder)) == {
        ("name", LINT_ERROR),
        ("description", LINT_ERROR),
    }


@pytest.mark.essential
def test_description_too_long_or_with_xml_tag(tmp_path: Path) -> None:
    long_folder = _skill(tmp_path, "long", f"name: long\ndescription: {'x' * 1025}\n")
    assert _checks(lint_skill(long_folder)) == {("description", LINT_ERROR)}
    tag_folder = _skill(
        tmp_path, "tag", "name: tag\ndescription: Dispatches to /iflow-pick <N>.\n"
    )
    assert _checks(lint_skill(tag_folder)) == {("description", LINT_ERROR)}


@pytest.mark.essential
def test_unknown_key_warns(tmp_path: Path) -> None:
    folder = _skill(tmp_path, "demo", "name: demo\ndescription: Does it.\ntrigers: x\n")
    findings = lint_skill(folder)
    assert _checks(findings) == {("unknown_key", LINT_WARN)}
    assert "'trigers'" in findings[0].message


@pytest.mark.essential
def test_missing_skill_md_and_frontmatter(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert _checks(lint_skill(empty)) == {("missing_skill_md", LINT_ERROR)}
    bare = tmp_path / "bare"
    bare.mkdir()
    (bare / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
    assert _checks(lint_skill(bare)) == {("missing_frontmatter", LINT_ERROR)}


@pytest.mark.essential
def test_long_body_and_side_file_toc_are_info(tmp_path: Path) -> None:
    folder = _skill(
        tmp_path, "demo", "name: demo\ndescription: Does it.\n", body="line\n" * 501
    )
    (folder / "mode.md").write_text("# Mode\n" + "step\n" * 101, encoding="utf-8")
    (folder / "short.md").write_text("# Short\n", encoding="utf-8")
    (folder / "listed.md").write_text(
        "# Listed\n\n**Contents:** A · B\n" + "step\n" * 101, encoding="utf-8"
    )
    findings = lint_skill(folder)
    assert _checks(findings) == {("long_body", LINT_INFO), ("side_file_toc", LINT_INFO)}
    assert [f.path.name for f in findings if f.check == "side_file_toc"] == ["mode.md"]


# --- packaged skills guard --------------------------------------------------


@pytest.fixture(scope="module")
def scaffolded(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Every editor scaffolded with every optional (pstack) skill switched on."""
    root = tmp_path_factory.mktemp("lint-all")
    cfg = root / ".issueflows" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('[issueflow]\npstack_skills = "all"\n', encoding="utf-8")
    run_init(root, skip_dep_check=True, editors=list(EDITORS))
    return root


def test_every_packaged_skill_is_spec_clean(scaffolded: Path) -> None:
    skill_dirs = sorted({p.parent for p in scaffolded.rglob("SKILL.md")})
    assert len(skill_dirs) >= 4 * 13, skill_dirs  # every editor, every lifecycle skill
    problems = [
        f"{f.path.relative_to(scaffolded)}: {f.check} — {f.message}"
        for folder in skill_dirs
        for f in lint_skill(folder)
        if f.severity in (LINT_ERROR, LINT_WARN)
    ]
    assert problems == []


def test_side_files_keep_references_one_level_deep(scaffolded: Path) -> None:
    """A mode file names a sibling only to delegate, never as a file to read."""
    read_sibling = re.compile(r"\bread `([\w-]+\.md)`", re.IGNORECASE)
    skills = scaffolded / ".cursor" / "skills"
    for skill, sides in LIFECYCLE_SIDE_FILES.items():
        for side in sides:
            text = (skills / skill / side).read_text(encoding="utf-8")
            nested = set(read_sibling.findall(text)) & set(sides)
            assert not nested, (skill, side, nested)


def test_pick_router_points_at_capture_and_comments(scaffolded: Path) -> None:
    router = (scaffolded / ".cursor" / "skills" / "iflow-pick" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "read `capture.md` and `comments.md` in this skill folder" in router


# --- doctor wiring ----------------------------------------------------------


def _seed_issueflows(root: Path) -> None:
    for sub in (
        "00-tools",
        "01-current-issues",
        "02-partly-solved-issues",
        "03-solved-issues",
    ):
        (root / ".issueflows" / sub).mkdir(parents=True, exist_ok=True)


def test_doctor_reports_spec_findings(tmp_path: Path) -> None:
    _seed_issueflows(tmp_path)
    skills = tmp_path / ".claude" / "skills"
    skills.mkdir(parents=True)
    _skill(skills, "iflow-setup", "name: iflow-setup\ndescription: Sets up.\n")
    _skill(skills, "my-notes", "name: My Notes\ndescription: Mine.\n")

    result = CliRunner().invoke(app, ["doctor", str(tmp_path), "--json"])

    findings = json.loads(result.stdout)["findings"]
    spec = [f for f in findings if f["code"].startswith("skill_spec_")]
    assert [(f["code"], f["severity"]) for f in spec] == [("skill_spec_name", "warn")]
    assert ".claude/skills/my-notes/SKILL.md" in spec[0]["message"]
    assert result.exit_code == 0  # a user's own skill warns, it does not fail


def test_doctor_fails_on_broken_packaged_skill(tmp_path: Path) -> None:
    _seed_issueflows(tmp_path)
    skills = tmp_path / ".cursor" / "skills"
    skills.mkdir(parents=True)
    _skill(skills, "iflow-plan", "name: iflow-plan\ndescription: Plans <N>.\n")

    result = CliRunner().invoke(app, ["doctor", str(tmp_path), "--json"])

    codes = {(f["code"], f["severity"]) for f in json.loads(result.stdout)["findings"]}
    assert ("skill_spec_description", "error") in codes
    assert result.exit_code == 1
