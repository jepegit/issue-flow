"""Integration tests for ``issue-flow agent apply-changelog`` (issue #288)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from issue_flow import gitutils
from issue_flow.cli import app

pytestmark = pytest.mark.skipif(
    not gitutils.git_available(), reason="git is not on PATH"
)

_HISTORY = """# History

## [Unreleased]

## [0.1.0] - 2026-01-01

- First release.
"""

_BULLET = "- Prevent HISTORY conflicts. (#288)"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture(autouse=True)
def _no_gh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitutils, "GH", "gh-not-installed-for-tests")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "work"
    root.mkdir()
    _git(root, "init", "--initial-branch=main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "HISTORY.md").write_text(_HISTORY, encoding="utf-8")
    _git(root, "add", "HISTORY.md")
    _git(root, "commit", "-m", "seed")
    _git(root, "remote", "add", "origin", str(root))
    _git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    return root


def _write_status(root: Path, *, folder: str = "01-current-issues") -> Path:
    status_dir = root / ".issueflows" / folder
    status_dir.mkdir(parents=True)
    path = status_dir / "issue288_status.md"
    path.write_text(
        f"# Status — #288\n\n- [x] Done\n\n### Deferred changelog\n\n{_BULLET}\n",
        encoding="utf-8",
    )
    return path


def _invoke(root: Path, *extra: str) -> tuple[int, dict]:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "agent",
            "apply-changelog",
            "--issue",
            "288",
            "-C",
            str(root),
            "--json",
            *extra,
        ],
    )
    payload = json.loads(result.stdout)
    return result.exit_code, payload


def test_apply_changelog_appends_on_default(repo: Path) -> None:
    _write_status(repo)
    code, payload = _invoke(repo)
    assert code == 0
    assert payload["action"] == "appended"
    assert payload["ok"] is True
    text = (repo / "HISTORY.md").read_text(encoding="utf-8")
    assert _BULLET in text
    assert text.index("## [Unreleased]") < text.index(_BULLET)


def test_apply_changelog_is_idempotent(repo: Path) -> None:
    _write_status(repo)
    assert _invoke(repo)[0] == 0
    code, payload = _invoke(repo)
    assert code == 0
    assert payload["action"] == "noop"
    assert payload["reason"] == "already_present"
    assert (repo / "HISTORY.md").read_text(encoding="utf-8").count(_BULLET) == 1


def test_apply_changelog_refuses_issue_branch(repo: Path) -> None:
    _write_status(repo)
    _git(repo, "switch", "-c", "288-defer-changelog")
    code, payload = _invoke(repo)
    assert code == 1
    assert payload["action"] == "refused"
    assert payload["reason"] == "not_default_branch"
    assert _BULLET not in (repo / "HISTORY.md").read_text(encoding="utf-8")


def test_apply_changelog_reads_solved_status(repo: Path) -> None:
    _write_status(repo, folder="03-solved-issues")
    code, payload = _invoke(repo)
    assert code == 0
    assert payload["action"] == "appended"
    assert "03-solved-issues" in payload["status_file"]


def test_apply_changelog_promotes_when_planned_version(repo: Path) -> None:
    status_dir = repo / ".issueflows" / "01-current-issues"
    status_dir.mkdir(parents=True)
    (status_dir / "issue288_status.md").write_text(
        f"### Deferred changelog\n\n{_BULLET}\n\nPlanned version: 0.2.0\n",
        encoding="utf-8",
    )
    code, payload = _invoke(repo)
    assert code == 0
    assert payload["action"] == "promoted"
    text = (repo / "HISTORY.md").read_text(encoding="utf-8")
    assert "## [0.2.0] - " in text
    assert text.index("## [Unreleased]") < text.index("## [0.2.0]")
    assert _BULLET in text


def test_apply_changelog_noop_nohistory(repo: Path) -> None:
    status_dir = repo / ".issueflows" / "01-current-issues"
    status_dir.mkdir(parents=True)
    (status_dir / "issue288_status.md").write_text(
        "### Deferred changelog\n\nnohistory\n",
        encoding="utf-8",
    )
    code, payload = _invoke(repo)
    assert code == 0
    assert payload["reason"] == "nohistory"
    assert _BULLET not in (repo / "HISTORY.md").read_text(encoding="utf-8")
