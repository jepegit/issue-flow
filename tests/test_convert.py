"""Tests for issue_flow.convert and canonical scaffolding."""

from __future__ import annotations

from pathlib import Path

from issue_flow.convert import run_convert
from issue_flow.init import run_init
from issue_flow.templating import build_canonical_manifest, build_manifest
from issue_flow.editors import get_profile


def test_build_canonical_manifest_is_skill_only() -> None:
    manifest = build_canonical_manifest()
    cursor_manifest = build_manifest(get_profile("cursor"))
    assert all("agent/skills" in path for _, path in manifest)
    assert all(template.startswith("skills/") for template, _ in manifest)
    assert len(manifest) < len(cursor_manifest)


def test_init_canonical_creates_agent_store(tmp_path: Path) -> None:
    run_init(tmp_path, canonical=True, skip_dep_check=True)

    agent_skills = tmp_path / ".issueflows" / "agent" / "skills"
    assert agent_skills.is_dir()
    assert (agent_skills / "iflow-init" / "SKILL.md").is_file()
    assert (tmp_path / ".issueflows" / "agent" / "manifest.json").is_file()
    assert (tmp_path / "AGENTS.md").is_file()
    assert not (tmp_path / ".cursor").exists()

    config = (tmp_path / ".issueflows" / "config.toml").read_text(encoding="utf-8")
    assert "canonical_format = true" in config

    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".cursor/" in gitignore
    assert ".claude/" in gitignore


def test_convert_to_editor_materializes_cursor_tree(tmp_path: Path) -> None:
    run_init(tmp_path, canonical=True, skip_dep_check=True)

    run_convert(tmp_path, to="cursor", force=True)

    skills = tmp_path / ".cursor" / "skills" / "iflow-init" / "SKILL.md"
    assert skills.is_file()
    assert (tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc").is_file()


def test_convert_to_canonical_prunes_editor_dirs(tmp_path: Path) -> None:
    run_init(tmp_path, skip_dep_check=True)
    assert (tmp_path / ".cursor").exists()

    run_convert(tmp_path, to="canonical", force=True, prune_other=True)

    assert (
        tmp_path / ".issueflows" / "agent" / "skills" / "iflow-init" / "SKILL.md"
    ).is_file()
    assert not (tmp_path / ".cursor").exists()


def test_convert_prune_other_removes_sibling_editors(tmp_path: Path) -> None:
    run_init(tmp_path, editors=["cursor", "claude"], skip_dep_check=True)
    assert (tmp_path / ".cursor").exists()
    assert (tmp_path / ".claude").exists()

    run_convert(tmp_path, to="cursor", force=True, prune_other=True)

    assert (tmp_path / ".cursor").exists()
    assert not (tmp_path / ".claude").exists()
