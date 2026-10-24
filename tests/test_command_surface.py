"""The merged command surface and its noise budgets (issue #406).

issue-flow ships eleven lifecycle commands with modes. Mode instructions live
in side files next to each ``SKILL.md`` so an agent reads only what the mode
needs. These tests pin the surface, the progressive-disclosure layout, and
word budgets that keep the always-on context small.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from issue_flow.config import Settings
from issue_flow.editors import EDITORS, get_profile
from issue_flow.modes import resolve_mode
from issue_flow.templating import (
    COMMAND_NAMES,
    COMMANDS,
    COMMAND_RENAMES,
    DEFAULT_SKILL_DIRS,
    PSTACK_SKILL_NAMES,
    RETIRED_COMMANDS,
    RETIRED_SKILLS,
    STEM_RENAMES,
    build_manifest,
    render_template,
    rename_stem,
    skill_side_templates,
)

LIFECYCLE_STEMS = [stem for stem in DEFAULT_SKILL_DIRS if stem.startswith("iflow_")]

# Word budgets. The always-on rule loads into every agent session, so it gets
# the tightest cap; a SKILL.md loads on invocation; a mode file only when that
# mode runs.
RULE_BUDGET = 900
SKILL_BUDGET = 1600
SIDE_BUDGET = 3000
WORKFLOW_DOC_BUDGET = 1500

RETIRED_COMMAND_RE = re.compile(
    r"(?<![\w-])/?iflow-(?:capture|init|yolo|cycle|auto|drive|ops|fix|epic|split|"
    r"review|doctor|graphify|archive|pr-sync|workspace-git|version-bump|"
    r"history-update|comments)(?![\w-])"
)


def _words(text: str) -> int:
    return len(text.split())


@pytest.fixture
def loud_context(tmp_path: Path) -> dict[str, object]:
    """Render context with every optional rule section switched on."""
    cfg = tmp_path / ".issueflows" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        "[issueflow]\n"
        'pstack_skills = "all"\n'
        "caveman_default = true\n"
        "grill_me_default = true\n"
        "label_flows = true\n"
        "suggest_graphify = true\n"
        "remind_cleanup = true\n"
        "noob = true\n",
        encoding="utf-8",
    )
    return Settings().template_context(tmp_path, EDITORS["cursor"])


def test_surface_is_eleven_lifecycle_commands() -> None:
    assert len(COMMANDS) == 11
    assert len(LIFECYCLE_STEMS) == 11
    assert COMMAND_NAMES == [
        "iflow",
        "iflow-setup",
        "iflow-pick",
        "iflow-plan",
        "iflow-build",
        "iflow-pause",
        "iflow-close",
        "iflow-cleanup",
        "iflow-run",
        "iflow-issue",
        "iflow-status",
    ]
    standard = resolve_mode("standard")
    assert standard.skills == frozenset(DEFAULT_SKILL_DIRS)
    assert {"caveman", "grill_me"} < standard.skills
    assert "gh_ci" not in standard.skills


@pytest.mark.parametrize(
    ("stem", "sides"),
    [
        ("iflow_setup", {"harness.md.j2"}),
        ("iflow_pick", {"capture.md.j2", "comments.md.j2"}),
        ("iflow_run", {"yolo.md.j2", "cycle.md.j2", "auto.md.j2", "drive.md.j2"}),
        (
            "iflow_issue",
            {"new.md.j2", "fix.md.j2", "epic.md.j2", "split.md.j2", "review.md.j2"},
        ),
        ("iflow_status", {"doctor.md.j2", "git.md.j2", "graph.md.j2"}),
        (
            "iflow_close",
            {"ci.md.j2", "changelog.md.j2", "merge.md.j2", "ops.md.j2", "sync.md.j2", "version.md.j2"},
        ),
        (
            "iflow_cleanup",
            {"archive.md.j2", "classify.md.j2", "github.md.j2", "prs.md.j2", "workspace.md.j2"},
        ),
    ],
)
def test_merged_skills_ship_mode_files(stem: str, sides: set[str]) -> None:
    assert set(skill_side_templates(stem)) == sides


def test_router_names_every_mode_file(loud_context: dict[str, object]) -> None:
    """Each SKILL.md must point at every side file it ships, by name."""
    for stem in LIFECYCLE_STEMS:
        skill = render_template(f"skills/{stem}/SKILL.md.j2", loud_context)
        for side in skill_side_templates(stem):
            assert f"`{side.removesuffix('.j2')}`" in skill, (stem, side)


def test_side_files_carry_no_frontmatter_or_directive(
    loud_context: dict[str, object],
) -> None:
    """Mode files are plain markdown: no skill frontmatter, stamp, or footer."""
    for stem in LIFECYCLE_STEMS:
        for side in skill_side_templates(stem):
            text = render_template(f"skills/{stem}/{side}", loud_context)
            assert not text.startswith("---"), (stem, side)
            assert "issue-flow-version:" not in text, (stem, side)
            assert "MODEL & EXECUTION DIRECTIVE" not in text, (stem, side)
            assert "NEXT (noob)" not in text, (stem, side)


def test_rule_body_word_budget(loud_context: dict[str, object]) -> None:
    rule = render_template("rules/AGENTS.md.j2", loud_context)
    assert _words(rule) <= RULE_BUDGET, _words(rule)


def test_skill_and_side_word_budgets(loud_context: dict[str, object]) -> None:
    for stem in LIFECYCLE_STEMS:
        skill = render_template(f"skills/{stem}/SKILL.md.j2", loud_context)
        assert _words(skill) <= SKILL_BUDGET, (stem, _words(skill))
        for side in skill_side_templates(stem):
            text = render_template(f"skills/{stem}/{side}", loud_context)
            assert _words(text) <= SIDE_BUDGET, (stem, side, _words(text))


def test_workflow_doc_word_budget(loud_context: dict[str, object]) -> None:
    doc = render_template("docs/issue-workflow.md.j2", loud_context)
    assert _words(doc) <= WORKFLOW_DOC_BUDGET, _words(doc)


def test_no_template_names_a_retired_command(loud_context: dict[str, object]) -> None:
    rendered = {
        "rules/AGENTS.md.j2": render_template("rules/AGENTS.md.j2", loud_context),
        "docs/issue-workflow.md.j2": render_template(
            "docs/issue-workflow.md.j2", loud_context
        ),
    }
    for stem in LIFECYCLE_STEMS:
        rendered[stem] = render_template(f"skills/{stem}/SKILL.md.j2", loud_context)
        for side in skill_side_templates(stem):
            rendered[f"{stem}/{side}"] = render_template(
                f"skills/{stem}/{side}", loud_context
            )
    for name, text in rendered.items():
        hits = RETIRED_COMMAND_RE.findall(text)
        assert not hits, (name, hits)


def test_rule_lists_every_installed_command_once(
    loud_context: dict[str, object],
) -> None:
    rule = render_template("rules/AGENTS.md.j2", loud_context)
    for name, _purpose, _modes in COMMANDS:
        assert rule.count(f"| `{name}` |") == 1, name
    assert "starts with" in rule
    assert "`iflow <step> [args]`" in rule


def test_rule_body_keeps_the_core_contract(loud_context: dict[str, object]) -> None:
    rule = render_template("rules/AGENTS.md.j2", loud_context)
    assert "- [x] Done" in rule and "- [ ] Done" in rule
    assert "this-project.md" in rule
    assert "Never call bare `python`" in rule
    assert "conda run -n" in rule
    assert "issue-flow agent resolve" in rule
    assert "remind the user to run `/iflow-cleanup`" in rule
    assert "**On by default here**" in rule  # caveman_default
    assert "**On by default during `/iflow-plan` here.**" in rule  # grill_me_default
    for name in PSTACK_SKILL_NAMES:
        assert name in rule


def test_claude_rules_import_agents_md_once() -> None:
    claude = render_template("rules/CLAUDE.md.j2", {})
    assert "@AGENTS.md" in claude
    assert _words(claude) < 40


def test_cursor_rule_is_a_pointer(loud_context: dict[str, object]) -> None:
    mdc = render_template("rules/issueflow-rules.mdc.j2", loud_context)
    assert "AGENTS.md" in mdc
    assert _words(mdc) < 60


def test_claude_is_skills_first() -> None:
    assert get_profile("claude").commands_dir is None
    templates = [name for name, _ in build_manifest(get_profile("claude"))]
    assert not any(name.startswith("commands/") for name in templates)
    assert ("rules/CLAUDE.md.j2", "CLAUDE.md") in build_manifest(get_profile("claude"))


def test_opencode_gets_thin_wrappers() -> None:
    entries = [
        (name, path)
        for name, path in build_manifest(get_profile("opencode"))
        if name.startswith("commands/")
    ]
    assert len(entries) == len(COMMAND_NAMES)
    assert {name for name, _ in entries} == {"commands/_wrapper.md.j2"}
    wrapper = render_template(
        "commands/_wrapper.md.j2",
        {
            "agent_dir": ".opencode",
            "command_name": "iflow-run",
            "command_description": "Hands-off runs.",
        },
    )
    assert ".opencode/skills/iflow-run/SKILL.md" in wrapper
    assert "$ARGUMENTS" in wrapper
    assert _words(wrapper) < 40


def test_rename_maps_cover_every_retired_stem() -> None:
    for old, new in STEM_RENAMES.items():
        assert new in DEFAULT_SKILL_DIRS
        assert rename_stem(old) == new
    assert rename_stem("iflow-yolo") == "iflow-run"
    assert rename_stem("iflow-workspace-git") == "iflow-status"
    assert rename_stem("iflow_plan") == "iflow_plan"
    for old in COMMAND_RENAMES:
        assert old in RETIRED_COMMANDS
    for old in ("iflow-capture", "iflow-yolo", "gh-ci", "iflow-init", "iflow-comments"):
        assert old in RETIRED_SKILLS


def test_close_bundle_keeps_its_safety_contract(
    loud_context: dict[str, object],
) -> None:
    close = render_template("skills/iflow_close/SKILL.md.j2", loud_context)
    merge = render_template("skills/iflow_close/merge.md.j2", loud_context)
    sync = render_template("skills/iflow_close/sync.md.j2", loud_context)
    for token in ("`stay`", "`draft`", "`yolo`", "`ops`", "`nohistory`"):
        assert token in close, token
    assert "Never edit or stage `HISTORY.md` on the issue branch" in close
    assert "Changelog-Id" in close
    assert "--force-with-lease" in close
    assert "**Already merged**" in merge
    assert "--auto" in merge
    assert "Never `--admin`" in merge
    assert "base_detected: true" in sync
    assert "`--base <ref>`" in sync


def test_close_cleanup_reminder_and_auto_cleanup_are_gated(
    loud_context: dict[str, object],
) -> None:
    on = render_template("skills/iflow_close/SKILL.md.j2", loud_context)
    assert "Remind the user to run `/iflow-cleanup`" in on
    off = render_template(
        "skills/iflow_close/SKILL.md.j2", {**loud_context, "remind_cleanup": False}
    )
    assert "Remind the user to run `/iflow-cleanup`" not in off
    auto = render_template(
        "skills/iflow_close/SKILL.md.j2", {**loud_context, "auto_cleanup": True}
    )
    assert "Never merge because of this knob" in auto


def test_run_router_and_modes(loud_context: dict[str, object]) -> None:
    router = render_template("skills/iflow_run/SKILL.md.j2", loud_context)
    for mode in ("yolo", "cycle", "auto", "drive"):
        assert f"`{mode}.md`" in router
    cycle = render_template(
        "skills/iflow_run/cycle.md.j2", {**loud_context, "cycle_onfail": "skip"}
    )
    assert "Default from config **`skip`**" in cycle
    yolo = render_template("skills/iflow_run/yolo.md.j2", loud_context)
    assert "nohistory" in yolo and "stay" in yolo


def test_issue_router_sends_epic_text_to_anchor_creation(
    loud_context: dict[str, object],
) -> None:
    router = render_template("skills/iflow_issue/SKILL.md.j2", loud_context)
    assert "`epic <free text>`" in router
    assert "epic-anchor mode" in router
    epic = render_template("skills/iflow_issue/epic.md.j2", loud_context)
    assert "start [N]" in epic and "epic_session.md" in epic


def test_pick_captures_known_issue_directly(loud_context: dict[str, object]) -> None:
    pick = render_template("skills/iflow_pick/SKILL.md.j2", loud_context)
    assert "skip Phase 1" in pick
    assert "`capture.md`" in pick
    capture = render_template("skills/iflow_pick/capture.md.j2", loud_context)
    assert "`comments.md`" in capture
    assert "title,body,url,number,comments" in capture


def test_dispatcher_routes_capture_to_pick(loud_context: dict[str, object]) -> None:
    iflow = render_template("skills/iflow_iflow/SKILL.md.j2", loud_context)
    assert "`/iflow-pick <N>`" in iflow
    assert "Never auto-dispatch to any command other than" in iflow


def test_noob_footer_uses_merged_names(loud_context: dict[str, object]) -> None:
    issue = render_template("skills/iflow_issue/SKILL.md.j2", loud_context)
    assert "### NEXT (noob)" in issue
    assert "/iflow-issue epic <N> publish" in issue
    run = render_template("skills/iflow_run/SKILL.md.j2", loud_context)
    assert "### NEXT (noob)" in run
    assert "/iflow-cleanup" in run


def test_workflow_doc_lists_commands_and_modes(loud_context: dict[str, object]) -> None:
    doc = render_template("docs/issue-workflow.md.j2", loud_context)
    for name, _purpose, modes in COMMANDS:
        assert f"`/{name}`" in doc, name
        if modes != "—":
            assert modes in doc, name
    assert "iflow run cycle label:yolo" in doc


def test_removing_part_of_a_merged_skill_keeps_the_skill() -> None:
    from issue_flow.templating import rename_removed_stems

    assert rename_removed_stems(["gh_ci", "iflow_ops"]) == []
    assert rename_removed_stems(["iflow_yolo"]) == []
    assert rename_removed_stems(
        ["iflow_yolo", "iflow_cycle", "iflow_auto", "iflow_drive"]
    ) == ["iflow_run"]
    assert rename_removed_stems(["iflow-yolo", "iflow-cycle", "iflow-auto", "iflow-drive"]) == [
        "iflow-run"
    ]
    assert rename_removed_stems(["caveman", "iflow_epic"]) == ["caveman"]
