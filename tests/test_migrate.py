"""``issue-flow update`` migrates a pre-#406 scaffold in one run.

The fixture builds what an older release left on disk: thirty skill folders,
full command copies for Claude Code, a canonical snapshot, user-global copies,
config stems that no longer exist, and an older Linguist block. One
``run_update`` must leave only the merged surface behind, keep anything the
user edited, and rewrite the config so the CLI resolves cleanly.
"""

from __future__ import annotations

from pathlib import Path

import tomllib

from issue_flow.init import run_update
from issue_flow.migrate import migrate_config_stems
from issue_flow.skill_ownership import (
    hash_skill_text,
    save_stamp,
    save_stamp_hash,
    user_global_stamp_key,
)
from issue_flow.surfaces import _LINGUIST_MARKER_BEGIN, _LINGUIST_MARKER_END
from issue_flow.user_global import (
    editor_user_global_skills_root,
    user_global_skill_stamp_path,
)

OLD_SKILLS = (
    "iflow-capture",
    "iflow-comments",
    "iflow-init",
    "iflow-yolo",
    "iflow-cycle",
    "iflow-auto",
    "iflow-drive",
    "iflow-fix",
    "iflow-epic",
    "iflow-split",
    "iflow-review",
    "iflow-doctor",
    "iflow-workspace-git",
    "iflow-graphify",
    "iflow-archive",
    "iflow-pr-sync",
    "iflow-ops",
    "iflow-version-bump",
    "iflow-history-update",
    "gh-ci",
)
OLD_COMMANDS = (
    "iflow",
    "iflow-plan",
    "iflow-capture",
    "iflow-yolo",
    "iflow-epic",
    "iflow-workspace-git",
)


def _old_skill(skill_dir: Path, project_root: Path | None = None) -> str:
    """Write an issue-flow-looking skill; stamp it in the project store."""
    text = f"---\nname: {skill_dir.name}\nissue-flow-version: 0.9.0\n---\n\nold\n"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")
    if project_root is not None:
        save_stamp(project_root, ".issueflows", skill_dir, hash_skill_text(text))
    return text


def _old_project(root: Path) -> None:
    (root / ".issueflows").mkdir()
    (root / ".issueflows" / "config.toml").write_text(
        "[issueflow]\n"
        'mode = "lean"\n'
        "linguist_attributes = true\n"
        "\n"
        "[issueflow.step_profiles]\n"
        'iflow_capture = "reasoning"\n'
        'iflow_cycle = "economy"\n'
        "\n"
        "# my custom mode\n"
        "[modes.lean]\n"
        'extends = "standard"\n'
        'remove = ["iflow_yolo", "iflow_cycle", "iflow_auto", "iflow_drive", "gh_ci",'
        ' "iflow-yolo", "iflow-cycle", "iflow-auto", "iflow-drive"]\n',
        encoding="utf-8",
    )
    for editor in (".cursor", ".claude"):
        for name in OLD_SKILLS:
            _old_skill(root / editor / "skills" / name, root)
    for name in OLD_COMMANDS:
        path = root / ".claude" / "commands" / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("old command copy\n", encoding="utf-8")
    (root / ".claude" / "commands" / "my-own.md").write_text("mine\n", encoding="utf-8")
    for name in ("iflow-yolo", "iflow-capture"):
        _old_skill(root / ".issueflows" / "agent" / "skills" / name, root)
    (root / ".gitattributes").write_text(
        f"*.png binary\n\n{_LINGUIST_MARKER_BEGIN}\nold block\n{_LINGUIST_MARKER_END}\n",
        encoding="utf-8",
    )


def test_update_migrates_an_old_scaffold_in_one_run(tmp_path: Path) -> None:
    _old_project(tmp_path)
    # A retired skill the user edited after issue-flow wrote it stays put.
    edited = tmp_path / ".cursor" / "skills" / "iflow-fix" / "SKILL.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "my notes\n", encoding="utf-8")

    run_update(tmp_path, editors=["cursor", "claude"])

    for editor in (".cursor", ".claude"):
        skills = tmp_path / editor / "skills"
        for name in OLD_SKILLS:
            if editor == ".cursor" and name == "iflow-fix":
                continue
            assert not (skills / name).exists(), (editor, name)
        assert (skills / "iflow-pick" / "capture.md").is_file()
        assert (skills / "iflow-close" / "ci.md").is_file()
        # The custom mode removed the hands-off runs (old stems, mapped).
        assert not (skills / "iflow-run").exists()
    assert edited.is_file()
    assert edited.read_text(encoding="utf-8").endswith("my notes\n")

    commands = tmp_path / ".claude" / "commands"
    assert sorted(p.name for p in commands.iterdir()) == ["my-own.md"]

    canonical = tmp_path / ".issueflows" / "agent" / "skills"
    assert not (canonical / "iflow-yolo").exists()
    assert not (canonical / "iflow-capture").exists()

    config = (tmp_path / ".issueflows" / "config.toml").read_text(encoding="utf-8")
    data = tomllib.loads(config)
    # All four run modes removed -> iflow-run goes; gh_ci alone never removes close.
    assert data["modes"]["lean"]["remove"] == ["iflow_run", "iflow-run"]
    assert data["issueflow"]["step_profiles"] == {
        "iflow_pick": "reasoning",
        "iflow_run": "economy",
    }
    assert "# my custom mode" in config

    attributes = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
    assert attributes.startswith("*.png binary\n")
    assert "old block" not in attributes
    assert ".cursor/** linguist-generated" in attributes


def test_update_is_idempotent_after_migration(tmp_path: Path) -> None:
    _old_project(tmp_path)
    run_update(tmp_path, editors=["cursor"])
    config = (tmp_path / ".issueflows" / "config.toml").read_text(encoding="utf-8")
    snapshot = sorted(
        p.relative_to(tmp_path).as_posix() for p in (tmp_path / ".cursor").rglob("*")
    )

    run_update(tmp_path, editors=["cursor"])

    assert (tmp_path / ".issueflows" / "config.toml").read_text(encoding="utf-8") == config
    assert snapshot == sorted(
        p.relative_to(tmp_path).as_posix() for p in (tmp_path / ".cursor").rglob("*")
    )
    assert migrate_config_stems(tmp_path / ".issueflows" / "config.toml") == []


def test_update_prunes_stamped_user_global_retired_skills(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".issueflows").mkdir()
    root = editor_user_global_skills_root("cursor")
    assert root is not None
    stamps = user_global_skill_stamp_path()
    ours = _old_skill(root / "gh-ci")
    save_stamp_hash(stamps, user_global_stamp_key("cursor", "gh-ci"), hash_skill_text(ours))
    _old_skill(root / "iflow-init")  # no stamp: not provably ours

    run_update(project, editors=["cursor"])

    assert not (root / "gh-ci").exists()
    assert (root / "iflow-init").exists()
    assert (root / "iflow-setup" / "SKILL.md").is_file()
    assert (root / "iflow-setup" / "harness.md").is_file()


def test_doctor_reports_a_kept_retired_skill(tmp_path: Path) -> None:
    from issue_flow.agent import audit_unmanaged_editor_skills
    from issue_flow.config import Settings

    _old_skill(tmp_path / ".cursor" / "skills" / "iflow-yolo")
    (tmp_path / ".cursor" / "skills" / "my-notes").mkdir()

    findings = {f.code: f for f in audit_unmanaged_editor_skills(tmp_path, Settings())}

    assert findings["retired_editor_skill"].severity == "warn"
    assert "iflow-yolo" in findings["retired_editor_skill"].message
    assert "my-notes" in findings["unmanaged_editor_skill"].message
