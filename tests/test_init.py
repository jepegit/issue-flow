"""Tests for issue_flow.init (the init command)."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from issue_flow import dependencies as deps_module
from issue_flow import init as init_module
from issue_flow.dependencies import REQUIRED_DEPENDENCIES
from issue_flow.init import run_init


def test_init_creates_dotenv_with_commented_keys(tmp_path: Path) -> None:
    """init should create .env with commented ISSUEFLOW_* defaults when absent."""
    run_init(tmp_path)

    env_file = tmp_path / ".env"
    assert env_file.is_file()
    text = env_file.read_text(encoding="utf-8")
    assert "# ISSUEFLOW_DIR=.issueflows" in text
    assert "# ISSUEFLOW_AGENT_DIR=.cursor" in text
    assert "# ISSUEFLOW_DOCS_DIR=docs" in text
    assert "# ISSUEFLOW_HISTORY_FILE=HISTORY.md" in text


def test_init_second_run_skips_dotenv_when_keys_documented(tmp_path: Path) -> None:
    """Re-running init should not append duplicate ISSUEFLOW_* hints."""
    run_init(tmp_path)
    first = (tmp_path / ".env").read_text(encoding="utf-8")

    run_init(tmp_path)
    second = (tmp_path / ".env").read_text(encoding="utf-8")

    assert first == second


def test_init_appends_missing_dotenv_keys(tmp_path: Path) -> None:
    """If .env exists without ISSUEFLOW_* lines, init should append commented hints."""
    (tmp_path / ".env").write_text("OTHER=1\n", encoding="utf-8")

    run_init(tmp_path)

    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert text.startswith("OTHER=1\n")
    assert "issue-flow: optional environment" in text
    assert "# ISSUEFLOW_DIR=.issueflows" in text
    assert "# ISSUEFLOW_AGENT_DIR=.cursor" in text
    assert "# ISSUEFLOW_DOCS_DIR=docs" in text
    assert "# ISSUEFLOW_HISTORY_FILE=HISTORY.md" in text


def test_init_force_does_not_wipe_custom_dotenv(tmp_path: Path) -> None:
    """init --force must not replace an existing .env wholesale."""
    run_init(tmp_path)
    env_file = tmp_path / ".env"
    custom = (
        "MY_SECRET=keep-me\n"
        "# ISSUEFLOW_DIR=.issueflows\n"
        "# ISSUEFLOW_AGENT_DIR=.cursor\n"
        "# ISSUEFLOW_DOCS_DIR=docs\n"
        "# ISSUEFLOW_HISTORY_FILE=HISTORY.md\n"
    )
    env_file.write_text(custom, encoding="utf-8")

    run_init(tmp_path, force=True)

    assert "MY_SECRET=keep-me" in env_file.read_text(encoding="utf-8")


def test_init_creates_directories(tmp_path: Path) -> None:
    """Running init should create .issueflows/ with all five subdirectories."""
    run_init(tmp_path)

    issueflows = tmp_path / ".issueflows"
    assert issueflows.is_dir()
    assert (issueflows / "00-tools").is_dir()
    assert (issueflows / "01-current-issues").is_dir()
    assert (issueflows / "02-partly-solved-issues").is_dir()
    assert (issueflows / "03-solved-issues").is_dir()
    assert (issueflows / "04-designs-and-guides").is_dir()


def test_init_creates_gitkeep_files(tmp_path: Path) -> None:
    """Each .issueflows/ subdirectory should contain a .gitkeep file."""
    run_init(tmp_path)

    issueflows = tmp_path / ".issueflows"
    for subdir in [
        "00-tools",
        "01-current-issues",
        "02-partly-solved-issues",
        "03-solved-issues",
        "04-designs-and-guides",
    ]:
        gitkeep = issueflows / subdir / ".gitkeep"
        assert gitkeep.is_file(), f"{subdir}/.gitkeep should exist"


def test_init_creates_project_brief(tmp_path: Path) -> None:
    """init should create the durable project brief when missing."""
    run_init(tmp_path)

    brief = tmp_path / ".issueflows" / "04-designs-and-guides" / "this-project.md"
    assert brief.is_file()
    text = brief.read_text(encoding="utf-8")
    assert "# " in text
    assert "What this project is" in text
    assert "How to run / test" in text


def test_init_preserves_existing_project_brief(tmp_path: Path) -> None:
    """Re-running init should not overwrite the hand-editable project brief."""
    run_init(tmp_path)
    brief = tmp_path / ".issueflows" / "04-designs-and-guides" / "this-project.md"
    custom = "# Custom project brief\n\nKeep this content.\n"
    brief.write_text(custom, encoding="utf-8")

    run_init(tmp_path)

    assert brief.read_text(encoding="utf-8") == custom


def test_init_force_preserves_existing_project_brief(tmp_path: Path) -> None:
    """Even init --force should not clobber the user-owned project brief."""
    run_init(tmp_path)
    brief = tmp_path / ".issueflows" / "04-designs-and-guides" / "this-project.md"
    custom = "# Custom project brief\n\nKeep this content under force.\n"
    brief.write_text(custom, encoding="utf-8")

    run_init(tmp_path, force=True)

    assert brief.read_text(encoding="utf-8") == custom


def test_init_creates_tools_readme(tmp_path: Path) -> None:
    """init should seed the 00-tools README index when missing."""
    run_init(tmp_path)

    readme = tmp_path / ".issueflows" / "00-tools" / "README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "00-tools" in text
    assert "Tool index" in text
    assert "Check here first" in text


def test_init_preserves_existing_tools_readme(tmp_path: Path) -> None:
    """Re-running init must not overwrite the agent-grown tools index."""
    run_init(tmp_path)
    readme = tmp_path / ".issueflows" / "00-tools" / "README.md"
    custom = "# My toolbox\n\n| dedupe.py | drops dups | always |\n"
    readme.write_text(custom, encoding="utf-8")

    run_init(tmp_path)

    assert readme.read_text(encoding="utf-8") == custom


def test_init_force_preserves_existing_tools_readme(tmp_path: Path) -> None:
    """Even init --force must not clobber the user-owned tools index."""
    run_init(tmp_path)
    readme = tmp_path / ".issueflows" / "00-tools" / "README.md"
    custom = "# My toolbox under force\n\nKeep me.\n"
    readme.write_text(custom, encoding="utf-8")

    run_init(tmp_path, force=True)

    assert readme.read_text(encoding="utf-8") == custom


def test_init_start_skill_documents_toolbox_and_upfront_status(tmp_path: Path) -> None:
    """iflow-start skill should nudge toolbox reuse and up-front status seeding."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "skills" / "iflow-start" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "00-tools" in content
    # Status file is seeded before code, not just at close.
    assert "Seed the status file up front" in content


def test_init_plan_skill_documents_toolbox_prior_art(tmp_path: Path) -> None:
    """iflow-plan skill prior-art discovery should check the tools folder."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "skills" / "iflow-plan" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "00-tools" in content


def test_init_cursor_is_skills_first(tmp_path: Path) -> None:
    """Running init should create Cursor skills, not Cursor command files."""
    run_init(tmp_path)

    assert not (tmp_path / ".cursor" / "commands").exists()
    skills_dir = tmp_path / ".cursor" / "skills"
    assert (skills_dir / "iflow" / "SKILL.md").is_file()
    assert (skills_dir / "iflow-init" / "SKILL.md").is_file()
    assert (skills_dir / "iflow-start" / "SKILL.md").is_file()
    assert (skills_dir / "iflow-close" / "SKILL.md").is_file()


def test_init_creates_cursor_skills(tmp_path: Path) -> None:
    """Running init should create bundled Agent Skills under .cursor/skills/."""
    run_init(tmp_path)

    skills = tmp_path / ".cursor" / "skills"
    for name in (
        "iflow",
        "iflow-init",
        "iflow-start",
        "iflow-close",
        "iflow-version-bump",
        "iflow-history-update",
    ):
        skill_file = skills / name / "SKILL.md"
        assert skill_file.is_file(), f"expected {skill_file}"
        text = skill_file.read_text(encoding="utf-8")
        assert text.startswith("---")
        assert f"name: {name}" in text
        assert "disable-model-invocation: true" in text


def test_init_creates_cursor_rule(tmp_path: Path) -> None:
    run_init(tmp_path)
    rule = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    assert rule.is_file()
    content = rule.read_text(encoding="utf-8")
    assert "alwaysApply: false" in content
    assert "**/*" in content
    assert ".issueflows" in content


def test_init_creates_docs(tmp_path: Path) -> None:
    run_init(tmp_path)
    doc = tmp_path / "docs" / "issue-workflow.md"
    assert doc.is_file()
    content = doc.read_text(encoding="utf-8")
    assert "/iflow-init" in content
    assert ".issueflows" in content


def test_init_idempotent_skips_existing(tmp_path: Path) -> None:
    """Running init twice should skip files that already exist (no overwrite)."""
    run_init(tmp_path)

    # Tamper with a file so we can verify it was NOT overwritten
    rule_file = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    rule_file.write_text("custom content", encoding="utf-8")

    run_init(tmp_path)

    assert rule_file.read_text(encoding="utf-8") == "custom content"


def test_init_force_overwrites(tmp_path: Path) -> None:
    """Running init with force=True should overwrite existing files."""
    run_init(tmp_path)

    rule_file = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    rule_file.write_text("custom content", encoding="utf-8")

    run_init(tmp_path, force=True)

    content = rule_file.read_text(encoding="utf-8")
    assert content != "custom content"
    assert "alwaysApply: false" in content
    assert "**/*" in content


def test_init_templates_reference_issueflows_dir(tmp_path: Path) -> None:
    """Generated workflow skills should reference .issueflows/ paths."""
    run_init(tmp_path)

    skills_dir = tmp_path / ".cursor" / "skills"
    for name in ["iflow-init", "iflow-start", "iflow-close"]:
        content = (skills_dir / name / "SKILL.md").read_text(encoding="utf-8")
        assert ".issueflows/" in content, f"{name} should reference .issueflows/"


def test_init_issue_close_documents_version_bump(tmp_path: Path) -> None:
    """iflow-close skill should describe optional uv semver bump before commit/PR."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "skills" / "iflow-close" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "uv version --bump" in content
    assert "iflow-version-bump" in content


def test_init_version_bump_skill_documents_all_levels_and_default(
    tmp_path: Path,
) -> None:
    """version-bump skill should list every uv level and the pre-release default."""
    run_init(tmp_path)
    content = (
        tmp_path / ".cursor" / "skills" / "iflow-version-bump" / "SKILL.md"
    ).read_text(encoding="utf-8")
    for level in (
        "major",
        "minor",
        "patch",
        "stable",
        "alpha",
        "beta",
        "rc",
        "post",
        "dev",
    ):
        assert level in content, f"version-bump skill should mention {level}"
    # Pre-release-aware default when no level is given.
    assert "pre-release-aware default" in content
    assert "alpha" in content and "beta" in content


def test_init_version_bump_skill_documents_release_strategies(
    tmp_path: Path,
) -> None:
    """version-bump skill resolves the release strategy: brief, detection, tag path."""
    run_init(tmp_path)
    content = (
        tmp_path / ".cursor" / "skills" / "iflow-version-bump" / "SKILL.md"
    ).read_text(encoding="utf-8")
    # Resolution order: the project brief's release section wins...
    assert "Release & version bump" in content
    assert "this-project.md" in content
    # ...then detection from pyproject.toml...
    assert 'dynamic = ["version"]' in content
    assert "setuptools_scm" in content
    # ...and the tag-derived path defers tagging until after the merge.
    assert "planned" in content.lower()
    assert "git tag" in content
    assert "gh release create" in content
    assert "never tag an issue-branch commit" in content.lower()
    # The static path is unchanged.
    assert "uv version --bump" in content
    # Self-healing: discovered strategies get recorded in the brief.
    assert "Record what you learn" in content


def test_init_project_brief_documents_release_section(tmp_path: Path) -> None:
    """The starter project brief should carry a Release & version bump section."""
    run_init(tmp_path)
    brief = (
        tmp_path / ".issueflows" / "04-designs-and-guides" / "this-project.md"
    ).read_text(encoding="utf-8")
    assert "## Release & version bump" in brief
    assert "uv version --bump" in brief
    assert "gh release create" in brief


def test_init_close_skill_defers_tag_creation(tmp_path: Path) -> None:
    """iflow-close should plan (not create) tags for tag-derived projects."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "skills" / "iflow-close" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "release strategy" in content
    assert "Git-tag derived" in content
    assert "planned tag" in content


def test_init_cleanup_skill_offers_planned_tag(tmp_path: Path) -> None:
    """iflow-cleanup's consolidated confirm should cover the planned release tag."""
    run_init(tmp_path)
    content = (
        tmp_path / ".cursor" / "skills" / "iflow-cleanup" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "Planned release tag" in content
    assert "git tag -l" in content


def test_init_close_skill_documents_prerelease_default(tmp_path: Path) -> None:
    """iflow-close skill should describe the pre-release-aware default bump."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "skills" / "iflow-close" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "pre-release-aware default" in content
    # The named-level list should include a pre-release level.
    assert "beta" in content


def test_init_issue_close_documents_history_update_step(tmp_path: Path) -> None:
    """iflow-close skill should describe the HISTORY.md update step and opt-out token."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "skills" / "iflow-close" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "HISTORY.md" in content
    assert "iflow-history-update" in content
    assert "[Unreleased]" in content
    assert "nohistory" in content


def test_init_issue_close_documents_uncommitted_and_branch_reminder(
    tmp_path: Path,
) -> None:
    """iflow-close skill should flag unrelated changes and document post-PR switching."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "skills" / "iflow-close" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "git status" in content
    assert "not relevant" in content
    assert "issue branch" in content
    assert "stay on branch" in content
    assert "don't switch" in content
    assert "git switch <default>" in content
    assert "git status --porcelain" in content


def test_init_close_skill_mentions_switchback_fast_path(tmp_path: Path) -> None:
    """iflow-close skill should offer `issue-flow agent switchback` as fast path."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "skills" / "iflow-close" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "issue-flow agent switchback" in content


def test_init_rule_documents_designs_folder(tmp_path: Path) -> None:
    """The generated rule file should mention the designs-and-guides folder."""
    run_init(tmp_path)
    rule = (tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc").read_text(
        encoding="utf-8"
    )
    assert "04-designs-and-guides" in rule
    assert "Designs and guides" in rule


def test_init_commands_reference_designs_folder(tmp_path: Path) -> None:
    """/iflow-plan, /iflow-start, and /iflow-close skills should reference the designs folder."""
    run_init(tmp_path)
    skills_dir = tmp_path / ".cursor" / "skills"
    for name in ("iflow-plan", "iflow-start", "iflow-close"):
        content = (skills_dir / name / "SKILL.md").read_text(encoding="utf-8")
        assert "04-designs-and-guides" in content, (
            f"{name} should reference the designs-and-guides folder"
        )


def test_init_issue_init_documents_branch_inference(tmp_path: Path) -> None:
    """iflow-init skill should describe resolving an issue from the current branch when no args."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "skills" / "iflow-init" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "git -C <project_root> branch --show-current" in content
    assert "You have not provided an issue reference" in content
    assert "issue-style branch" in content


def test_init_proceeds_silently_when_all_dependencies_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With all deps present the check should not prompt or abort."""
    monkeypatch.setattr(
        init_module, "check_dependencies", lambda: list(REQUIRED_DEPENDENCIES[:0])
    )

    def fail_confirm(*_a: object, **_kw: object) -> bool:
        raise AssertionError("typer.confirm should not be called when all deps present")

    monkeypatch.setattr(typer, "confirm", fail_confirm)

    run_init(tmp_path)

    assert (tmp_path / ".cursor" / "skills" / "iflow-init" / "SKILL.md").is_file()


def test_init_continues_when_skip_dep_check_is_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``skip_dep_check=True`` must bypass the prompt even if deps are missing."""
    monkeypatch.setattr(
        init_module, "check_dependencies", lambda: list(REQUIRED_DEPENDENCIES)
    )

    def fail_confirm(*_a: object, **_kw: object) -> bool:
        raise AssertionError("typer.confirm must not run when --skip-dep-check is set")

    monkeypatch.setattr(typer, "confirm", fail_confirm)

    run_init(tmp_path, skip_dep_check=True)

    assert (tmp_path / ".cursor" / "skills" / "iflow-init" / "SKILL.md").is_file()


def test_init_continues_in_non_tty_when_deps_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-interactive stdin (CI) must auto-skip the prompt."""
    monkeypatch.setattr(
        init_module, "check_dependencies", lambda: list(REQUIRED_DEPENDENCIES)
    )
    monkeypatch.setattr(deps_module.sys.stdin, "isatty", lambda: False)

    def fail_confirm(*_a: object, **_kw: object) -> bool:
        raise AssertionError("typer.confirm must not run on non-TTY stdin")

    monkeypatch.setattr(typer, "confirm", fail_confirm)

    run_init(tmp_path)

    assert (tmp_path / ".cursor" / "skills" / "iflow-init" / "SKILL.md").is_file()


def test_init_aborts_cleanly_when_user_declines_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A decline at the prompt must raise typer.Exit and leave no scaffold behind."""
    monkeypatch.setattr(
        init_module, "check_dependencies", lambda: list(REQUIRED_DEPENDENCIES)
    )
    monkeypatch.setattr(deps_module.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(typer, "confirm", lambda *_a, **_kw: False)

    with pytest.raises(typer.Exit) as exc_info:
        run_init(tmp_path)

    assert exc_info.value.exit_code == 1
    assert not (tmp_path / ".cursor").exists()
    assert not (tmp_path / ".issueflows").exists()


def test_init_calls_graphify_register_when_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When graphify is on PATH, run_init must call register_with_cursor."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(
        graphify_module.shutil,
        "which",
        lambda cmd: "/usr/bin/graphify" if cmd == "graphify" else None,
    )

    calls: list[Path] = []

    class _Result:
        returncode = 0
        stderr = ""

    def fake_run(cmd: list[str], **kwargs: object) -> _Result:
        calls.append(kwargs.get("cwd"))  # type: ignore[arg-type]
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)

    run_init(tmp_path)

    assert calls == [tmp_path]


def test_init_skips_graphify_when_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When graphify is missing, run_init must not call subprocess and must still succeed."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)

    def fail_run(*_a: object, **_kw: object) -> object:
        raise AssertionError(
            "subprocess.run must not be called when graphify is missing"
        )

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)

    run_init(tmp_path)

    assert (tmp_path / ".cursor" / "skills" / "iflow-graphify" / "SKILL.md").is_file()


def test_init_creates_graphify_skill(tmp_path: Path) -> None:
    """The /graphify skill must be scaffolded for Cursor."""
    run_init(tmp_path)

    graphify_skill = tmp_path / ".cursor" / "skills" / "iflow-graphify" / "SKILL.md"
    assert not (tmp_path / ".cursor" / "commands").exists()
    assert graphify_skill.is_file()

    skill_content = graphify_skill.read_text(encoding="utf-8")
    assert "name: iflow-graphify" in skill_content
    assert "issue-flow graphify" in skill_content
    assert "graphify-out" in skill_content
    assert "disable-model-invocation: true" in skill_content


def test_init_creates_status_skill(tmp_path: Path) -> None:
    """The /iflow-status skill must be scaffolded for Cursor."""
    run_init(tmp_path)

    status_skill = tmp_path / ".cursor" / "skills" / "iflow-status" / "SKILL.md"
    assert status_skill.is_file()

    skill_content = status_skill.read_text(encoding="utf-8")
    assert "name: iflow-status" in skill_content
    assert "/iflow-status" in skill_content
    assert "read-only" in skill_content.lower()
    assert "off-path" in skill_content.lower()
    assert "disable-model-invocation: true" in skill_content


def test_init_creates_issue_pick_skill(tmp_path: Path) -> None:
    """The /iflow-pick front-door skill must be scaffolded for Cursor."""
    run_init(tmp_path)

    pick_skill = tmp_path / ".cursor" / "skills" / "iflow-pick" / "SKILL.md"
    assert pick_skill.is_file()

    skill_content = pick_skill.read_text(encoding="utf-8")
    assert "name: iflow-pick" in skill_content
    assert "/iflow-pick" in skill_content
    assert "/iflow-init" in skill_content
    assert ".issueflows/" in skill_content
    assert "disable-model-invocation: true" in skill_content


def test_init_rule_documents_knowledge_graph_section(tmp_path: Path) -> None:
    """The generated rule file should mention the optional graphify knowledge graph."""
    run_init(tmp_path)
    rule = (tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc").read_text(
        encoding="utf-8"
    )
    assert "Knowledge graph" in rule
    assert "graphify-out/GRAPH_REPORT.md" in rule
    assert "/iflow-graphify" in rule


_AGENTS_BEGIN = "<!-- BEGIN issue-flow (managed: do not edit this block) -->"
_AGENTS_END = "<!-- END issue-flow (managed) -->"


def test_init_creates_agents_md_with_managed_block(tmp_path: Path) -> None:
    """init writes AGENTS.md containing the issue-flow managed block."""
    run_init(tmp_path)

    agents = tmp_path / "AGENTS.md"
    assert agents.is_file()
    content = agents.read_text(encoding="utf-8")
    assert _AGENTS_BEGIN in content
    assert _AGENTS_END in content
    assert "Issue-flow best practices" in content
    # AGENTS.md is editor-neutral: no literal "Cursor".
    assert "Cursor" not in content


def test_init_preserves_existing_agents_md_user_content(tmp_path: Path) -> None:
    """A hand-maintained AGENTS.md keeps its content; the block is appended."""
    agents = tmp_path / "AGENTS.md"
    user_text = "# My project\n\nHand-written guidance that must survive.\n"
    agents.write_text(user_text, encoding="utf-8")

    run_init(tmp_path)

    content = agents.read_text(encoding="utf-8")
    assert content.startswith("# My project")
    assert "Hand-written guidance that must survive." in content
    assert _AGENTS_BEGIN in content
    assert "Issue-flow best practices" in content


def test_init_agents_md_block_is_idempotent(tmp_path: Path) -> None:
    """Re-running init must not duplicate the managed block."""
    run_init(tmp_path)
    first = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")

    run_init(tmp_path)
    second = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")

    assert first == second
    assert second.count(_AGENTS_BEGIN) == 1


def test_init_claude_editor_writes_claude_tree_and_claude_md(tmp_path: Path) -> None:
    """--editor claude scaffolds under .claude/ with a CLAUDE.md rules file."""
    run_init(tmp_path, editors=["claude"])

    assert (tmp_path / ".claude" / "commands" / "iflow-init.md").is_file()
    assert (tmp_path / ".claude" / "skills" / "iflow-init" / "SKILL.md").is_file()
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / "AGENTS.md").is_file()
    # No Cursor scaffolding leaks in.
    assert not (tmp_path / ".cursor").exists()


def test_init_codex_editor_has_skills_but_no_commands(tmp_path: Path) -> None:
    """--editor codex scaffolds skills + AGENTS.md but no slash commands."""
    run_init(tmp_path, editors=["codex"])

    assert (tmp_path / ".codex" / "skills" / "iflow-init" / "SKILL.md").is_file()
    assert not (tmp_path / ".codex" / "commands").exists()
    assert not (tmp_path / ".codex" / "command").exists()
    assert (tmp_path / "AGENTS.md").is_file()
    # Codex has no .mdc / CLAUDE.md extra.
    assert not (tmp_path / "CLAUDE.md").exists()


def test_init_opencode_editor_uses_singular_command_dir(tmp_path: Path) -> None:
    run_init(tmp_path, editors=["opencode"])

    assert (tmp_path / ".opencode" / "command" / "iflow-init.md").is_file()
    assert not (tmp_path / ".opencode" / "commands").exists()
    assert (tmp_path / ".opencode" / "skills" / "iflow" / "SKILL.md").is_file()


def test_init_all_editors_scaffolds_every_agent_dir(tmp_path: Path) -> None:
    run_init(tmp_path, editors=["all"])

    assert not (tmp_path / ".cursor" / "commands").exists()
    assert (tmp_path / ".cursor" / "skills" / "iflow-init" / "SKILL.md").is_file()
    assert (tmp_path / ".claude" / "commands" / "iflow-init.md").is_file()
    assert (tmp_path / ".opencode" / "command" / "iflow-init.md").is_file()
    assert (tmp_path / ".codex" / "skills" / "iflow-init" / "SKILL.md").is_file()
    # Shared, neutral outputs exist exactly once.
    assert (tmp_path / "AGENTS.md").is_file()
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.count(_AGENTS_BEGIN) == 1


def test_init_unknown_editor_exits_cleanly(tmp_path: Path) -> None:
    """An unknown --editor value aborts with a non-zero exit and no scaffold."""
    with pytest.raises(typer.Exit) as exc_info:
        run_init(tmp_path, editors=["sublime"])

    assert exc_info.value.exit_code == 2
    assert not (tmp_path / ".issueflows").exists()


def test_init_default_mode_is_full_and_writes_no_config(tmp_path: Path) -> None:
    """Without --mode, init scaffolds the full set and writes no config.toml."""
    run_init(tmp_path)

    skills = tmp_path / ".cursor" / "skills"
    assert (skills / "iflow-close" / "SKILL.md").is_file()
    assert (skills / "iflow-yolo" / "SKILL.md").is_file()
    # Default mode leaves the persisted config untouched (back-compat).
    assert not (tmp_path / ".issueflows" / "config.toml").exists()


def test_init_mode_simple_scaffolds_subset(tmp_path: Path) -> None:
    run_init(tmp_path, mode="simple")

    skills = tmp_path / ".cursor" / "skills"
    for present in (
        "iflow",
        "iflow-init",
        "iflow-plan",
        "iflow-start",
        "iflow-pause",
        "iflow-status",
    ):
        assert (skills / present / "SKILL.md").is_file(), present
    for absent in (
        "iflow-close",
        "iflow-cleanup",
        "iflow-yolo",
        "iflow-fix",
        "iflow-graphify",
        "iflow-pick",
    ):
        assert not (skills / absent).exists(), absent

    config = tmp_path / ".issueflows" / "config.toml"
    assert 'mode = "simple"' in config.read_text(encoding="utf-8")


def test_init_switch_to_simple_prunes_excluded_skills(tmp_path: Path) -> None:
    """Switching standard -> simple removes the now-excluded skills."""
    run_init(tmp_path)
    close = tmp_path / ".cursor" / "skills" / "iflow-close"
    assert close.is_dir()

    run_init(tmp_path, mode="simple", force=True)

    assert not close.exists()
    assert (tmp_path / ".cursor" / "skills" / "iflow-init" / "SKILL.md").is_file()


def test_init_unknown_mode_aborts_without_scaffold(tmp_path: Path) -> None:
    with pytest.raises(typer.Exit) as exc_info:
        run_init(tmp_path, mode="nope")

    assert exc_info.value.exit_code == 2
    assert not (tmp_path / ".cursor").exists()


def test_init_simple_mode_dispatcher_has_no_close_target(tmp_path: Path) -> None:
    """The /iflow dispatcher's done-state must not route to /iflow-close in simple mode."""
    run_init(tmp_path, mode="simple")
    dispatcher = (tmp_path / ".cursor" / "skills" / "iflow" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    # The close-dispatch reason line is gated out; the markdown-only fallback is in.
    assert "status marks the issue" not in dispatcher
    assert "03-solved-issues" in dispatcher


def test_init_standard_mode_dispatcher_routes_to_close(tmp_path: Path) -> None:
    """Standard mode keeps the /iflow-close dispatch in the done state."""
    run_init(tmp_path)
    dispatcher = (tmp_path / ".cursor" / "skills" / "iflow" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "status marks the issue" in dispatcher


def test_init_detects_project_name(tmp_path: Path) -> None:
    """If a pyproject.toml exists, its name should appear in the rule file."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')

    run_init(tmp_path)

    rule = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    content = rule.read_text(encoding="utf-8")
    assert "test-project" in content
