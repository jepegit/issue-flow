"""Tests for issue_flow.templating."""

from __future__ import annotations

from pathlib import Path

from issue_flow import __version__ as ISSUE_FLOW_VERSION
from issue_flow.editors import EDITORS, get_profile
from issue_flow.step_profiles import PACKAGED_DEFAULTS, enrich_render_context
from issue_flow.templating import (
    COMMAND_NAMES,
    SKILL_DIRS,
    TEMPLATE_MANIFEST,
    build_manifest,
    is_skill_template,
    render_template,
    resolve_output_path,
    stamp_skill_version,
)

_ALL_SKILLS = sorted(SKILL_DIRS)
_ALL_COMMANDS = sorted(COMMAND_NAMES)
_MODE_CONTEXT = {
    "mode": "standard",
    "mode_name": "Standard",
    "included_skills": _ALL_SKILLS,
    "included_commands": _ALL_COMMANDS,
    "caveman_default": False,
    "grill_me_default": False,
    "label_flows": True,
    "yolo_label": "yolo",
    "checks_watch_minutes": 15,
    "step_directives": True,
    "model_label_flows": False,
    "deep_model_label": "deep",
    "fast_model_label": "fast",
    "step_profiles": dict(PACKAGED_DEFAULTS),
    "remind_cleanup": True,
    "suggest_graphify": True,
    "auto_switchback": True,
    "pr_merge_method": "squash",
    "cycle_max_issues": 10,
    "auto_adversarial_loops": 2,
    "confirm_version_bump": False,
    "ruff_autofix": True,
    "auto_close": False,
    "early_pr": False,
    "confirm_changelog_update": True,
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
        result = render_template(template_name, ctx)
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
    rendered = render_template("commands/iflow-init.md.j2", context)
    assert "CUSTOM_DIR/01-current-issues" in rendered
    assert "{{ issueflows_dir }}" not in rendered


def test_project_brief_template_renders() -> None:
    """The durable project brief starter template should render with placeholders."""
    rendered = render_template("docs/this-project.md.j2", _default_context())
    assert "# test-project" in rendered
    assert "What this project is" in rendered
    assert "How to run / test" in rendered
    assert "Entry points" in rendered


def test_resolve_output_path() -> None:
    context = {"agent_dir": ".cursor", "docs_dir": "docs"}
    path = resolve_output_path("{agent_dir}/commands/iflow-init.md", context)
    assert path == Path(".cursor/commands/iflow-init.md")


def test_manifest_entry_count() -> None:
    # Cursor is skills-first: 1 rule + 1 doc + 24 skills = 26
    assert len(TEMPLATE_MANIFEST) == 26


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


def test_build_manifest_cursor_matches_default() -> None:
    """The default TEMPLATE_MANIFEST is the cursor profile manifest."""
    assert build_manifest(EDITORS["cursor"]) == TEMPLATE_MANIFEST
    assert len(build_manifest(EDITORS["cursor"])) == 26


def test_build_manifest_cursor_has_skills_and_rules_but_no_commands() -> None:
    """Cursor now uses Agent Skills as the primary slash-menu surface."""
    manifest = build_manifest(get_profile("cursor"))
    template_names = [name for name, _ in manifest]
    paths = _resolved_paths("cursor")
    assert not any(name.startswith("commands/") for name in template_names)
    assert ".cursor/skills/iflow/SKILL.md" in paths
    assert ".cursor/skills/iflow-iflow/SKILL.md" not in paths
    assert ".cursor/rules/issueflow-rules.mdc" in paths


def test_build_manifest_codex_has_skills_and_docs_but_no_commands() -> None:
    """Codex: skills (24) + docs (1), no slash commands and no rules extra."""
    manifest = build_manifest(get_profile("codex"))
    template_names = [name for name, _ in manifest]
    assert not any(name.startswith("commands/") for name in template_names)
    assert sum(name.startswith("skills/") for name in template_names) == 24
    assert "docs/issue-workflow.md.j2" in template_names
    # No .mdc / CLAUDE.md rules extra for Codex.
    assert not any(name.startswith("rules/") for name in template_names)
    assert len(manifest) == 25


def test_build_manifest_opencode_uses_singular_command_dir() -> None:
    paths = _resolved_paths("opencode")
    assert ".opencode/command/iflow-init.md" in paths
    assert ".opencode/skills/iflow-init/SKILL.md" in paths
    # opencode has no editor-specific rules file (AGENTS.md is handled by init).
    assert not any(p.endswith(".mdc") for p in paths)
    assert "CLAUDE.md" not in paths


def test_build_manifest_claude_emits_claude_md_and_commands() -> None:
    manifest = build_manifest(get_profile("claude"))
    assert ("rules/CLAUDE.md.j2", "CLAUDE.md") in manifest
    paths = _resolved_paths("claude")
    assert ".claude/commands/iflow-init.md" in paths
    assert "CLAUDE.md" in paths


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
            rendered = render_template(template_name, context)
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
        "iflow_pick",
        "iflow_init",
        "iflow_comments",
        "iflow_plan",
        "iflow_build",
        "iflow_pause",
        "iflow_close",
        "iflow_cleanup",
        "iflow_yolo",
        "iflow_fix",
        "iflow_issue",
        "iflow_status",
        "iflow_archive",
        "iflow_cycle",
        "iflow_auto",
        "iflow_version_bump",
        "iflow_history_update",
        "iflow_graphify",
    ):
        assert f"skills/{skill}/SKILL.md.j2" in template_names


def test_claude_manifest_has_expected_commands() -> None:
    """Command-emitting editors still include every slash-command template."""
    template_names = {name for name, _ in build_manifest(get_profile("claude"))}
    for command in (
        "iflow",
        "iflow-pick",
        "iflow-init",
        "iflow-plan",
        "iflow-build",
        "iflow-pause",
        "iflow-close",
        "iflow-cleanup",
        "iflow-yolo",
        "iflow-fix",
        "iflow-issue",
        "iflow-status",
        "iflow-doctor",
        "iflow-archive",
        "iflow-cycle",
        "iflow-auto",
        "iflow-graphify",
    ):
        assert f"commands/{command}.md.j2" in template_names


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
    rendered = render_template("commands/iflow-build.md.j2", _default_context())
    assert "Branch status preflight" in rendered
    assert "Sweep stale current issues" in rendered
    assert "git fetch --prune" in rendered


_CLI_FASTPATH_SURFACES = {
    "commands/iflow.md.j2": "issue-flow agent state",
    "commands/iflow-status.md.j2": "issue-flow status",
    "commands/iflow-init.md.j2": "issue-flow agent capture",
    "commands/iflow-build.md.j2": "issue-flow agent preflight",
    "commands/iflow-plan.md.j2": "issue-flow agent preflight",
    "skills/iflow_iflow/SKILL.md.j2": "issue-flow agent state",
    "skills/iflow_status/SKILL.md.j2": "issue-flow status",
    "skills/iflow_init/SKILL.md.j2": "issue-flow agent capture",
    "skills/iflow_build/SKILL.md.j2": "issue-flow agent preflight",
    "skills/iflow_plan/SKILL.md.j2": "issue-flow agent preflight",
    "commands/iflow-archive.md.j2": "issue-flow agent archive",
    "skills/iflow_archive/SKILL.md.j2": "issue-flow agent archive",
    "commands/iflow-review.md.j2": "issue-flow agent label-candidates",
    "skills/iflow_review/SKILL.md.j2": "issue-flow agent label-candidates",
}


def test_cli_fast_path_notes_render_with_fallback() -> None:
    """Updated surfaces advertise the optional CLI fast path AND keep a fallback."""
    for template_name, expected_cmd in _CLI_FASTPATH_SURFACES.items():
        rendered = render_template(template_name, _default_context())
        assert "CLI fast path (optional)" in rendered, template_name
        assert expected_cmd in rendered, template_name
        # The CLI is optional, so the note must point back to the manual steps.
        assert "fall back to the manual" in rendered, template_name


def test_iflow_init_fast_path_mentions_sweep_and_capture() -> None:
    """/iflow-init's fast path covers both the capture and the sweep shortcuts."""
    rendered = render_template("commands/iflow-init.md.j2", _default_context())
    assert "issue-flow agent capture" in rendered
    assert "issue-flow agent sweep --except" in rendered


def test_issue_close_delegates_post_merge_cleanup_to_issue_cleanup() -> None:
    """/iflow-close no longer deletes branches; it points at /iflow-cleanup instead."""
    rendered = render_template("commands/iflow-close.md.j2", _default_context())
    assert "/iflow-cleanup" in rendered
    assert "git pull --ff-only" in rendered
    # The destructive branch delete lives in /iflow-cleanup now, not /iflow-close.
    assert "git branch -d" not in rendered


def test_issue_close_switches_to_default_when_clean_unless_stay() -> None:
    """/iflow-close should switch back to default after PR when the tree is clean."""
    rendered = render_template("commands/iflow-close.md.j2", _default_context())
    assert "stay on branch" in rendered
    assert "don't switch" in rendered
    assert "dont switch to main" in rendered
    assert "git status --porcelain" in rendered
    assert "git switch <default>" in rendered
    assert "A clean tree here means" in rendered


def test_issue_cleanup_describes_post_merge_branch_cleanup() -> None:
    """The /iflow-cleanup command owns the post-merge branch cleanup logic."""
    rendered = render_template("commands/iflow-cleanup.md.j2", _default_context())
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
    skill = render_template("skills/iflow_cleanup/SKILL.md.j2", _default_context())
    assert "include github" in skill.lower()
    assert (
        "Second consolidated confirm" in skill or "second consolidated confirm" in skill
    )
    assert "issue-flow agent branches" in skill


def test_issue_start_requires_or_offers_plan() -> None:
    """/iflow-build should read the plan file and offer to run /iflow-plan when missing."""
    rendered = render_template("commands/iflow-build.md.j2", _default_context())
    assert "issue<N>_plan.md" in rendered
    assert "/iflow-plan" in rendered


def test_issue_plan_writes_plan_file_and_stops_for_confirmation() -> None:
    """/iflow-plan must produce a plan file and require confirmation."""
    rendered = render_template("commands/iflow-plan.md.j2", _default_context())
    assert "issue<N>_plan.md" in rendered
    assert "Goal" in rendered
    assert "Approach" in rendered
    assert "Confirm" in rendered or "confirmation" in rendered.lower()
    assert "1.75" in rendered
    assert "Prior-art discovery" in rendered
    assert "GRAPH_REPORT.md" in rendered
    assert "### Prior art" in rendered


def test_issue_plan_includes_prior_art_discovery() -> None:
    """/iflow-plan must document graceful graphify + grep prior-art checklist."""
    rendered = render_template("commands/iflow-plan.md.j2", _default_context())
    assert "Prior-art discovery" in rendered
    assert "God Nodes" in rendered
    assert "None found (grep + graph checked)" in rendered
    assert "Open questions" in rendered
    skill = render_template("skills/iflow_plan/SKILL.md.j2", _default_context())
    assert "Prior-art discovery" in skill or "Prior art" in skill
    assert "### Prior art" in skill


def test_templates_reference_project_brief() -> None:
    """Rules, plan, start, and docs should tell agents about this-project.md."""
    templates = (
        "rules/issueflow-rules.mdc.j2",
        "rules/AGENTS.md.j2",
        "rules/CLAUDE.md.j2",
        "commands/iflow-plan.md.j2",
        "commands/iflow-build.md.j2",
        "skills/iflow_plan/SKILL.md.j2",
        "skills/iflow_build/SKILL.md.j2",
        "docs/issue-workflow.md.j2",
    )
    for template_name in templates:
        rendered = render_template(template_name, _default_context())
        assert "this-project.md" in rendered, template_name


def test_issue_start_reads_prior_art_from_plan() -> None:
    """/iflow-build should remind the agent to read ### Prior art from the plan."""
    rendered = render_template("commands/iflow-build.md.j2", _default_context())
    assert "### Prior art" in rendered
    skill = render_template("skills/iflow_build/SKILL.md.j2", _default_context())
    assert "### Prior art" in skill


def test_issue_pause_moves_to_partly_solved() -> None:
    """/iflow-pause moves the issue group to the partly-solved folder."""
    rendered = render_template("commands/iflow-pause.md.j2", _default_context())
    assert "02-partly-solved-issues" in rendered
    assert "Remaining work" in rendered
    assert "- [ ] Done" in rendered


def test_issue_yolo_has_safeguards() -> None:
    """/iflow-yolo must advertise the up-front safeguards before chaining."""
    rendered = render_template("commands/iflow-yolo.md.j2", _default_context())
    assert "uv run pytest" in rendered
    assert "default branch" in rendered.lower()
    # Must not chain cleanup automatically.
    assert "/iflow-cleanup" in rendered


def test_issue_yolo_chains_hands_off_close() -> None:
    """/iflow-yolo must forward the yolo token so close merges and pulls itself."""
    for template_name in (
        "commands/iflow-yolo.md.j2",
        "skills/iflow_yolo/SKILL.md.j2",
    ):
        rendered = render_template(template_name, _default_context())
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
        rendered = render_template(template_name, _default_context())
        assert "`yolo`" in rendered, template_name
        assert "gh pr merge" in rendered, template_name
        assert "gh pr list" in rendered, template_name
        assert "gh pr checks" in rendered, template_name
        assert "--watch" in rendered, template_name
        assert "15" in rendered, template_name
        assert "--squash --auto" in rendered, template_name
        assert "last resort" in rendered.lower(), template_name
        # Branch deletion still belongs to /iflow-cleanup, never to close.
        assert "branch deletion stays in `/iflow-cleanup`" in rendered.lower(), (
            template_name
        )


def test_close_bakes_pr_merge_method_and_gates_cleanup_reminder() -> None:
    """pr_merge_method and remind_cleanup gate close skill wording."""
    on = render_template(
        "skills/iflow_close/SKILL.md.j2",
        {**_default_context(), "pr_merge_method": "merge", "remind_cleanup": True},
    )
    assert "gh pr merge <number> --merge" in on
    assert "/iflow-cleanup" in on
    off = render_template(
        "skills/iflow_close/SKILL.md.j2",
        {**_default_context(), "remind_cleanup": False, "ruff_autofix": False},
    )
    assert "ruff check --fix" not in off
    # Still mentions cleanup skill ownership, but step 10/11 reminder is gated.
    assert "Tell the user to run **`/iflow-cleanup`**" not in off


def test_cycle_bakes_max_issues() -> None:
    rendered = render_template(
        "skills/iflow_cycle/SKILL.md.j2",
        {**_default_context(), "cycle_max_issues": 20},
    )
    assert "longer than **20**" in rendered
    assert "default 20" in rendered


def test_workflow_doc_bakes_auto_adversarial_loops() -> None:
    rendered = render_template(
        "docs/issue-workflow.md.j2",
        {**_default_context(), "auto_adversarial_loops": 5},
    )
    assert "auto_adversarial_loops" in rendered
    assert "**5**" in rendered
    assert "loops:<n>" in rendered


def test_iflow_auto_skill_skeleton_renders() -> None:
    assert "iflow_auto" in SKILL_DIRS
    assert "iflow-auto" in COMMAND_NAMES
    skill = render_template("skills/iflow_auto/SKILL.md.j2", _default_context())
    assert "auto_status.md" in skill
    assert "adversarial review not implemented" in skill
    assert "loops:<n>" in skill
    assert str(_default_context()["auto_adversarial_loops"]) in skill
    cmd = render_template("commands/iflow-auto.md.j2", _default_context())
    assert "iflow-auto/SKILL.md" in cmd
    assert "Stage 1" in cmd


def test_iflow_lists_auto_as_off_path() -> None:
    """/iflow and its skill must list /iflow-auto among the explicit-only commands."""
    cmd = render_template("commands/iflow.md.j2", _default_context())
    skill = render_template("skills/iflow_iflow/SKILL.md.j2", _default_context())
    assert "/iflow-auto" in cmd
    assert "/iflow-auto" in skill
    rules = render_template("rules/AGENTS.md.j2", _default_context())
    assert "/iflow-auto" in rules
    assert "auto_status.md" in rules


def test_start_auto_close_chains_into_close() -> None:
    off = render_template("skills/iflow_build/SKILL.md.j2", _default_context())
    assert "tell the user to run `/iflow-close`" in off
    on = render_template(
        "skills/iflow_build/SKILL.md.j2",
        {**_default_context(), "auto_close": True},
    )
    assert "follow" in on and "iflow-close/SKILL.md" in on
    assert "tell the user to run `/iflow-close`" not in on


def test_build_early_pr_step_and_tokens() -> None:
    """Build always documents early-PR tokens; baked early_pr appears in text."""
    off = render_template("skills/iflow_build/SKILL.md.j2", _default_context())
    assert "Early PR tokens" in off
    assert "`early`" in off and "`noearly`" in off
    assert "gh pr create --draft" in off
    assert "Refs #N" in off
    assert "currently **False**" in off or "currently **false**" in off
    on = render_template(
        "skills/iflow_build/SKILL.md.j2",
        {**_default_context(), "early_pr": True},
    )
    assert "currently **True**" in on or "currently **true**" in on
    cmd = render_template("commands/iflow-build.md.j2", _default_context())
    assert "Early pull request (optional)" in cmd
    assert "gh pr list" in cmd


def test_close_formalizes_draft_and_early_pr_reuse() -> None:
    rendered = render_template("skills/iflow_close/SKILL.md.j2", _default_context())
    assert "Draft PR token" in rendered
    assert "gh pr create --draft" in rendered
    assert "gh pr ready" in rendered
    assert "early pr" in rendered.lower()
    assert "skip merge entirely" in rendered.lower()
    cmd = render_template("commands/iflow-close.md.j2", _default_context())
    assert "`draft`" in cmd
    assert "gh pr create --draft" in cmd
    assert "gh pr ready" in cmd


def test_history_confirm_changelog_update_gate() -> None:
    on = render_template(
        "skills/iflow_history_update/SKILL.md.j2",
        {**_default_context(), "confirm_changelog_update": True},
    )
    assert "confirm once before writing" in on
    assert "**stop**" in on
    assert "nohistory" in on
    off = render_template(
        "skills/iflow_history_update/SKILL.md.j2",
        {**_default_context(), "confirm_changelog_update": False},
    )
    assert "without a confirm prompt" in off
    assert "confirm once before writing" not in off


def test_changelog_timing_forbids_post_merge_updates() -> None:
    """Close/history/cleanup must keep HISTORY in the PR commit, not after merge."""
    ctx = {**_default_context(), "confirm_changelog_update": False}
    history = render_template("skills/iflow_history_update/SKILL.md.j2", ctx)
    close = render_template("skills/iflow_close/SKILL.md.j2", ctx)
    cleanup = render_template("skills/iflow_cleanup/SKILL.md.j2", ctx)
    assert "after close has finished or after merge" in history
    assert "early PR" in history
    assert "Changelog timing" in close
    assert "Do **not** offer to update" in cleanup


def test_issue_close_bakes_checks_watch_minutes_override() -> None:
    """checks_watch_minutes from context is baked into close surfaces."""
    context = {**_default_context(), "checks_watch_minutes": 30}
    for template_name in (
        "commands/iflow-close.md.j2",
        "skills/iflow_close/SKILL.md.j2",
    ):
        rendered = render_template(template_name, context)
        assert "30" in rendered, template_name


def test_issue_pick_routes_yolo_label_when_label_flows_on() -> None:
    """/iflow-pick surfaces the label-driven yolo routing when label_flows is on."""
    context = {**_default_context(), "label_flows": True, "yolo_label": "fast-track"}
    for template_name in (
        "commands/iflow-pick.md.j2",
        "skills/iflow_pick/SKILL.md.j2",
    ):
        rendered = render_template(template_name, context)
        assert "fast-track" in rendered, template_name
        assert "iflow-yolo" in rendered, template_name


def test_issue_pick_omits_label_routing_when_label_flows_off() -> None:
    """With label_flows off, /iflow-pick renders no label-driven routing text."""
    context = {**_default_context(), "label_flows": False, "yolo_label": "yolo"}
    for template_name in (
        "commands/iflow-pick.md.j2",
        "skills/iflow_pick/SKILL.md.j2",
    ):
        rendered = render_template(template_name, context)
        assert "Label-driven yolo flow" not in rendered, template_name


def test_issue_fix_describes_interactive_session() -> None:
    """/iflow-fix must describe the off-path interactive iterative-fix session."""
    rendered = render_template("commands/iflow-fix.md.j2", _default_context())
    # Off-path and explicitly not driven by /iflow during a session.
    assert "off-path" in rendered.lower()
    assert "/iflow" in rendered
    # Always creates a GitHub issue via gh; GitLab is out of scope.
    assert "gh issue create" in rendered
    assert "GitLab is not supported" in rendered
    # The fix loop records each fix in the status file's log section.
    assert "Iterative fixes log" in rendered
    assert "issue<N>_status.md" in rendered
    # Branch-from-current-vs-default choice and delegation to init/close.
    assert "/iflow-init" in rendered
    assert "/iflow-close" in rendered
    # Keeps the unchecked Done checkbox during the session.
    assert "- [ ] Done" in rendered


def test_issue_fix_skill_mirrors_command() -> None:
    """The issue-fix skill must carry the same session flow and frontmatter."""
    rendered = render_template("skills/iflow_fix/SKILL.md.j2", _default_context())
    assert "name: iflow-fix" in rendered
    assert "disable-model-invocation: true" in rendered
    assert "gh issue create" in rendered
    assert "Iterative fixes log" in rendered
    assert "/iflow-init" in rendered
    assert "/iflow-close" in rendered


def test_iflow_archive_command_documents_gated_deletion() -> None:
    """/iflow-archive must describe the summary file, recovery ref, and gating."""
    rendered = render_template("commands/iflow-archive.md.j2", _default_context())
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
    assert "off-path" in rendered.lower()
    # Selection inputs.
    assert "keep <K>" in rendered
    assert "all" in rendered


def test_iflow_archive_skill_mirrors_command() -> None:
    """The iflow-archive skill must carry the same flow and frontmatter."""
    rendered = render_template("skills/iflow_archive/SKILL.md.j2", _default_context())
    assert "name: iflow-archive" in rendered
    assert "disable-model-invocation: true" in rendered
    assert "_archived_issues.md" in rendered
    assert "git rev-parse HEAD" in rendered
    assert "Consolidated confirm" in rendered
    # Only the solved folder is ever touched.
    assert "03-solved-issues" in rendered


def test_iflow_does_not_auto_dispatch_archive() -> None:
    """/iflow must list /iflow-archive among the explicit-only commands."""
    cmd = render_template("commands/iflow.md.j2", _default_context())
    assert "/iflow-archive" in cmd


def test_rules_body_mentions_archive() -> None:
    """The shared rules body must describe /iflow-archive as off-path + gated."""
    rendered = render_template("rules/AGENTS.md.j2", _default_context())
    assert "/iflow-archive" in rendered
    assert "_archived_issues.md" in rendered
    assert "pre-archive git ref" in rendered


def test_iflow_lists_issue_fix_as_off_path() -> None:
    """/iflow and its skill must list /iflow-fix among the explicit-only commands."""
    cmd = render_template("commands/iflow.md.j2", _default_context())
    skill = render_template("skills/iflow_iflow/SKILL.md.j2", _default_context())
    assert "/iflow-fix" in cmd
    assert "/iflow-fix" in skill


def test_iflow_issue_describes_normal_issue_create() -> None:
    """/iflow-issue must describe confirm-gated create + optional init handoff."""
    rendered = render_template("commands/iflow-issue.md.j2", _default_context())
    assert "off-path" in rendered.lower()
    assert "gh issue create" in rendered
    assert "GitLab is not supported" in rendered
    assert "Problem / context" in rendered
    assert "Acceptance criteria" in rendered
    assert "/iflow-init" in rendered
    assert "/iflow-plan" in rendered
    assert "epic" in rendered.lower()


def test_iflow_issue_skill_mirrors_command() -> None:
    """The iflow-issue skill must carry the same flow and frontmatter."""
    rendered = render_template("skills/iflow_issue/SKILL.md.j2", _default_context())
    assert "name: iflow-issue" in rendered
    assert "disable-model-invocation: true" in rendered
    assert "gh issue create" in rendered
    assert "/iflow-init" in rendered
    assert "/iflow-plan" in rendered
    assert "Acceptance criteria" in rendered


def test_iflow_lists_issue_as_off_path() -> None:
    """/iflow and its skill must list /iflow-issue among the explicit-only commands."""
    cmd = render_template("commands/iflow.md.j2", _default_context())
    skill = render_template("skills/iflow_iflow/SKILL.md.j2", _default_context())
    assert "/iflow-issue" in cmd
    assert "/iflow-issue" in skill


def test_rules_body_mentions_iflow_issue() -> None:
    """The shared rules body must describe /iflow-issue as off-path."""
    rendered = render_template("rules/AGENTS.md.j2", _default_context())
    assert "/iflow-issue" in rendered
    assert "well-specified normal GitHub issue" in rendered


def test_iflow_review_command_documents_kinds_and_cli() -> None:
    """/iflow-review must describe kinds, confirm gate, and CLI helpers."""
    rendered = render_template("commands/iflow-review.md.j2", _default_context())
    assert "label-candidates" in rendered
    assert "label-apply" in rendered
    assert "yolo" in rendered
    assert "Consolidated confirm" in rendered or "consolidated confirm" in rendered
    assert "off-path" in rendered.lower()
    assert "gh label create" in rendered


def test_iflow_review_skill_mirrors_command() -> None:
    """The iflow-review skill must carry the same flow and frontmatter."""
    rendered = render_template("skills/iflow_review/SKILL.md.j2", _default_context())
    assert "name: iflow-review" in rendered
    assert "disable-model-invocation: true" in rendered
    assert "label-candidates" in rendered
    assert "label-apply" in rendered
    assert "well-specified" in rendered
    assert "low blast radius" in rendered
    assert "/iflow-cycle yolo" in rendered


def test_iflow_cycle_documents_yolo_alias() -> None:
    """/iflow-cycle must document the yolo → label:<yolo_label> alias (#175)."""
    context = {**_default_context(), "yolo_label": "fast-track"}
    skill = render_template("skills/iflow_cycle/SKILL.md.j2", context)
    cmd = render_template("commands/iflow-cycle.md.j2", context)
    for rendered in (skill, cmd):
        assert "label:fast-track" in rendered
        assert "yolo" in rendered
        assert "All yolo issues" in rendered or "all yolo" in rendered.lower()
    rules = render_template("rules/AGENTS.md.j2", context)
    assert "/iflow-cycle yolo" in rules
    assert "label:fast-track" in rules


def test_iflow_epic_documents_goal_and_model_markers() -> None:
    """Epic skill/command must document Stage/issue Goal and Model markers (#193)."""
    skill = render_template("skills/iflow_epic/SKILL.md.j2", _default_context())
    cmd = render_template("commands/iflow-epic.md.j2", _default_context())
    for rendered in (skill, cmd):
        assert "- Goal:" in rendered
        assert "Model:" in rendered
        assert "deep" in rendered and "fast" in rendered and "default" in rendered
    assert "Copied into the GitHub issue body" in skill or "copied into" in skill.lower()


def test_iflow_lists_review_as_off_path() -> None:
    """/iflow must list /iflow-review among the explicit-only commands."""
    cmd = render_template("commands/iflow.md.j2", _default_context())
    skill = render_template("skills/iflow_iflow/SKILL.md.j2", _default_context())
    assert "/iflow-review" in cmd
    assert "/iflow-review" in skill


def test_rules_body_mentions_review() -> None:
    """The shared rules body must describe /iflow-review as off-path."""
    rendered = render_template("rules/AGENTS.md.j2", _default_context())
    assert "/iflow-review" in rendered
    assert "label-candidates" in rendered


def test_iflow_describes_state_machine() -> None:
    """/iflow must describe the four-state dispatch and name its downstream targets."""
    rendered = render_template("commands/iflow.md.j2", _default_context())
    # Dispatches into all four linear-flow commands.
    for target in (
        "/iflow-init",
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
    assert "/iflow-yolo" in rendered


def test_iflow_treats_branch_derived_n_as_authoritative() -> None:
    """/iflow's step 0 must treat a branch-derived N as authoritative.

    The branch-derived N should win even when `issue<N>_*` files don't exist
    yet, or when unrelated groups sit in 01-current-issues. It should also
    trigger the archived-issue guard warning when the group lives in
    02-partly-solved or 03-solved.
    """
    rendered = render_template("commands/iflow.md.j2", _default_context())
    assert "authoritative" in rendered.lower()
    # Both archive folders are consulted for the archived-issue guard warning.
    assert "02-partly-solved-issues" in rendered
    assert "03-solved-issues" in rendered
    assert "archived-issue guard" in rendered.lower()


def test_issue_pick_documents_three_phases_and_fix_shortcut() -> None:
    """/iflow-pick must describe its three phases, ranking inputs, and the `fix` shortcut."""
    rendered = render_template("commands/iflow-pick.md.j2", _default_context())
    # Three phases.
    assert "Phase 1" in rendered
    assert "Phase 2" in rendered
    assert "Phase 3" in rendered
    # Parked work is the primary candidate source, GitHub the fallback.
    assert "02-partly-solved-issues" in rendered
    assert "gh issue list" in rendered
    # Relevance ranking combines milestone + labels + topical similarity.
    assert "Milestone" in rendered or "milestone" in rendered
    assert "Labels" in rendered or "label" in rendered
    # `fix` shortcut creates a new issue every time.
    assert "fix" in rendered
    assert "gh issue create" in rendered
    # Delegates capture to /iflow-init and hands off to /iflow-plan.
    assert "/iflow-init" in rendered
    assert "/iflow-plan" in rendered
    # Off-path: not auto-dispatched by /iflow.
    assert "off-path" in rendered.lower()
    # Phase B (auto sub-issue creation) is explicitly out of scope.
    assert "Phase B" in rendered


def test_issue_pick_skill_mirrors_command() -> None:
    """The issue-pick skill must carry the same front-door flow and frontmatter."""
    rendered = render_template("skills/iflow_pick/SKILL.md.j2", _default_context())
    assert "name: iflow-pick" in rendered
    assert "disable-model-invocation: true" in rendered
    assert "Phase 1" in rendered
    assert "Phase 2" in rendered
    assert "Phase 3" in rendered
    assert "/iflow-init" in rendered
    assert "/iflow-plan" in rendered


def test_iflow_does_not_auto_dispatch_issue_pick() -> None:
    """/iflow must list /iflow-pick among the explicit-only, never-auto-dispatched commands."""
    cmd = render_template("commands/iflow.md.j2", _default_context())
    skill = render_template("skills/iflow_iflow/SKILL.md.j2", _default_context())
    assert "/iflow-pick" in cmd
    assert "/iflow-pick" in skill


def test_issue_init_mentions_branch_preflight_and_archive_guard() -> None:
    """The /iflow-init command must include the preflight and archived-issue guard."""
    rendered = render_template("commands/iflow-init.md.j2", _default_context())
    assert "Branch status preflight" in rendered
    assert "Archived-issue guard" in rendered or "archived" in rendered.lower()


def test_issueflow_rules_has_branch_hygiene_section() -> None:
    """The workspace rules must describe branch and folder hygiene expectations."""
    rendered = render_template("rules/issueflow-rules.mdc.j2", _default_context())
    assert "Branch hygiene" in rendered
    assert "git branch -d" in rendered
    assert "Folder hygiene" in rendered
    assert "alwaysApply: false" in rendered
    assert '"**/*"' in rendered or "'**/*'" in rendered


def test_lifecycle_skills_include_resolve_partial() -> None:
    """Lifecycle skills must document multi-root project-root resolution."""
    stems = (
        "iflow_init",
        "iflow_close",
        "iflow_cleanup",
        "iflow_pick",
        "iflow_status",
        "iflow_iflow",
        "iflow_build",
        "iflow_plan",
        "iflow_pause",
        "iflow_yolo",
        "iflow_fix",
    )
    for stem in stems:
        rendered = render_template(f"skills/{stem}/SKILL.md.j2", _default_context())
        assert "issue-flow agent resolve" in rendered, stem
        assert (
            "Multi-root workspaces" in rendered or "multi-root" in rendered.lower()
        ), stem


def test_rules_body_mentions_multi_root_workspaces() -> None:
    """The shared rules body must point agents at the multi-root contract."""
    rendered = render_template("rules/_body.md.j2", _default_context())
    assert "Multi-root workspaces" in rendered
    assert "issue-flow agent resolve" in rendered
    assert "multi-repo-workspaces.md" in rendered


def test_rules_body_documents_slashless_chat_invocation() -> None:
    """Issue #118: agents must honor `iflow plan` as explicit invocation."""
    rendered = render_template("rules/_body.md.j2", _default_context())
    assert "Chat invocation (no slash)" in rendered
    assert "`iflow plan`" in rendered
    assert "`iflow pick`" in rendered or "`iflow {{ cmd[6:] }}`" in rendered
    assert "starts with" in rendered.lower()
    for template_name in ("rules/issueflow-rules.mdc.j2", "rules/AGENTS.md.j2"):
        rules = render_template(template_name, _default_context())
        assert "Chat invocation (no slash)" in rules
        assert "`iflow plan`" in rules


def test_iflow_plan_skill_documents_slashless_invoke_line() -> None:
    """Lifecycle skills should recommend `iflow plan` before slash form."""
    rendered = render_template("skills/iflow_plan/SKILL.md.j2", _default_context())
    assert "**Invoke:**" in rendered
    assert "type `iflow plan` in chat" in rendered
    assert "/iflow-plan" in rendered


def test_issue_workflow_doc_leads_with_slashless_chat() -> None:
    """docs/issue-workflow should document space form before slash-only wording."""
    rendered = render_template("docs/issue-workflow.md.j2", _default_context())
    assert "Keyboard-friendly chat" in rendered
    plan_idx = rendered.index("iflow plan")
    slash_only = rendered.find("| `iflow-plan` | `iflow plan`")
    assert slash_only == -1 or plan_idx < slash_only
    assert "`iflow plan`, `iflow-plan`, `/iflow-plan`" in rendered


def test_issue_workflow_doc_covers_epic_cycle_review_examples() -> None:
    """Scaffolded workflow doc must document epic/cycle/review with examples (#179)."""
    rendered = render_template("docs/issue-workflow.md.j2", _default_context())
    assert "/iflow-epic" in rendered
    assert "/iflow-cycle" in rendered
    assert "/iflow-review" in rendered
    assert "iflow review yolo" in rendered
    assert "iflow cycle yolo" in rendered
    assert "/iflow-cycle yolo" in rendered
    assert "iflow epic" in rendered
    assert "publish" in rendered
    assert "iflow-epic" in rendered
    assert "iflow-cycle" in rendered
    # Off-path list should name the batch/epic skills explicitly.
    assert "/iflow-epic" in rendered.split("Not auto-dispatched:")[1].split("\n")[0]
    assert "/iflow-cycle" in rendered.split("Not auto-dispatched:")[1].split("\n")[0]


def test_rules_body_defers_to_project_toolchain_and_covers_conda() -> None:
    """Regression for issue #58: the shared rules body must defer to the
    project's existing toolchain and cover conda, not hard-mandate uv."""
    # The body is included by all three rules outputs; assert on each so none drift.
    for template_name in (
        "rules/issueflow-rules.mdc.j2",
        "rules/AGENTS.md.j2",
        "rules/CLAUDE.md.j2",
    ):
        rendered = render_template(template_name, _default_context())
        lowered = rendered.lower()
        # Defers to whatever the project already documents.
        assert "respect the project's existing toolchain" in lowered
        # conda is explicitly covered, including pytest inside the activated env.
        assert "conda" in lowered
        assert "conda activate" in rendered
        assert "conda run -n" in rendered
        # uv stays the documented default/example…
        assert "uv run" in rendered
        # …but the old hard mandate is gone.
        assert "Use `uv` exclusively" not in rendered
        assert "uv exclusively" not in lowered


def test_issue_close_describes_history_update_step() -> None:
    """/iflow-close must describe the HISTORY.md update step and its input tokens."""
    rendered = render_template("commands/iflow-close.md.j2", _default_context())
    assert "HISTORY.md" in rendered
    assert "[Unreleased]" in rendered
    assert "iflow-history-update" in rendered
    # Opt-out token is documented.
    assert "nohistory" in rendered
    # Override token for the bullet summary is documented.
    assert 'log "..."' in rendered or "log " in rendered


def test_iflow_close_and_start_nudge_ruff_fix_when_present() -> None:
    """Lifecycle commands should run ruff check --fix when ruff is in the project."""
    for template_name in (
        "commands/iflow-close.md.j2",
        "commands/iflow-build.md.j2",
        "skills/iflow_close/SKILL.md.j2",
        "skills/iflow_build/SKILL.md.j2",
    ):
        rendered = render_template(template_name, _default_context())
        assert "ruff check --fix" in rendered, template_name
        assert "[tool.ruff]" in rendered, template_name


def test_history_update_skill_documents_both_modes() -> None:
    """The history-update skill must describe append-and-promote, plus the missing-file fallback."""
    rendered = render_template(
        "skills/iflow_history_update/SKILL.md.j2", _default_context()
    )
    assert "HISTORY.md" in rendered
    assert "[Unreleased]" in rendered
    # Append mode (no bump) and promote mode (with bump) are both described.
    assert "append" in rendered.lower()
    assert "promote" in rendered.lower()
    # Gracefully skip when the file is missing; never auto-create.
    assert "skipping changelog" in rendered.lower() or "skip" in rendered.lower()
    assert "Never create" in rendered or "never create" in rendered.lower()


def test_history_update_skill_respects_history_file_override() -> None:
    """The history-update skill should reference {{ history_file }} so custom filenames work."""
    context = _default_context()
    context["history_file"] = "CHANGELOG.md"
    rendered = render_template("skills/iflow_history_update/SKILL.md.j2", context)
    assert "CHANGELOG.md" in rendered
    # No leftover Jinja placeholder.
    assert "{{ history_file }}" not in rendered


def test_issue_yolo_forwards_history_tokens() -> None:
    """/iflow-yolo must forward the new history-related tokens to /iflow-close."""
    rendered = render_template("commands/iflow-yolo.md.j2", _default_context())
    assert "nohistory" in rendered
    assert "log " in rendered  # `log "..."` bullet-summary override
    assert "stay" in rendered
    assert "don't switch" in rendered


def test_issue_init_fetches_and_triages_comments() -> None:
    """/iflow-init must fetch comments and call the comments-triage skill."""
    rendered = render_template("commands/iflow-init.md.j2", _default_context())
    # gh fetch now asks for the comments field too.
    assert "title,body,url,number,comments" in rendered
    # The curated section header appears in the file-content template.
    assert "## Comments (curated summary)" in rendered
    # The triage step exists and delegates to the new skill.
    assert "Triage comments" in rendered
    assert "iflow-comments" in rendered
    # The three triage buckets are named.
    assert "Additional tasks" in rendered
    assert "Clarifications" in rendered
    assert "Superseded" in rendered
    # The body contract: preserve the fetched body text faithfully, but the
    # "Agent efficiency" guidance (issue #9) says not to obsess over byte-exactness.
    assert "Agent efficiency" in rendered
    assert "Preserve the issue **body** text exactly as returned by GitHub" in rendered


def test_issue_init_documents_agent_efficiency() -> None:
    """Regression guard for issue #9: the Agent efficiency guidance must live in the template.

    It was originally added only to the generated `.cursor/commands/iflow-init.md` and got
    wiped by a later regeneration; it now belongs in the source template so it survives.
    """
    rendered = render_template("commands/iflow-init.md.j2", _default_context())
    assert "## Agent efficiency" in rendered
    assert "trailing newlines" in rendered
    assert "CRLF" in rendered
    # The reconciled body contract no longer demands literal byte-for-byte equality.
    assert "byte-for-byte" not in rendered
    # The mirror skill should not re-introduce the stricter "byte-for-byte" wording.
    skill = render_template("skills/iflow_init/SKILL.md.j2", _default_context())
    assert "byte-for-byte" not in skill


def test_issue_init_skill_delegates_to_comments_skill() -> None:
    """The issue-init skill must fetch comments and point at the comments skill."""
    rendered = render_template("skills/iflow_init/SKILL.md.j2", _default_context())
    assert "title,body,url,number,comments" in rendered
    assert "iflow-comments" in rendered
    assert "## Comments (curated summary)" in rendered


def test_caveman_skill_renders_full_mode_english_only() -> None:
    """The caveman skill ships as a model-invocable, full-mode-only behavior skill."""
    rendered = render_template("skills/caveman/SKILL.md.j2", _default_context())
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


def test_rules_body_caveman_pointer_is_membership_gated() -> None:
    """The rules body mentions caveman only when it is in included_skills."""
    with_caveman = _default_context()
    rendered_on = render_template("rules/AGENTS.md.j2", with_caveman)
    assert "caveman" in rendered_on.lower()
    assert "Optional response styles" in rendered_on

    without_caveman = _default_context()
    without_caveman["included_skills"] = [s for s in _ALL_SKILLS if s != "caveman"]
    rendered_off = render_template("rules/AGENTS.md.j2", without_caveman)
    assert "Optional response styles" not in rendered_off


def test_rules_body_caveman_default_switches_pointer_wording() -> None:
    """caveman_default flips the pointer between off-by-default and always-on."""
    off = _default_context()
    off["caveman_default"] = False
    rendered_off = render_template("rules/AGENTS.md.j2", off)
    assert "off by default" in rendered_off
    assert "on by default for this project" not in rendered_off

    on = _default_context()
    on["caveman_default"] = True
    rendered_on = render_template("rules/AGENTS.md.j2", on)
    assert "on by default for this project" in rendered_on
    assert "caveman_default = true" in rendered_on
    # The always-on pointer must still preserve the normal-prose carve-outs.
    assert "never caveman" in rendered_on


def test_grill_me_skill_renders_as_planning_interview() -> None:
    """The grill-me skill ships as a model-invocable planning-interview skill."""
    rendered = render_template("skills/grill_me/SKILL.md.j2", _default_context())
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


def test_rules_body_grill_me_pointer_is_membership_gated() -> None:
    """The rules body mentions grill-me only when it is in included_skills."""
    with_grill = _default_context()
    rendered_on = render_template("rules/AGENTS.md.j2", with_grill)
    assert "grill-me" in rendered_on.lower()
    assert "Planning aids" in rendered_on

    without_grill = _default_context()
    without_grill["included_skills"] = [s for s in _ALL_SKILLS if s != "grill_me"]
    rendered_off = render_template("rules/AGENTS.md.j2", without_grill)
    assert "Planning aids" not in rendered_off


def test_rules_body_grill_me_default_switches_pointer_wording() -> None:
    """grill_me_default flips the pointer between off-by-default and always-on."""
    off = _default_context()
    off["grill_me_default"] = False
    rendered_off = render_template("rules/AGENTS.md.j2", off)
    assert "off by default" in rendered_off
    assert "on by default during planning for this project" not in rendered_off

    on = _default_context()
    on["grill_me_default"] = True
    rendered_on = render_template("rules/AGENTS.md.j2", on)
    assert "on by default during planning for this project" in rendered_on
    assert "grill_me_default = true" in rendered_on


def test_issue_comments_skill_documents_triage_rules() -> None:
    """The new iflow-comments skill must describe triage rules and buckets."""
    ctx = enrich_render_context(_default_context(), "skills/iflow_comments/SKILL.md.j2")
    rendered = render_template("skills/iflow_comments/SKILL.md.j2", ctx)
    # Frontmatter identity.
    assert "name: iflow-comments" in rendered
    assert "disable-model-invocation: true" in rendered
    # Chronological precedence (later wins) is called out.
    lowered = rendered.lower()
    assert "chronological" in lowered
    assert "later" in lowered
    # All three buckets are named.
    assert "Additional tasks" in rendered
    assert "Clarifications" in rendered
    assert "Superseded" in rendered
    # The output contract header matches exactly what /iflow-init expects.
    assert "## Comments (curated summary)" in rendered
    # Noise-filtering guidance exists.
    assert "bot" in lowered
    # Zero-comment edge case is handled.
    assert "zero comments" in lowered or "skip the whole section" in lowered


def test_iflow_plan_skill_includes_reasoning_directive() -> None:
    ctx = enrich_render_context(_default_context(), "skills/iflow_plan/SKILL.md.j2")
    rendered = render_template("skills/iflow_plan/SKILL.md.j2", ctx)
    assert "### MODEL & EXECUTION DIRECTIVE" in rendered
    assert "Profile: reasoning" in rendered


def test_iflow_init_skill_includes_economy_directive() -> None:
    ctx = enrich_render_context(_default_context(), "skills/iflow_init/SKILL.md.j2")
    rendered = render_template("skills/iflow_init/SKILL.md.j2", ctx)
    assert "### MODEL & EXECUTION DIRECTIVE" in rendered
    assert "Profile: economy" in rendered


def test_step_directives_off_omits_directive_block() -> None:
    ctx = enrich_render_context(_default_context(), "skills/iflow_plan/SKILL.md.j2")
    ctx["step_directives"] = False
    rendered = render_template("skills/iflow_plan/SKILL.md.j2", ctx)
    assert "MODEL & EXECUTION DIRECTIVE" not in rendered


def test_iflow_pick_includes_model_label_block_when_enabled() -> None:
    ctx = _default_context()
    ctx["model_label_flows"] = True
    ctx = enrich_render_context(ctx, "skills/iflow_pick/SKILL.md.j2")
    rendered = render_template("skills/iflow_pick/SKILL.md.j2", ctx)
    assert "Label-driven model profile" in rendered
    assert "deep_model_label" in rendered


def test_is_skill_template_matches_skill_manifest_paths() -> None:
    assert is_skill_template("skills/iflow_init/SKILL.md.j2")
    assert is_skill_template("skills/caveman/SKILL.md.j2")
    assert not is_skill_template("commands/iflow-init.md.j2")
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
    rendered = render_template("skills/iflow_init/SKILL.md.j2", _default_context())
    assert f"issue-flow-version: {ISSUE_FLOW_VERSION}" in rendered


def test_render_template_does_not_stamp_commands() -> None:
    rendered = render_template("commands/iflow-init.md.j2", _default_context())
    assert "issue-flow-version:" not in rendered
