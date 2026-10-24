"""Tests for issue_flow.templating."""

from __future__ import annotations

import re
from pathlib import Path

from issue_flow import __version__ as ISSUE_FLOW_VERSION
from issue_flow.editors import EDITORS, get_profile
from issue_flow.step_profiles import PACKAGED_DEFAULTS, enrich_render_context
from issue_flow.templating import (
    COMMANDS,
    COMMAND_NAMES,
    DEFAULT_SKILL_DIRS,
    PSTACK_NAME_TO_STEM,
    PSTACK_SKILL_NAMES,
    SKILL_DIRS,
    TEMPLATE_MANIFEST,
    build_canonical_manifest,
    build_manifest,
    is_skill_template,
    noob_stem_for_template,
    packaged_skill_output_names,
    render_template,
    resolve_output_path,
    skill_side_templates,
    stamp_skill_version,
)

def _skill_bundle(stem: str, context: dict) -> str:
    """Render a skill folder: ``SKILL.md`` plus every mode file (issue #406)."""
    parts = [render_template(f"skills/{stem}/SKILL.md.j2", context)]
    for side in skill_side_templates(stem):
        parts.append(render_template(f"skills/{stem}/{side}", context))
    return "\n".join(parts)


def _render(template_name: str, context: dict) -> str:
    """Render ``template_name``; skill and command templates render their whole skill.

    Mode content moved out of ``SKILL.md`` into side files, and command files
    became thin wrappers, so content assertions read the skill folder as a
    bundle.
    """
    match = re.fullmatch(r"commands/(iflow(?:-[a-z]+)?)(?: [a-z]+)?\.md\.j2", template_name)
    if match:
        name = match.group(1)
        stem = "iflow_iflow" if name == "iflow" else name.replace("-", "_")
        return _skill_bundle(stem, context)
    match = re.fullmatch(r"skills/([a-z_]+)/[a-zA-Z_]+\.md\.j2", template_name)
    if match and not template_name.startswith("skills/_"):
        return _skill_bundle(match.group(1), context)
    return render_template(template_name, context)


# The standard surface: every default stem, no opt-in (pstack) stems.
_ALL_SKILLS = sorted(DEFAULT_SKILL_DIRS)
_ALL_COMMANDS = sorted(COMMAND_NAMES)
_MODE_CONTEXT = {
    "mode": "standard",
    "mode_name": "Standard",
    "included_skills": _ALL_SKILLS,
    "included_commands": _ALL_COMMANDS,
    "command_rows": list(COMMANDS),
    "caveman_default": False,
    "grill_me_default": False,
    "label_flows": True,
    "yolo_label": "yolo",
    "ops_label": "ops",
    "publish_label": "publish",
    "checks_watch_minutes": 15,
    "step_directives": True,
    "model_label_flows": False,
    "deep_model_label": "deep",
    "fast_model_label": "fast",
    "step_profiles": dict(PACKAGED_DEFAULTS),
    "remind_cleanup": True,
    "noob": False,
    "cleanup_include_github": False,
    "cleanup_yes_a1": False,
    "cleanup_yes_a2": False,
    "on_bleeding_edge": False,
    "suggest_graphify": True,
    "auto_graphify_on_plan": False,
    "graphify_gitignored": False,
    "auto_switchback": True,
    "auto_remove_worktree": True,
    "worktree_first": True,
    "pr_merge_method": "squash",
    "cycle_max_issues": 10,
    "cycle_onfail": "stop",
    "cycle_nonyolo": "merge",
    "auto_adversarial_loops": 2,
    "confirm_version_bump": False,
    "ruff_autofix": True,
    "auto_close": False,
    "auto_cleanup": False,
    "auto_plan": True,
    "auto_build": True,
    "hands_off": False,
    "early_pr": False,
    "fix_auto_name": False,
    "confirm_changelog_update": True,
    "defer_changelog": False,
    "essential_tests": False,
    "test_runner": "pytest",
    "essential_marker": "essential",
    "essential_review": "close",
    "pstack_skills": [],
}


def test_all_templates_render_without_error() -> None:
    """Every template in the manifest should render with default context values."""
    context = {
        "issueflows_dir": ".issueflows",
        "agent_dir": ".cursor",
        "docs_dir": "docs",
        "history_file": "HISTORY.md",
        "tools_folder": "00-tools",
        "current_issues_folder": "01-current-issues",
        "partly_solved_folder": "02-partly-solved-issues",
        "solved_folder": "03-solved-issues",
        "designs_folder": "04-designs-and-guides",
        "project_name": "test-project",
        "editor": "cursor",
        "editor_name": "Cursor",
        "commands_dir": "commands",
        "commands_supported": False,
        "graphify_installer": "cursor",
        **_MODE_CONTEXT,
    }
    for template_name, _ in TEMPLATE_MANIFEST:
        ctx = enrich_render_context(context, template_name)
        result = _render(template_name, ctx)
        assert isinstance(result, str)
        assert len(result) > 0, f"Template {template_name} rendered empty"


def test_template_substitution() -> None:
    """Template variables should be replaced in the rendered output."""
    context = {
        "issueflows_dir": "CUSTOM_DIR",
        "agent_dir": ".cursor",
        "docs_dir": "docs",
        "history_file": "HISTORY.md",
        "tools_folder": "00-tools",
        "current_issues_folder": "01-current-issues",
        "partly_solved_folder": "02-partly-solved-issues",
        "solved_folder": "03-solved-issues",
        "designs_folder": "04-designs-and-guides",
        "project_name": "my-project",
        "editor": "cursor",
        "editor_name": "Cursor",
        "commands_dir": "commands",
        "commands_supported": True,
        "graphify_installer": "cursor",
        **_MODE_CONTEXT,
    }
    rendered = _render("commands/iflow-pick.md.j2", context)
    assert "CUSTOM_DIR/01-current-issues" in rendered
    assert "{{ issueflows_dir }}" not in rendered


def test_project_brief_template_renders() -> None:
    """The durable project brief starter template should render with placeholders."""
    rendered = _render("docs/this-project.md.j2", _default_context())
    assert "# test-project" in rendered
    assert "What this project is" in rendered
    assert "How to run / test" in rendered
    assert "Entry points" in rendered


def test_resolve_output_path() -> None:
    context = {"agent_dir": ".cursor", "docs_dir": "docs"}
    path = resolve_output_path("{agent_dir}/commands/iflow-setup.md", context)
    assert path == Path(".cursor/commands/iflow-setup.md")


def _resolved_paths(profile_id: str) -> set[str]:
    """All resolved output paths for a profile, as forward-slash strings."""
    profile = get_profile(profile_id)
    context = {
        "agent_dir": profile.agent_dir,
        "commands_dir": profile.commands_dir or "commands",
        "docs_dir": "docs",
    }
    return {
        resolve_output_path(path_template, context).as_posix()
        for _, path_template in build_manifest(profile)
    }


def test_build_manifest_cursor_has_skills_and_rules_but_no_commands() -> None:
    """Cursor now uses Agent Skills as the primary slash-menu surface."""
    manifest = build_manifest(get_profile("cursor"))
    template_names = [name for name, _ in manifest]
    paths = _resolved_paths("cursor")
    assert not any(name.startswith("commands/") for name in template_names)
    assert ".cursor/skills/iflow/SKILL.md" in paths
    assert ".cursor/skills/iflow-iflow/SKILL.md" not in paths
    assert ".cursor/rules/issueflow-rules.mdc" in paths


def test_build_manifest_opencode_uses_singular_command_dir() -> None:
    paths = _resolved_paths("opencode")
    assert ".opencode/command/iflow-setup.md" in paths
    assert ".opencode/skills/iflow-setup/SKILL.md" in paths
    # opencode has no editor-specific rules file (AGENTS.md is handled by init).
    assert not any(p.endswith(".mdc") for p in paths)
    assert "CLAUDE.md" not in paths


def test_build_manifest_no_cursor_leakage_in_non_cursor_outputs() -> None:
    """Non-cursor editors must not write under .cursor/ or mention "Cursor"."""
    for editor_id in ("claude", "opencode", "codex"):
        profile = get_profile(editor_id)
        context = {
            "issueflows_dir": ".issueflows",
            "agent_dir": profile.agent_dir,
            "docs_dir": "docs",
            "history_file": "HISTORY.md",
            "tools_folder": "00-tools",
            "current_issues_folder": "01-current-issues",
            "partly_solved_folder": "02-partly-solved-issues",
            "solved_folder": "03-solved-issues",
            "designs_folder": "04-designs-and-guides",
            "project_name": "test-project",
            "editor": profile.id,
            "editor_name": profile.name,
            "commands_dir": profile.commands_dir or "commands",
            "commands_supported": profile.commands_dir is not None,
            "graphify_installer": profile.graphify_installer or "",
            **_MODE_CONTEXT,
        }
        manifest = build_manifest(profile) + [("rules/AGENTS.md.j2", "AGENTS.md")]
        for template_name, path_template in manifest:
            resolved = resolve_output_path(path_template, context).as_posix()
            assert ".cursor" not in resolved, f"{editor_id}: {resolved}"
            rendered = _render(template_name, context)
            assert "Cursor" not in rendered, (
                f"{editor_id} output {template_name} leaks literal 'Cursor'"
            )


def test_manifest_has_expected_skills() -> None:
    """Every expected skill has a default Cursor manifest entry."""
    template_names = {name for name, _ in TEMPLATE_MANIFEST}
    assert not any(name.startswith("commands/") for name in template_names)
    assert (
        "skills/iflow_iflow/SKILL.md.j2",
        "{agent_dir}/skills/iflow/SKILL.md",
    ) in TEMPLATE_MANIFEST
    for skill in (
        "iflow_setup",
        "iflow_pick",
        "iflow_setup",
        "iflow_pick",
        "iflow_pick",
        "iflow_plan",
        "iflow_build",
        "iflow_pause",
        "iflow_close",
        "iflow_cleanup",
        "iflow_run",
        "iflow_issue",
        "iflow_issue",
        "iflow_issue",
        "iflow_status",
        "iflow_status",
        "iflow_cleanup",
        "iflow_run",
        "iflow_run",
        "iflow_run",
        "iflow_close",
        "iflow_close",
        "iflow_status",
    ):
        assert f"skills/{skill}/SKILL.md.j2" in template_names


def _default_context() -> dict[str, object]:
    return {
        "issue_flow_version": ISSUE_FLOW_VERSION,
        "issueflows_dir": ".issueflows",
        "agent_dir": ".cursor",
        "docs_dir": "docs",
        "history_file": "HISTORY.md",
        "tools_folder": "00-tools",
        "current_issues_folder": "01-current-issues",
        "partly_solved_folder": "02-partly-solved-issues",
        "solved_folder": "03-solved-issues",
        "designs_folder": "04-designs-and-guides",
        "project_name": "test-project",
        "editor": "cursor",
        "editor_name": "Cursor",
        "commands_dir": "commands",
        "commands_supported": True,
        "graphify_installer": "cursor",
        **_MODE_CONTEXT,
    }


def test_issue_start_mentions_branch_and_sweep_preflight() -> None:
    """The /iflow-build command must include the new preflight and sweep steps."""
    rendered = _render("commands/iflow-build.md.j2", _default_context())
    assert "Branch status preflight" in rendered
    assert "Sweep stale current issues" in rendered
    assert "git fetch --prune" in rendered


_CLI_FASTPATH_SURFACES = {
    "commands/iflow.md.j2": "issue-flow agent state",
    "commands/iflow-status.md.j2": "issue-flow status",
    "commands/iflow-pick.md.j2": "issue-flow agent capture",
    "commands/iflow-build.md.j2": "issue-flow agent preflight",
    "commands/iflow-plan.md.j2": "issue-flow agent preflight",
    "skills/iflow_iflow/SKILL.md.j2": "issue-flow agent state",
    "skills/iflow_status/SKILL.md.j2": "issue-flow status",
    "skills/iflow_pick/capture.md.j2": "issue-flow agent capture",
    "skills/iflow_build/SKILL.md.j2": "issue-flow agent preflight",
    "skills/iflow_plan/SKILL.md.j2": "issue-flow agent preflight",
    "commands/iflow-cleanup archive.md.j2": "issue-flow agent archive",
    "skills/iflow_cleanup/archive.md.j2": "issue-flow agent archive",
    "commands/iflow-issue review.md.j2": "issue-flow agent label-candidates",
    "skills/iflow_issue/review.md.j2": "issue-flow agent label-candidates",
}


def test_cli_fast_path_notes_render_with_fallback() -> None:
    """Updated surfaces advertise the optional CLI fast path AND keep a fallback."""
    for template_name, expected_cmd in _CLI_FASTPATH_SURFACES.items():
        rendered = _render(template_name, _default_context())
        assert "CLI fast path (optional)" in rendered, template_name
        assert expected_cmd in rendered, template_name
        # The CLI is optional, so the note must point back to the manual steps.
        assert "fall back to the manual" in rendered, template_name


def test_iflow_capture_fast_path_mentions_sweep_and_capture() -> None:
    """/iflow-pick's fast path covers both the capture and the sweep shortcuts."""
    rendered = _render("commands/iflow-pick.md.j2", _default_context())
    assert "issue-flow agent capture" in rendered
    assert "issue-flow agent sweep --except" in rendered


def test_iflow_init_is_harness_cold_start_not_capture() -> None:
    """/iflow-setup guides issue-flow init; it must not own agent capture (#241)."""
    rendered = _render("commands/iflow-setup.md.j2", _default_context())
    assert "issue-flow init" in rendered
    assert "workspace bootstrap" in rendered
    assert "https://issue-flow.readthedocs.io/en/latest/how-to/workspaces/" in rendered
    assert "https://issue-flow.readthedocs.io/en/latest/how-to/for-agents/" in rendered
    assert "issue-flow agent capture" not in rendered
    assert "/iflow-pick" in rendered


def test_iflow_init_skill_points_at_workspace_howto() -> None:
    """Agents following /iflow-setup must see the same parent-folder recipe (#313)."""
    rendered = _render("skills/iflow_setup/SKILL.md.j2", _default_context())
    assert "https://issue-flow.readthedocs.io/en/latest/how-to/workspaces/" in rendered
    assert "https://issue-flow.readthedocs.io/en/latest/how-to/for-agents/" in rendered
    assert "uv tool upgrade issue-flow" in rendered
    assert "workspace bootstrap --yes --default" in rendered
    assert "workspace init --default" in rendered
    assert "workspace update" in rendered


def test_iflow_setup_points_at_capture_not_init() -> None:
    """After #241, /iflow-setup must send issue capture to /iflow-pick."""
    command = _render("commands/iflow-setup.md.j2", _default_context())
    skill = _render("skills/iflow_setup/SKILL.md.j2", _default_context())
    for rendered in (command, skill):
        assert (
            "that is `/iflow-pick`" in rendered or "is `/iflow-pick`" in rendered
        )
        assert (
            "Capturing a GitHub issue" not in rendered or "/iflow-pick" in rendered
        )
        assert "that is `/iflow-setup`" not in rendered
        assert "is `/iflow-setup`;" not in rendered


def test_issue_close_delegates_post_merge_cleanup_to_issue_cleanup() -> None:
    """/iflow-close no longer deletes branches; it points at /iflow-cleanup instead."""
    rendered = _render("commands/iflow-close.md.j2", _default_context())
    assert "/iflow-cleanup" in rendered
    assert "git pull --ff-only" in rendered
    # The destructive branch delete lives in /iflow-cleanup now, not /iflow-close.
    assert "git branch -d" not in rendered


def test_issue_cleanup_describes_post_merge_branch_cleanup() -> None:
    """The /iflow-cleanup command owns the post-merge branch cleanup logic."""
    rendered = _render("commands/iflow-cleanup.md.j2", _default_context())
    assert "git branch -d" in rendered
    assert "git pull --ff-only" in rendered
    assert "gh pr view" in rendered
    # Never -D automatically.
    assert (
        "-D" not in rendered or "Never use `-D`" in rendered or "Never `-D`" in rendered
    )
    assert "include GitHub" in rendered or "include github" in rendered
    assert "Phase B" in rendered
    assert "agent branches" in rendered
    assert "git push origin --delete" in rendered
    assert "--force" in rendered
    skill = _render("skills/iflow_cleanup/SKILL.md.j2", _default_context())
    assert "include github" in skill.lower()
    assert (
        "Second consolidated confirm" in skill or "second consolidated confirm" in skill
    )
    assert "issue-flow agent branches" in skill
    assert "default-sync" in skill
    assert "default-sync" in rendered


def test_worktree_start_does_not_require_home_ff() -> None:
    """Issue #303: worktree start may skip home ff-only when default-sync says so."""
    pick = _render("skills/iflow_pick/SKILL.md.j2", _default_context())
    shared = _render("skills/_worktree_start.md.j2", _default_context())
    for rendered in (pick, shared):
        assert "default-sync" in rendered
        assert "proceeds whether or not home is ff-able" in rendered
        assert "origin/<default>" in rendered
    cleanup = _render("skills/iflow_cleanup/SKILL.md.j2", _default_context())
    assert (
        "Never rebase default" in cleanup or "never rebase default" in cleanup.lower()
    )
    close = _render("skills/iflow_close/SKILL.md.j2", _default_context())
    assert "default_sync" in close or "default-sync" in close


def test_issue_start_requires_or_offers_plan() -> None:
    """/iflow-build should read the plan file and offer to run /iflow-plan when missing."""
    rendered = _render("commands/iflow-build.md.j2", _default_context())
    assert "issue<N>_plan.md" in rendered
    assert "/iflow-plan" in rendered


def test_iflow_plan_auto_graphify_on_plan_gated() -> None:
    """Issue #214: plan auto-runs graphify only when auto_graphify_on_plan is true."""
    off_cmd = _render("commands/iflow-plan.md.j2", _default_context())
    off_skill = _render("skills/iflow_plan/SKILL.md.j2", _default_context())
    assert "auto_graphify_on_plan = true" not in off_cmd
    assert "auto_graphify_on_plan = true" not in off_skill

    on_ctx = {**_default_context(), "auto_graphify_on_plan": True}
    on_cmd = _render("commands/iflow-plan.md.j2", on_ctx)
    on_skill = _render("skills/iflow_plan/SKILL.md.j2", on_ctx)
    assert "auto_graphify_on_plan = true" in on_cmd
    assert "issue-flow graphify -C <project_root>" in on_cmd
    assert "auto_graphify_on_plan = true" in on_skill
    assert on_cmd.count("issue-flow graphify -C <project_root>") == 1
    assert on_skill.count("issue-flow graphify -C <project_root>") == 1
    assert "Leave `extract` to the user" in on_skill


def test_hands_off_bakes_graphify_and_skips_confirms() -> None:
    """Issue #402: hands_off forces AST graphify and skips unattended confirms."""
    on = {
        **_default_context(),
        "hands_off": True,
        "auto_graphify_on_plan": False,
        "graphify_gitignored": False,
    }
    plan = _render("skills/iflow_plan/SKILL.md.j2", on)
    epic = _render("skills/iflow_issue/epic.md.j2", on)
    for rendered in (plan, epic):
        assert "issue-flow graphify -C <project_root>" in rendered
        assert "extract" not in rendered
        assert "auto_graphify_on_plan = true" not in rendered
    assert "before every plan" in plan
    assert "before the epic draft" in epic

    off_plan = _render("skills/iflow_plan/SKILL.md.j2", _default_context())
    off_epic = _render("skills/iflow_issue/epic.md.j2", _default_context())
    assert "hands_off` is on" not in off_plan
    assert "hands_off` is on" not in off_epic
    assert "issue-flow graphify -C <project_root>" not in off_plan

    drive = _render("skills/iflow_run/drive.md.j2", on)
    assert "No drive confirm" in drive
    assert "short description" in drive
    assert "records **accept**" in drive
    drive_off = _render("skills/iflow_run/drive.md.j2", _default_context())
    assert "Require `<N>`" in drive_off
    assert "**Drive confirm**" in drive_off
    assert "short description" not in drive_off
    assert "records **accept**" not in drive_off

    yolo = _render("skills/iflow_run/yolo.md.j2", on)
    assert "already authorized" in yolo
    yolo_off = _render("skills/iflow_run/yolo.md.j2", _default_context())
    assert "Single consolidated confirm" in yolo_off
    assert "Require an explicit yes" in yolo_off

    auto = _render("skills/iflow_run/auto.md.j2", on)
    assert "last_outcome: accepted" in auto
    assert "grant N more loops" not in auto
    auto_off = _render("skills/iflow_run/auto.md.j2", _default_context())
    assert "grant N more loops" in auto_off

    cycle = _render("skills/iflow_run/cycle.md.j2", on)
    assert "already authorized" in cycle
    cycle_off = _render("skills/iflow_run/cycle.md.j2", _default_context())
    assert "One consolidated confirm" in cycle_off
    assert "Explicit yes" in cycle_off or "explicit yes" in cycle_off


def test_issue_start_reads_prior_art_from_plan() -> None:
    """/iflow-build should remind the agent to read ### Prior art from the plan."""
    rendered = _render("commands/iflow-build.md.j2", _default_context())
    assert "### Prior art" in rendered
    skill = _render("skills/iflow_build/SKILL.md.j2", _default_context())
    assert "### Prior art" in skill


def test_issue_pause_moves_to_partly_solved() -> None:
    """/iflow-pause moves the issue group to the partly-solved folder."""
    rendered = _render("commands/iflow-pause.md.j2", _default_context())
    assert "02-partly-solved-issues" in rendered
    assert "Remaining work" in rendered
    assert "- [ ] Done" in rendered


def test_issue_yolo_has_safeguards() -> None:
    """/iflow-run yolo must advertise the up-front safeguards before chaining."""
    rendered = _render("commands/iflow-run yolo.md.j2", _default_context())
    assert "uv run pytest" in rendered
    assert "default branch" in rendered.lower()
    # Must not chain cleanup automatically.
    assert "/iflow-cleanup" in rendered


def test_issue_yolo_chains_hands_off_close() -> None:
    """/iflow-run yolo must forward the yolo token so close merges and pulls itself."""
    for template_name in (
        "commands/iflow-run yolo.md.j2",
        "skills/iflow_run/yolo.md.j2",
    ):
        rendered = _render(template_name, _default_context())
        assert "/iflow-close yolo" in rendered, template_name
        assert "gh pr merge --squash" in rendered, template_name
        assert "gh pr checks --watch" in rendered, template_name
        assert "15" in rendered, template_name


def test_issue_close_yolo_token_merges_and_pulls() -> None:
    """/iflow-close must document the hands-off `yolo` token behaviour."""
    for template_name in (
        "commands/iflow-close.md.j2",
        "skills/iflow_close/SKILL.md.j2",
    ):
        rendered = _render(template_name, _default_context())
        assert "`yolo`" in rendered, template_name
        assert "gh pr merge" in rendered, template_name
        assert "gh pr list" in rendered, template_name
        assert "gh pr checks" in rendered, template_name
        assert "--watch" in rendered, template_name
        assert "issue-flow agent pr-ready" in rendered, template_name
        assert "15" in rendered, template_name
        assert "--squash --auto" in rendered, template_name
        assert "last resort" in rendered.lower(), template_name
        # Branch deletion still belongs to /iflow-cleanup, never to close.
        assert "branch deletion stays in `/iflow-cleanup`" in rendered.lower(), (
            template_name
        )


def test_cleanup_bakes_include_github_default() -> None:
    """cleanup_include_github gates Phase B default wording in cleanup skill."""
    off = _render(
        "skills/iflow_cleanup/SKILL.md.j2",
        {**_default_context(), "cleanup_include_github": False},
    )
    assert "Phase B runs too" not in off
    assert "no github" in off
    on = _render(
        "skills/iflow_cleanup/SKILL.md.j2",
        {**_default_context(), "cleanup_include_github": True},
    )
    assert "cleanup_include_github = true" in on
    assert "Phase B runs too" in on


def test_cleanup_bakes_on_bleeding_edge() -> None:
    """on_bleeding_edge gates self-update default wording in cleanup skill."""
    off = _render(
        "skills/iflow_cleanup/SKILL.md.j2",
        {**_default_context(), "on_bleeding_edge": False},
    )
    assert "issue-flow agent self-update" in off
    assert "on_bleeding_edge = true" not in off
    on = _render(
        "skills/iflow_cleanup/SKILL.md.j2",
        {**_default_context(), "on_bleeding_edge": True},
    )
    assert "on_bleeding_edge = true" in on
    assert "issue-flow agent self-update" in on
    cmd_on = _render(
        "commands/iflow-cleanup.md.j2",
        {**_default_context(), "on_bleeding_edge": True},
    )
    assert "on_bleeding_edge = true" in cmd_on
    assert "issue-flow agent self-update" in cmd_on


def test_iflow_dispatcher_epic_gap_contract() -> None:
    """Issue #210: /iflow skill+command mention epic_hint / next_candidates."""
    for template_name in (
        "skills/iflow_iflow/SKILL.md.j2",
        "commands/iflow.md.j2",
    ):
        rendered = _render(template_name, _default_context())
        assert "epic_hint" in rendered, template_name
        assert "next_candidates" in rendered, template_name
        assert "no silent pick" in rendered.lower(), template_name
        assert "Dispatch only to the four targets above" in rendered
        assert "/iflow-pick" in rendered, template_name
        assert "epic_session" in rendered, template_name
        assert "one-and-ask" in rendered, template_name
        assert "the user chooses the candidate every time" in rendered.lower(), template_name


def test_cycle_bakes_max_issues() -> None:
    rendered = _render(
        "skills/iflow_run/cycle.md.j2",
        {**_default_context(), "cycle_max_issues": 20},
    )
    assert "longer than **20**" in rendered
    assert "default 20" in rendered


def test_cycle_non_yolo_lane_bakes_policy() -> None:
    """#386: yolo:no issues run on a non-yolo lane; the merge policy is baked."""
    skill = _render(
        "skills/iflow_run/cycle.md.j2",
        {**_default_context(), "cycle_nonyolo": "pr-only"},
    )
    assert "## Lanes — yolo vs non-yolo" in skill
    assert "**`nonyolo:merge`** / **`nonyolo:pr-only`** / **`nonyolo:stop`**" in skill
    assert "Default from config **`pr-only`**" in skill
    assert (
        "**not** a stop condition by itself unless the policy is `nonyolo:stop`"
        in skill
    )
    assert "**already merged**" in skill
    assert "`nonyolo` policy" in skill  # cycle_status.md records it
    cmd = _render(
        "commands/iflow-run cycle.md.j2",
        {**_default_context(), "cycle_nonyolo": "pr-only"},
    )
    assert "non-yolo lane" in cmd
    assert "Default from config **`pr-only`**" in cmd


def test_drive_and_auto_forward_nonyolo_and_never_stop_on_yolo_no() -> None:
    ctx = {**_default_context(), "cycle_nonyolo": "merge"}
    for template in (
        "skills/iflow_run/drive.md.j2",
        "commands/iflow-run drive.md.j2",
        "skills/iflow_run/auto.md.j2",
        "commands/iflow-run auto.md.j2",
    ):
        rendered = _render(template, ctx)
        assert "nonyolo:" in rendered, template
        assert "`yolo: no`" in rendered, template
        assert "not a stop" in rendered.lower(), template
    drive = _render("skills/iflow_run/drive.md.j2", ctx)
    # Constraint is scoped to the default branch; issue branches may be
    # rebased + force-with-lease pushed by sync-branch.
    assert "Never rebase / force-push / push the **default branch**" in drive
    assert "--force-with-lease" in drive
    assert "**already merged**" in drive
    assert "`--base <parent>`" in drive


def test_cleanup_documents_orchestrator_token() -> None:
    ctx = _default_context()
    skill = _render("skills/iflow_cleanup/SKILL.md.j2", ctx)
    assert "Orchestrator token" in skill
    assert "never `unique_work` / `skipped`" in skill
    assert "`drive` / `landed`" in skill


def test_iflow_dispatcher_warns_on_version_drift() -> None:
    ctx = _default_context()
    skill = _render("skills/iflow_iflow/SKILL.md.j2", ctx)
    assert "`version_drift`" in skill
    assert "**Version drift.**" in skill
    assert "Leave running `issue-flow update` to the user" in skill
    cmd = _render("commands/iflow.md.j2", ctx)
    assert "`version_drift`" in cmd


def test_rules_body_checks_graph_json_before_graphify_query() -> None:
    body = _render("rules/_body.md.j2", _default_context())
    assert "graphify-out/graph.json" in body
    assert "`graphify query`" in body


def test_start_auto_close_chains_into_close() -> None:
    off = _render("skills/iflow_build/SKILL.md.j2", _default_context())
    assert "tell the user to run `/iflow-close`" in off
    on = _render(
        "skills/iflow_build/SKILL.md.j2",
        {**_default_context(), "auto_close": True},
    )
    assert "follow" in on and "iflow-close/SKILL.md" in on
    assert "tell the user to run `/iflow-close`" not in on


def test_pick_auto_plan_chains_into_plan() -> None:
    """Issue #219: pick Phase 3 chains to plan when auto_plan is true."""
    off = _render(
        "skills/iflow_pick/SKILL.md.j2",
        {**_default_context(), "auto_plan": False},
    )
    assert "Ask** whether to continue with `/iflow-plan`" in off
    assert "auto_plan = true" not in off
    on = _render("skills/iflow_pick/SKILL.md.j2", _default_context())
    assert "auto_plan = true" in on
    assert "noplan" in on
    assert "Ask** whether to continue with `/iflow-plan`" not in on
    cmd_on = _render("commands/iflow-pick.md.j2", _default_context())
    assert "auto_plan = true" in cmd_on
    assert "`noplan`" in cmd_on


def test_plan_auto_build_chains_into_build() -> None:
    """Issue #219: plan Accept chains to build when auto_build is true."""
    off = _render(
        "skills/iflow_plan/SKILL.md.j2",
        {**_default_context(), "auto_build": False},
    )
    assert "Tell the user to run `/iflow-build`" in off or (
        "Do **not** proceed to implementation from this skill" in off
    )
    assert "auto_build chained" not in off
    on = _render("skills/iflow_plan/SKILL.md.j2", _default_context())
    assert "auto_build" in on and "nobuild" in on
    assert "iflow-build" in on
    assert "chained the handoff" in on
    cmd_on = _render("commands/iflow-plan.md.j2", _default_context())
    assert "`nobuild`" in cmd_on
    assert "auto_build chained" in cmd_on or "auto_build` chained" in cmd_on


def test_essential_tests_hooks_gated_by_knob() -> None:
    """Essential-tests wording appears only when essential_tests is true."""
    off_close = _render("skills/iflow_close/SKILL.md.j2", _default_context())
    assert "Essential tests:" not in off_close
    assert "Essential tests review" not in off_close
    off_doctor = _render("skills/iflow_status/doctor.md.j2", _default_context())
    assert "Essential tests audit" not in off_doctor

    on_ctx = {
        **_default_context(),
        "essential_tests": True,
        "test_runner": "pytest",
        "essential_marker": "smoke",
        "essential_review": "close",
    }
    on_close = _render("skills/iflow_close/SKILL.md.j2", on_ctx)
    assert "pytest -m smoke" in on_close
    assert "Essential tests review" in on_close
    assert "@pytest.mark.smoke" in on_close

    build_both = _render(
        "skills/iflow_build/SKILL.md.j2",
        {**on_ctx, "essential_review": "both"},
    )
    assert "Essential tests" in build_both
    assert "@pytest.mark.smoke" in build_both

    build_close_only = _render(
        "skills/iflow_build/SKILL.md.j2",
        on_ctx,
    )
    assert "Essential tests review" not in build_close_only

    doctor = _render("skills/iflow_status/doctor.md.j2", on_ctx)
    assert "Essential tests audit" in doctor
    assert "test-registry.md" in doctor

    unsupported = _render(
        "skills/iflow_close/SKILL.md.j2",
        {**on_ctx, "test_runner": "nose"},
    )
    assert (
        "not supported" in unsupported.lower() or "unsupported" in unsupported.lower()
    )

    guide = _render("designs/essential-tests.md.j2", on_ctx)
    assert "smoke" in guide
    assert "pytest" in guide
    registry = _render("designs/test-registry.md.j2", on_ctx)
    assert "Essential?" in registry


def test_build_early_pr_step_and_tokens() -> None:
    """Build always documents early-PR tokens; baked early_pr appears in text."""
    off = _render("skills/iflow_build/SKILL.md.j2", _default_context())
    assert "Early PR tokens" in off
    assert "`early`" in off and "`noearly`" in off
    assert "gh pr create --draft" in off
    assert "Refs #N" in off
    assert "currently **False**" in off or "currently **false**" in off
    on = _render(
        "skills/iflow_build/SKILL.md.j2",
        {**_default_context(), "early_pr": True},
    )
    assert "currently **True**" in on or "currently **true**" in on
    cmd = _render("commands/iflow-build.md.j2", _default_context())
    assert "Early pull request (optional)" in cmd
    assert "gh pr list" in cmd


def test_close_documents_publish_on_success_label() -> None:
    ctx = {**_default_context(), "publish_label": "ship-it"}
    close = _render("skills/iflow_close/SKILL.md.j2", ctx)
    assert "Publish-on-success label" in close
    assert "publish-intent" in close
    assert "`ship-it`" in close
    assert "gh release create" in close
    cleanup = _render("skills/iflow_cleanup/SKILL.md.j2", ctx)
    assert "publish label" in cleanup.lower()
    assert "gh release create" in cleanup


def test_history_confirm_changelog_update_gate() -> None:
    on = _render(
        "skills/iflow_close/changelog.md.j2",
        {**_default_context(), "confirm_changelog_update": True},
    )
    assert "confirm once before writing" in on
    assert "**stop**" in on
    assert "nohistory" in on
    off = _render(
        "skills/iflow_close/changelog.md.j2",
        {**_default_context(), "confirm_changelog_update": False},
    )
    assert "without a confirm prompt" in off
    assert "confirm once before writing" not in off


def test_issue_close_bakes_checks_watch_minutes_override() -> None:
    """checks_watch_minutes from context is baked into close surfaces."""
    context = {**_default_context(), "checks_watch_minutes": 30}
    for template_name in (
        "commands/iflow-close.md.j2",
        "skills/iflow_close/SKILL.md.j2",
    ):
        rendered = _render(template_name, context)
        assert "30" in rendered, template_name


def test_issue_pick_routes_yolo_label_when_label_flows_on() -> None:
    """/iflow-pick surfaces the label-driven yolo routing when label_flows is on."""
    context = {**_default_context(), "label_flows": True, "yolo_label": "fast-track"}
    for template_name in (
        "commands/iflow-pick.md.j2",
        "skills/iflow_pick/SKILL.md.j2",
    ):
        rendered = _render(template_name, context)
        assert "fast-track" in rendered, template_name
        assert "iflow-run yolo" in rendered, template_name


def test_issue_pick_routes_ops_label_when_label_flows_on() -> None:
    """/iflow-pick surfaces the label-driven ops routing when label_flows is on."""
    context = {**_default_context(), "label_flows": True, "ops_label": "no-pr"}
    for template_name in (
        "commands/iflow-pick.md.j2",
        "skills/iflow_pick/SKILL.md.j2",
    ):
        rendered = _render(template_name, context)
        assert "`no-pr` label" in rendered, template_name
        assert "ops.md" in rendered, template_name
        assert "close ops" in rendered, template_name


def test_issue_close_documents_ops_token() -> None:
    """/iflow-close documents the ops / no-PR token and path."""
    for template_name in (
        "commands/iflow-close.md.j2",
        "skills/iflow_close/SKILL.md.j2",
    ):
        rendered = _render(template_name, _default_context())
        assert "ops" in rendered.lower(), template_name
        assert "Ops close path" in rendered or "no-PR close" in rendered, template_name
        assert "nopr" in rendered, template_name


def test_issue_pick_omits_label_routing_when_label_flows_off() -> None:
    """With label_flows off, /iflow-pick renders no label-driven routing text."""
    context = {**_default_context(), "label_flows": False, "yolo_label": "yolo"}
    for template_name in (
        "commands/iflow-pick.md.j2",
        "skills/iflow_pick/SKILL.md.j2",
    ):
        rendered = _render(template_name, context)
        assert "Label-driven yolo flow" not in rendered, template_name
        assert "Label-driven ops flow" not in rendered, template_name


def test_issue_fix_describes_interactive_session() -> None:
    """/iflow-issue fix must describe the off-path interactive iterative-fix session."""
    rendered = _render("commands/iflow-issue fix.md.j2", _default_context())
    # Off-path and explicitly not driven by /iflow during a session.
    assert "/iflow" in rendered
    # Always creates a GitHub issue via gh; GitLab is out of scope.
    assert "gh issue create" in rendered
    assert "GitLab is not supported" in rendered
    # The fix loop records each fix in the status file's log section.
    assert "Iterative fixes log" in rendered
    assert "issue<N>_status.md" in rendered
    # Branch-from-current-vs-default choice and delegation to capture/close.
    assert "/iflow-pick" in rendered
    assert "/iflow-close" in rendered
    # Keeps the unchecked Done checkbox during the session.
    assert "- [ ] Done" in rendered


def test_issue_fix_auto_name_knob() -> None:
    """fix_auto_name bakes agent-names vs ask-once naming into /iflow-issue fix."""
    off = _render("commands/iflow-issue fix.md.j2", _default_context())
    assert "fix_auto_name = false" in off
    assert "ask once" in off.lower()

    on = _render(
        "commands/iflow-issue fix.md.j2",
        {**_default_context(), "fix_auto_name": True},
    )
    assert "fix_auto_name = true" in on
    assert "Do **not** ask the user to approve or rename" in on
    skill_on = _render(
        "skills/iflow_issue/fix.md.j2",
        {**_default_context(), "fix_auto_name": True},
    )
    assert "fix_auto_name = true" in skill_on
    assert "Naming itself is not a separate confirm" in skill_on


def test_iflow_archive_command_documents_gated_deletion() -> None:
    """/iflow-cleanup archive must describe the summary file, recovery ref, and gating."""
    rendered = _render("commands/iflow-cleanup archive.md.j2", _default_context())
    # Dated summary file in the solved folder.
    assert "_archived_issues.md" in rendered
    assert "03-solved-issues" in rendered
    # Recovery relies on the recorded pre-archive git ref.
    assert "git rev-parse HEAD" in rendered
    assert "git show <ref>:<path>" in rendered
    # Destructive and gated: clean tree + one consolidated confirm.
    assert "clean working tree" in rendered
    assert "Consolidated confirm" in rendered
    # Off-path: never auto-dispatched.
    # Selection inputs.
    assert "keep <K>" in rendered
    assert "all" in rendered


def test_iflow_issue_describes_normal_issue_create() -> None:
    """/iflow-issue must describe confirm-gated create + optional init handoff."""
    rendered = _render("commands/iflow-issue.md.j2", _default_context())
    assert "gh issue create" in rendered
    assert "GitLab is not supported" in rendered
    assert "Problem / context" in rendered
    assert "Acceptance criteria" in rendered
    assert "/iflow-pick" in rendered
    assert "/iflow-plan" in rendered
    assert "epic" in rendered.lower()


def test_iflow_issue_skill_mirrors_command() -> None:
    """The iflow-issue skill must carry the same flow and frontmatter."""
    rendered = _render("skills/iflow_issue/SKILL.md.j2", _default_context())
    assert "name: iflow-issue" in rendered
    assert "disable-model-invocation: true" in rendered
    assert "gh issue create" in rendered
    assert "/iflow-pick" in rendered
    assert "/iflow-plan" in rendered
    assert "Acceptance criteria" in rendered


def test_issue_create_skills_use_body_file_not_bash_heredoc() -> None:
    """Multi-line gh bodies must name --body-file and the PowerShell failure."""
    for name in (
        "skills/iflow_issue/SKILL.md.j2",
        "commands/iflow-issue.md.j2",
        "skills/iflow_issue/fix.md.j2",
        "skills/iflow_close/SKILL.md.j2",
    ):
        rendered = _render(name, _default_context())
        assert "--body-file" in rendered, name
        assert "PowerShell" in rendered, name
        assert "<<'EOF'" in rendered, name


def test_iflow_lists_issue_as_off_path() -> None:
    """/iflow and its skill must list /iflow-issue among the explicit-only commands."""
    cmd = _render("commands/iflow.md.j2", _default_context())
    skill = _render("skills/iflow_iflow/SKILL.md.j2", _default_context())
    assert "/iflow-issue" in cmd
    assert "/iflow-issue" in skill


def test_iflow_split_describes_confirm_and_rest_recipe() -> None:
    """/iflow-issue split must describe confirm-gated create + native sub-issue link."""
    rendered = _render("commands/iflow-issue split.md.j2", _default_context())
    assert "gh issue create" in rendered
    assert "sub-issue-add" in rendered
    assert "sub_issue_id" in rendered
    assert "--input" in rendered
    assert "422" in rendered
    assert "Sub-issue of #" in rendered
    assert "GitLab is not supported" in rendered
    assert "/iflow-issue epic" in rendered


def test_iflow_issue_offers_split_for_over_large() -> None:
    """/iflow-issue over-large path offers split or epic, never auto-creates."""
    cmd = _render("commands/iflow-issue.md.j2", _default_context())
    skill = _render("skills/iflow_issue/SKILL.md.j2", _default_context())
    for rendered in (cmd, skill):
        assert "/iflow-issue split" in rendered
        assert (
            "do **not** auto-create" in rendered.lower()
            or "do not auto-create" in rendered.lower()
        )


def test_iflow_plan_scope_check_offers_split() -> None:
    """/iflow-plan scope check points at /iflow-issue split."""
    cmd = _render("commands/iflow-plan.md.j2", _default_context())
    skill = _render("skills/iflow_plan/SKILL.md.j2", _default_context())
    assert "/iflow-issue split" in cmd
    assert "/iflow-issue split" in skill


def test_iflow_review_command_documents_kinds_and_cli() -> None:
    """/iflow-issue review must describe kinds, confirm gate, and CLI helpers."""
    rendered = _render("commands/iflow-issue review.md.j2", _default_context())
    assert "label-candidates" in rendered
    assert "label-apply" in rendered
    assert "yolo" in rendered
    assert "Consolidated confirm" in rendered or "consolidated confirm" in rendered
    assert "gh label create" in rendered


def test_iflow_epic_documents_goal_and_model_markers() -> None:
    """Epic skill/command must document Stage/issue Goal and Model markers (#193)."""
    skill = _render("skills/iflow_issue/epic.md.j2", _default_context())
    cmd = _render("commands/iflow-issue epic.md.j2", _default_context())
    for rendered in (skill, cmd):
        assert "- Goal:" in rendered
        assert "Model:" in rendered
        assert "deep" in rendered and "fast" in rendered and "default" in rendered
    assert (
        "Copied into the GitHub issue body" in skill or "copied into" in skill.lower()
    )


def test_iflow_describes_state_machine() -> None:
    """/iflow must describe the four-state dispatch and name its downstream targets."""
    rendered = _render("commands/iflow.md.j2", _default_context())
    # Dispatches into all four linear-flow commands.
    for target in (
        "/iflow-pick",
        "/iflow-plan",
        "/iflow-build",
        "/iflow-close",
    ):
        assert target in rendered, f"/iflow must mention {target}"
    # State keywords from the dispatch table.
    assert "_original.md" in rendered
    assert "_plan.md" in rendered
    assert "- [x] Done" in rendered
    # Off-path commands are explicitly not auto-dispatched.
    assert "/iflow-pause" in rendered
    assert "/iflow-cleanup" in rendered
    assert "/iflow-run yolo" in rendered


def test_iflow_treats_branch_derived_n_as_authoritative() -> None:
    """/iflow's step 0 must treat a branch-derived N as authoritative.

    The branch-derived N should win even when `issue<N>_*` files don't exist
    yet, or when unrelated groups sit in 01-current-issues. It should also
    trigger the archived-issue guard warning when the group lives in
    02-partly-solved or 03-solved.
    """
    rendered = _render("commands/iflow.md.j2", _default_context())
    assert "authoritative" in rendered.lower()
    # Both archive folders are consulted for the archived-issue guard warning.
    assert "02-partly-solved-issues" in rendered
    assert "03-solved-issues" in rendered
    assert "archived-issue guard" in rendered.lower()


def test_issue_pick_skill_mirrors_command() -> None:
    """The issue-pick skill must carry the same front-door flow and frontmatter."""
    rendered = _render("skills/iflow_pick/SKILL.md.j2", _default_context())
    assert "name: iflow-pick" in rendered
    assert "disable-model-invocation: true" in rendered
    assert "Phase 1" in rendered
    assert "Phase 2" in rendered
    assert "Phase 3" in rendered
    assert "/iflow-pick" in rendered
    assert "/iflow-plan" in rendered


def test_iflow_does_not_auto_dispatch_issue_pick() -> None:
    """/iflow must list /iflow-pick among the explicit-only, never-auto-dispatched commands."""
    cmd = _render("commands/iflow.md.j2", _default_context())
    skill = _render("skills/iflow_iflow/SKILL.md.j2", _default_context())
    assert "/iflow-pick" in cmd
    assert "/iflow-pick" in skill


def test_issue_init_mentions_branch_preflight_and_archive_guard() -> None:
    """The /iflow-pick command must include the preflight and archived-issue guard."""
    rendered = _render("commands/iflow-pick.md.j2", _default_context())
    assert "Branch status preflight" in rendered
    assert "Archived-issue guard" in rendered or "archived" in rendered.lower()


def test_lifecycle_skills_include_resolve_partial() -> None:
    """Lifecycle skills must document multi-root project-root resolution."""
    stems = (
        "iflow_setup",
        "iflow_close",
        "iflow_cleanup",
        "iflow_pick",
        "iflow_status",
        "iflow_iflow",
        "iflow_build",
        "iflow_plan",
        "iflow_pause",
        "iflow_run",
        "iflow_issue",
    )
    for stem in stems:
        rendered = _render(f"skills/{stem}/SKILL.md.j2", _default_context())
        assert "issue-flow agent resolve" in rendered, stem
        assert "Resolve the project root first" in rendered, stem


def test_iflow_plan_skill_documents_slashless_invoke_line() -> None:
    """Lifecycle skills should recommend `iflow plan` before slash form."""
    rendered = _render("skills/iflow_plan/SKILL.md.j2", _default_context())
    assert "**Invoke:**" in rendered
    assert "type `iflow plan` in chat" in rendered
    assert "/iflow-plan" in rendered


def test_history_update_skill_documents_both_modes() -> None:
    """The history-update skill emits trailers and does not edit the changelog file."""
    rendered = _render(
        "skills/iflow_close/changelog.md.j2", _default_context()
    )
    assert "HISTORY.md" in rendered
    assert "Changelog-Id" in rendered
    assert "[Unreleased]" in rendered
    assert "do not" in rendered.lower() and "edit" in rendered.lower()
    # Keep-both still documents the leftover [Unreleased] repair.
    assert "append" in rendered.lower()
    assert "promote" in rendered.lower()
    assert "skip" in rendered.lower()
    assert "Never create" in rendered or "never create" in rendered.lower()


def test_history_update_skill_respects_history_file_override() -> None:
    """The history-update skill should reference {{ history_file }} so custom filenames work."""
    context = _default_context()
    context["history_file"] = "CHANGELOG.md"
    rendered = _render("skills/iflow_close/changelog.md.j2", context)
    assert "CHANGELOG.md" in rendered
    # No leftover Jinja placeholder.
    assert "{{ history_file }}" not in rendered


def test_caveman_skill_renders_full_mode_english_only() -> None:
    """The caveman skill ships as a model-invocable, full-mode-only behavior skill."""
    rendered = _render("skills/caveman/SKILL.md.j2", _default_context())
    assert "name: caveman" in rendered
    # Model-invocable (unlike workflow skills): the user opts in at runtime.
    assert "disable-model-invocation: true" not in rendered
    # Off switches and single full intensity, English only.
    assert "stop caveman" in rendered
    assert "normal mode" in rendered
    assert "English only" in rendered
    assert "Single level: **full**" in rendered


def test_caveman_in_standard_manifest_as_skills_caveman() -> None:
    """Standard scaffolding emits the caveman skill at skills/caveman/SKILL.md."""
    template_names = {name for name, _ in TEMPLATE_MANIFEST}
    assert "skills/caveman/SKILL.md.j2" in template_names
    assert "{agent_dir}/skills/caveman/SKILL.md" in {
        path for _, path in TEMPLATE_MANIFEST
    }


def test_grill_me_skill_renders_as_planning_interview() -> None:
    """The grill-me skill ships as a model-invocable planning-interview skill."""
    rendered = _render("skills/grill_me/SKILL.md.j2", _default_context())
    assert "name: grill-me" in rendered
    # Model-invocable (unlike workflow skills): the user opts in at runtime.
    assert "disable-model-invocation: true" not in rendered
    # Off switches and the core grilling discipline.
    assert "stop grilling" in rendered
    assert "normal mode" in rendered
    assert "One question at a time" in rendered


def test_grill_me_in_standard_manifest_as_skills_grill_me() -> None:
    """Standard scaffolding emits the grill-me skill at skills/grill-me/SKILL.md."""
    template_names = {name for name, _ in TEMPLATE_MANIFEST}
    assert "skills/grill_me/SKILL.md.j2" in template_names
    assert "{agent_dir}/skills/grill-me/SKILL.md" in {
        path for _, path in TEMPLATE_MANIFEST
    }


def test_gh_ci_in_standard_manifest_as_skills_gh_ci() -> None:
    """Standard scaffolding emits the gh-ci skill at skills/iflow-close/ci.md."""
    assert "iflow_close" in SKILL_DIRS
    template_names = {name for name, _ in TEMPLATE_MANIFEST}
    assert "skills/iflow_close/ci.md.j2" in template_names
    assert "{agent_dir}/skills/iflow-close/ci.md" in {
        path for _, path in TEMPLATE_MANIFEST
    }


def test_iflow_plan_skill_includes_reasoning_directive() -> None:
    ctx = enrich_render_context(_default_context(), "skills/iflow_plan/SKILL.md.j2")
    rendered = _render("skills/iflow_plan/SKILL.md.j2", ctx)
    assert "### MODEL & EXECUTION DIRECTIVE" in rendered
    assert "Profile: reasoning" in rendered


def test_step_directives_off_omits_directive_block() -> None:
    ctx = enrich_render_context(_default_context(), "skills/iflow_plan/SKILL.md.j2")
    ctx["step_directives"] = False
    rendered = _render("skills/iflow_plan/SKILL.md.j2", ctx)
    assert "MODEL & EXECUTION DIRECTIVE" not in rendered


def test_iflow_pick_includes_model_label_block_when_enabled() -> None:
    ctx = _default_context()
    ctx["model_label_flows"] = True
    ctx = enrich_render_context(ctx, "skills/iflow_pick/SKILL.md.j2")
    rendered = _render("skills/iflow_pick/SKILL.md.j2", ctx)
    assert "**Model label.**" in rendered
    assert "`deep` → announce the **reasoning** profile" in rendered


def test_is_skill_template_matches_skill_manifest_paths() -> None:
    assert is_skill_template("skills/iflow_setup/SKILL.md.j2")
    assert is_skill_template("skills/caveman/SKILL.md.j2")
    assert not is_skill_template("commands/iflow-setup.md.j2")
    assert not is_skill_template("skills/_model_directive.md.j2")


def test_stamp_skill_version_injects_frontmatter_key() -> None:
    content = "---\nname: demo\ndescription: test\n---\n\n# Body\n"
    stamped = stamp_skill_version(content, "1.2.3")
    assert "issue-flow-version: 1.2.3" in stamped
    assert stamped.startswith("---\nname: demo")


def test_stamp_skill_version_refreshes_existing_key() -> None:
    content = "---\nname: demo\nissue-flow-version: 0.1.0\n---\n\n# Body\n"
    stamped = stamp_skill_version(content, "0.2.0")
    assert stamped.count("issue-flow-version:") == 1
    assert "issue-flow-version: 0.2.0" in stamped
    assert "issue-flow-version: 0.1.0" not in stamped


def test_render_template_stamps_skill_outputs() -> None:
    rendered = _render("skills/iflow_pick/capture.md.j2", _default_context())
    assert f"issue-flow-version: {ISSUE_FLOW_VERSION}" in rendered


# ---------------------------------------------------------------------------
# Vendored pstack skills (issue #249)
# ---------------------------------------------------------------------------

_BASE_CONTEXT = {
    "issue_flow_version": ISSUE_FLOW_VERSION,
    "issueflows_dir": ".issueflows",
    "agent_dir": ".cursor",
    "docs_dir": "docs",
    "history_file": "HISTORY.md",
    "tools_folder": "00-tools",
    "current_issues_folder": "01-current-issues",
    "partly_solved_folder": "02-partly-solved-issues",
    "solved_folder": "03-solved-issues",
    "designs_folder": "04-designs-and-guides",
    "epics_folder": "05-epics",
    "project_name": "test-project",
    "editor": "cursor",
    "editor_name": "Cursor",
    "commands_dir": "commands",
    "commands_supported": False,
    "graphify_installer": "cursor",
    "skill_level": "standard",
}


def _pstack_mode(names: list[str]):
    from issue_flow.modes import resolve_mode

    return resolve_mode("standard", pstack_skills=names)


def test_pstack_stems_are_optional_not_default() -> None:
    assert len(PSTACK_SKILL_NAMES) == 9
    for name in PSTACK_SKILL_NAMES:
        stem = PSTACK_NAME_TO_STEM[name]
        assert stem in SKILL_DIRS
        assert stem not in DEFAULT_SKILL_DIRS
        assert stem.startswith("pstack_")
    assert PSTACK_NAME_TO_STEM["blast-radius"] == "pstack_blast_radius"


def test_packaged_skill_output_names_cover_aliases_and_pstack() -> None:
    names = packaged_skill_output_names()
    assert "iflow-plan" in names
    assert "iflow" in names
    assert "iflow-iflow" not in names
    assert "unslop" in names
    assert "pstack_unslop" not in names
    assert len(names) == len(SKILL_DIRS)


def test_default_manifest_has_no_pstack_entries() -> None:
    template_names = {name for name, _ in TEMPLATE_MANIFEST}
    assert not any("/pstack_" in name for name in template_names)
    for profile in EDITORS.values():
        for name, _ in build_manifest(profile):
            assert "/pstack_" not in name


def test_manifest_emits_pstack_skills_under_upstream_folder_names() -> None:
    mode = _pstack_mode(["unslop", "blast-radius"])
    for profile in EDITORS.values():
        manifest = build_manifest(profile, mode=mode)
        assert (
            "skills/pstack_unslop/SKILL.md.j2",
            "{agent_dir}/skills/unslop/SKILL.md",
        ) in manifest
        assert (
            "skills/pstack_blast_radius/SKILL.md.j2",
            "{agent_dir}/skills/blast-radius/SKILL.md",
        ) in manifest
        assert not any("/pstack_tdd/" in name for name, _ in manifest)
        # Default surface is still there alongside.
        assert any(name == "skills/iflow_plan/SKILL.md.j2" for name, _ in manifest)
    canonical = build_canonical_manifest(mode=mode)
    assert (
        "skills/pstack_unslop/SKILL.md.j2",
        "{issueflows_dir}/agent/skills/unslop/SKILL.md",
    ) in canonical


def test_every_pstack_template_renders_verbatim_with_provenance() -> None:
    context = {**_BASE_CONTEXT, **_MODE_CONTEXT}
    for name in PSTACK_SKILL_NAMES:
        stem = PSTACK_NAME_TO_STEM[name]
        rendered = _render(f"skills/{stem}/SKILL.md.j2", context)
        assert rendered.startswith("---\n")
        assert f"\nname: {name}\n" in rendered
        assert "disable-model-invocation: true" in rendered
        assert f"issue-flow-version: {ISSUE_FLOW_VERSION}" in rendered
        assert "vendored verbatim from cursor/plugins pstack v" in rendered
        # Jinja never touched the body.
        assert "{% raw %}" not in rendered
        assert "{% endraw %}" not in rendered
        assert "{{" not in rendered.split("-->", 1)[1] or "{{" in rendered


def test_pstack_license_ships_with_templates() -> None:
    from importlib import resources

    text = (
        resources.files("issue_flow.templates.skills")
        .joinpath("_pstack_LICENSE.txt")
        .read_text(encoding="utf-8")
    )
    assert text.startswith("MIT License")
    assert "Lauren Tan" in text


def test_noob_stem_for_template() -> None:
    assert noob_stem_for_template("skills/iflow_plan/SKILL.md.j2") == "plan"
    assert noob_stem_for_template("commands/iflow-plan.md.j2") == "plan"
    assert noob_stem_for_template("commands/iflow.md.j2") == "iflow"
    assert noob_stem_for_template("skills/iflow_pick/comments.md.j2") is None
    assert noob_stem_for_template("skills/caveman/SKILL.md.j2") is None


def test_noob_footer_omitted_by_default() -> None:
    ctx = {**_BASE_CONTEXT, **_MODE_CONTEXT}
    rendered = _render(
        "skills/iflow_plan/SKILL.md.j2",
        enrich_render_context(ctx, "skills/iflow_plan/SKILL.md.j2"),
    )
    assert "NEXT (noob)" not in rendered


def test_worktree_first_default_renders_worktree_add() -> None:
    ctx = {**_BASE_CONTEXT, **_MODE_CONTEXT}
    pick = _render(
        "skills/iflow_pick/SKILL.md.j2",
        enrich_render_context(ctx, "skills/iflow_pick/SKILL.md.j2"),
    )
    assert "worktree-add" in pick
    assert "Worktree-first start" in pick
    assert "worktree_first = false" not in pick
    cmd = _render(
        "commands/iflow-pick.md.j2",
        enrich_render_context(ctx, "commands/iflow-pick.md.j2"),
    )
    assert "worktree-add" in cmd


def test_worktree_first_false_renders_inplace_start() -> None:
    ctx = {**_BASE_CONTEXT, **_MODE_CONTEXT, "worktree_first": False}
    pick = _render(
        "skills/iflow_pick/SKILL.md.j2",
        enrich_render_context(ctx, "skills/iflow_pick/SKILL.md.j2"),
    )
    assert "Inplace start" in pick
    assert "git switch -c" in pick
    assert "Token `worktree`" in pick
    assert "Worktree-first start" not in pick
    cmd = _render(
        "commands/iflow-pick.md.j2",
        enrich_render_context(ctx, "commands/iflow-pick.md.j2"),
    )
    assert "git switch -c" in cmd
    assert "Token `worktree`" in cmd
