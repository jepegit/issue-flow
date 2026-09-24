"""Where issue worktrees go: ``worktrees_dir`` / ``worktrees_in_workspace`` (#328)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from issue_flow import gitutils
from issue_flow.cli import app
from issue_flow.project import WORKSPACE_FILENAME


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _repo(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(path, "init", "-b", "main")
    _git(path, "config", "user.email", "t@example.com")
    _git(path, "config", "user.name", "tester")
    _git(path, "commit", "--allow-empty", "-m", "init")
    return path


@pytest.fixture(autouse=True)
def _no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ISSUEFLOW_WORKTREES_DIR", raising=False)
    monkeypatch.delenv("ISSUEFLOW_WORKTREES_IN_WORKSPACE", raising=False)


# --- resolver: one test per row of the plan's table ---------------------------


@pytest.mark.essential
def test_default_is_sibling(tmp_path: Path) -> None:
    loc = gitutils.resolve_worktree_location(tmp_path / "demo", 7)
    assert loc.path == (tmp_path / "demo-7").resolve()
    assert loc.reason == "sibling"
    assert loc.note is None


@pytest.mark.essential
def test_workspace_folder_keeps_sibling_even_with_worktrees_dir(tmp_path: Path) -> None:
    (tmp_path / WORKSPACE_FILENAME).write_text("[workspace]\n", encoding="utf-8")
    common = tmp_path / "elsewhere"
    common.mkdir()
    loc = gitutils.resolve_worktree_location(
        tmp_path / "demo", 7, worktrees_dir=str(common)
    )
    assert loc.path == (tmp_path / "demo-7").resolve()
    assert loc.reason == "workspace"


def test_workspace_opt_out_uses_worktrees_dir(tmp_path: Path) -> None:
    (tmp_path / WORKSPACE_FILENAME).write_text("[workspace]\n", encoding="utf-8")
    common = tmp_path / "common"
    common.mkdir()
    loc = gitutils.resolve_worktree_location(
        tmp_path / "demo", 7, worktrees_dir=str(common), in_workspace=False
    )
    assert loc.path == (common / "demo-7").resolve()
    assert loc.reason == "worktrees_dir"


@pytest.mark.essential
def test_existing_worktrees_dir_is_used(tmp_path: Path) -> None:
    common = tmp_path / "worktrees"
    common.mkdir()
    loc = gitutils.resolve_worktree_location(
        tmp_path / "projects" / "demo", 7, worktrees_dir=str(common)
    )
    assert loc.path == (common / "demo-7").resolve()
    assert loc.reason == "worktrees_dir"


def test_missing_worktrees_dir_falls_back_with_note(tmp_path: Path) -> None:
    loc = gitutils.resolve_worktree_location(
        tmp_path / "demo", 7, worktrees_dir=str(tmp_path / "nope")
    )
    assert loc.path == (tmp_path / "demo-7").resolve()
    assert loc.reason == "fallback"
    assert loc.note is not None and "does not exist" in loc.note
    assert not (tmp_path / "nope").exists(), "the folder must never be created"


def test_relative_worktrees_dir_falls_back_with_note(tmp_path: Path) -> None:
    loc = gitutils.resolve_worktree_location(
        tmp_path / "demo", 7, worktrees_dir="worktrees"
    )
    assert loc.reason == "fallback"
    assert loc.note is not None and "not an absolute path" in loc.note


def test_tilde_is_expanded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "worktrees").mkdir()
    loc = gitutils.resolve_worktree_location(
        tmp_path / "projects" / "demo", 7, worktrees_dir="~/worktrees"
    )
    assert loc.path == (tmp_path / "worktrees" / "demo-7").resolve()
    assert loc.reason == "worktrees_dir"


# --- end to end through the CLI --------------------------------------------------


def test_cli_add_and_remove_in_worktrees_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = _repo(tmp_path / "projects" / "demo")
    common = tmp_path / "worktrees"
    common.mkdir()
    monkeypatch.setenv("ISSUEFLOW_WORKTREES_DIR", str(common))
    runner = CliRunner()

    added = runner.invoke(
        app,
        ["agent", "worktree-add", "12", "--slug", "fix", "-C", str(home), "--json"],
    )
    assert added.exit_code == 0, added.output
    payload = json.loads(added.stdout)
    assert payload["path"] == str((common / "demo-12").resolve())
    assert payload["location"] == "worktrees_dir"
    assert payload["location_note"] is None
    assert (common / "demo-12").is_dir()
    assert not (tmp_path / "projects" / "demo-12").exists()

    removed = runner.invoke(
        app, ["agent", "worktree-remove", "12", "-C", str(home), "--json"]
    )
    assert removed.exit_code == 0, removed.output
    assert json.loads(removed.stdout)["removed"] is True
    assert not (common / "demo-12").exists()


def test_cli_reports_fallback_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = _repo(tmp_path / "demo")
    monkeypatch.setenv("ISSUEFLOW_WORKTREES_DIR", str(tmp_path / "missing"))
    result = CliRunner().invoke(
        app,
        ["agent", "worktree-add", "3", "--slug", "x", "-C", str(home), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["path"] == str((tmp_path / "demo-3").resolve())
    assert payload["location"] == "fallback"
    assert "does not exist" in payload["location_note"]


def test_project_empty_string_switches_off_user_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    from issue_flow.config import Settings

    user_cfg = Path(os.environ["XDG_CONFIG_HOME"]) / "issue-flow" / "config.toml"
    user_cfg.parent.mkdir(parents=True, exist_ok=True)
    user_cfg.write_text('[issueflow]\nworktrees_dir = "/srv/worktrees"\n')

    other = tmp_path / "other"
    other.mkdir()
    assert Settings().resolve_worktrees_dir(other) == "/srv/worktrees"

    project = tmp_path / "demo"
    (project / ".issueflows").mkdir(parents=True)
    (project / ".issueflows" / "config.toml").write_text(
        '[issueflow]\nworktrees_dir = ""\n', encoding="utf-8"
    )
    assert Settings().resolve_worktrees_dir(project) == ""
