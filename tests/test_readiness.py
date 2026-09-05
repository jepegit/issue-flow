"""Tests for issue_flow.readiness (the facts behind ``/iflow-setup``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from issue_flow import gitutils, readiness
from issue_flow.readiness import probe


@pytest.fixture
def _no_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nothing on PATH: uv, git, and gh are all missing."""
    monkeypatch.setattr(readiness.shutil, "which", lambda _cmd: None)
    monkeypatch.setattr(gitutils, "git_available", lambda: False)
    monkeypatch.setattr(gitutils, "gh_available", lambda: False)


def _stub_git(
    monkeypatch: pytest.MonkeyPatch,
    *,
    repo_root: Path | None,
    commits: bool = False,
    origin: tuple[str, str] | None = None,
    authenticated: bool = False,
) -> None:
    """Pretend every tool is installed and the repo is in a given state."""
    monkeypatch.setattr(readiness.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
    monkeypatch.setattr(gitutils, "git_available", lambda: True)
    monkeypatch.setattr(gitutils, "gh_available", lambda: True)
    monkeypatch.setattr(gitutils, "repo_root", lambda _cwd: repo_root)
    monkeypatch.setattr(gitutils, "has_commits", lambda _cwd: commits)
    monkeypatch.setattr(gitutils, "remote_owner_repo", lambda _cwd: origin)
    monkeypatch.setattr(gitutils, "current_branch", lambda _cwd: "main")
    monkeypatch.setattr(gitutils, "gh_authenticated", lambda _cwd: authenticated)
    monkeypatch.setattr(gitutils, "gh_account", lambda _cwd: "octocat")


def _ids(report: readiness.Readiness) -> list[str]:
    return [blocker.id for blocker in report.blockers]


def test_bare_directory_without_tools_reports_every_blocker(
    tmp_path: Path, _no_tools: None
) -> None:
    report = probe(tmp_path)

    assert report.verdict == "needs_setup"
    assert report.project_kind == "new"
    assert report.tools == {"uv": False, "git": False, "gh": False}
    # gh_unauthenticated is not raised when gh itself is missing: installing it
    # is the actionable step, and the auth state is unknowable until then.
    assert _ids(report) == [
        "uv_missing",
        "git_missing",
        "gh_missing",
        "python_project_missing",
        "git_repo_missing",
        "git_remote_missing",
        "scaffold_missing",
    ]


def test_fully_configured_project_is_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'x'\n", encoding="utf-8"
    )
    (tmp_path / ".issueflows").mkdir()
    _stub_git(
        monkeypatch,
        repo_root=tmp_path,
        commits=True,
        origin=("octocat", "demo"),
        authenticated=True,
    )

    report = probe(tmp_path)

    assert report.verdict == "ready"
    assert report.blockers == []
    assert report.git["origin"] == "octocat/demo"
    assert report.github["account"] == "octocat"


def test_directory_inside_another_repo_is_not_a_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`git rev-parse` answers for the enclosing tree; that is not our repo.

    Without this distinction an empty folder created inside any existing
    checkout (a very common way to start a new project) would look like a
    repo that already has commits.
    """
    nested = tmp_path / "new-project"
    nested.mkdir()
    _stub_git(monkeypatch, repo_root=tmp_path, commits=True, origin=("o", "r"))

    report = probe(nested)

    assert report.git["is_repo"] is False
    assert report.git["enclosing_repo"] == str(tmp_path)
    assert report.git["has_commits"] is False
    assert report.git["has_origin"] is False
    assert report.project_kind == "new"

    repo_blocker = next(b for b in report.blockers if b.id == "git_repo_missing")
    assert repo_blocker.agent_may_run is False
    assert str(tmp_path) in repo_blocker.summary


def test_repo_without_commits_asks_for_the_first_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_git(monkeypatch, repo_root=tmp_path, commits=False, authenticated=True)

    ids = _ids(probe(tmp_path))

    assert "git_repo_missing" not in ids
    assert "git_commits_missing" in ids


def test_unauthenticated_gh_blocks_the_remote_fix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_git(monkeypatch, repo_root=tmp_path, commits=True, authenticated=False)

    report = probe(tmp_path)

    assert "gh_unauthenticated" in _ids(report)
    auth = next(b for b in report.blockers if b.id == "gh_unauthenticated")
    assert auth.fix == "gh auth login"
    # gh auth login is an interactive browser flow; the agent must not drive it.
    assert auth.agent_may_run is False
    # Creating the remote needs an authenticated gh, so it is not agent-runnable
    # until the user has signed in.
    remote = next(b for b in report.blockers if b.id == "git_remote_missing")
    assert remote.agent_may_run is False


def test_existing_project_never_offers_automatic_uv_init(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "main.py").write_text("print('hi')\n", encoding="utf-8")
    _stub_git(
        monkeypatch,
        repo_root=tmp_path,
        commits=True,
        origin=("o", "r"),
        authenticated=True,
    )

    report = probe(tmp_path)

    assert report.project_kind == "existing"
    python = next(b for b in report.blockers if b.id == "python_project_missing")
    assert python.agent_may_run is False
    assert "uv init" not in python.fix


def test_scaffold_output_alone_still_reads_as_a_new_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A folder holding only issue-flow's own output is not "existing" code."""
    (tmp_path / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / ".env").write_text("", encoding="utf-8")
    _stub_git(monkeypatch, repo_root=tmp_path, commits=False)

    assert probe(tmp_path).project_kind == "new"


def test_payload_is_json_serialisable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    _stub_git(monkeypatch, repo_root=tmp_path)
    payload = probe(tmp_path).as_dict()

    round_tripped = json.loads(json.dumps(payload))
    assert round_tripped["verdict"] == "needs_setup"
    assert {"id", "summary", "fix", "agent_may_run"} == set(
        round_tripped["blockers"][0]
    )
