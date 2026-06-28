"""Tests for issue_flow.gitutils — thin git/gh wrappers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from issue_flow import gitutils


class _FakeProc:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def _fake_runner(mapping: dict[tuple[str, ...], _FakeProc]):
    """Build a subprocess.run replacement keyed on a prefix of argv tokens."""

    def run(argv: list[str], **_kwargs: Any) -> _FakeProc:
        for prefix, proc in mapping.items():
            if tuple(argv[: len(prefix)]) == prefix:
                return proc
        return _FakeProc(returncode=1)

    return run


@pytest.fixture
def all_tools_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitutils.shutil, "which", lambda _cmd: f"/usr/bin/{_cmd}")


# ---------------------------------------------------------------------------
# owner/repo parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://github.com/octo/repo.git", ("octo", "repo")),
        ("https://github.com/octo/repo", ("octo", "repo")),
        ("git@github.com:octo/repo.git", ("octo", "repo")),
        ("ssh://git@github.com/octo/repo.git", ("octo", "repo")),
        ("git@github.com:octo/repo", ("octo", "repo")),
    ],
)
def test_remote_owner_repo_parses(
    monkeypatch: pytest.MonkeyPatch,
    all_tools_present: None,
    url: str,
    expected: tuple[str, str],
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "remote", "get-url"): _FakeProc(stdout=url)}),
    )
    assert gitutils.remote_owner_repo(Path(".")) == expected


def test_remote_owner_repo_none_when_git_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gitutils.shutil, "which", lambda _cmd: None)
    assert gitutils.remote_owner_repo(Path(".")) is None


# ---------------------------------------------------------------------------
# ahead/behind
# ---------------------------------------------------------------------------


def test_ahead_behind_parses(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    # `git rev-list --left-right --count origin/main...HEAD` => "<behind>\t<ahead>"
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "rev-list"): _FakeProc(stdout="3\t5")}),
    )
    assert gitutils.ahead_behind(Path("."), "main") == (5, 3)


def test_ahead_behind_none_on_bad_output(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "rev-list"): _FakeProc(stdout="garbage")}),
    )
    assert gitutils.ahead_behind(Path("."), "main") is None


# ---------------------------------------------------------------------------
# default branch detection + fallbacks
# ---------------------------------------------------------------------------


def test_default_branch_prefers_gh(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("gh", "repo", "view"): _FakeProc(stdout="develop")}),
    )
    assert gitutils.default_branch(Path(".")) == "develop"


def test_default_branch_falls_back_to_symbolic_ref(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner(
            {
                ("gh", "repo", "view"): _FakeProc(returncode=1),
                ("git", "symbolic-ref"): _FakeProc(stdout="origin/trunk"),
            }
        ),
    )
    assert gitutils.default_branch(Path(".")) == "trunk"


def test_default_branch_final_fallback_main(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess, "run", _fake_runner({})  # everything fails
    )
    assert gitutils.default_branch(Path(".")) == "main"


# ---------------------------------------------------------------------------
# graceful absence
# ---------------------------------------------------------------------------


def test_run_returns_none_when_executable_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gitutils.shutil, "which", lambda _cmd: None)

    def explode(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("subprocess.run must not run when tool is missing")

    monkeypatch.setattr(gitutils.subprocess, "run", explode)
    assert gitutils.current_branch(Path(".")) is None
    assert gitutils.working_tree_clean(Path(".")) is None
    assert gitutils.gh_issue_view(1, Path(".")) is None


def test_gh_issue_view_parses_json(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    payload = '{"number": 7, "title": "T", "body": "B", "url": "u", "comments": []}'
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("gh", "issue", "view"): _FakeProc(stdout=payload)}),
    )
    data = gitutils.gh_issue_view(7, Path("."), "octo/repo")
    assert data is not None
    assert data["number"] == 7
    assert data["title"] == "T"


def test_working_tree_clean_true_when_empty(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "status"): _FakeProc(stdout="")}),
    )
    assert gitutils.working_tree_clean(Path(".")) is True


def test_working_tree_clean_false_when_dirty(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "status"): _FakeProc(stdout=" M file.py")}),
    )
    assert gitutils.working_tree_clean(Path(".")) is False


def test_subprocess_import_is_available() -> None:
    """Guard against accidentally dropping the subprocess import."""
    assert gitutils.subprocess is subprocess
