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
# head sha
# ---------------------------------------------------------------------------


def test_head_sha_returns_sha(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "rev-parse"): _FakeProc(stdout="abc123\n")}),
    )
    assert gitutils.head_sha(Path(".")) == "abc123"


def test_head_sha_none_on_failure(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "rev-parse"): _FakeProc(returncode=128)}),
    )
    assert gitutils.head_sha(Path(".")) is None


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
        gitutils.subprocess,
        "run",
        _fake_runner({}),  # everything fails
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


def test_run_decodes_stdout_as_utf8_replace(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    """Windows locale decoding must not be used for gh/git capture (#216)."""
    seen: dict[str, Any] = {}

    def capture_run(argv: list[str], **kwargs: Any) -> _FakeProc:
        seen.update(kwargs)
        return _FakeProc(stdout="ok\n")

    monkeypatch.setattr(gitutils.subprocess, "run", capture_run)
    assert gitutils._stdout(["git", "branch", "--show-current"], Path(".")) == "ok"
    assert seen.get("text") is True
    assert seen.get("encoding") == "utf-8"
    assert seen.get("errors") == "replace"


def test_stdout_none_when_captured_stdout_is_none(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    """Decode-thread failures can leave CompletedProcess.stdout as None (#216)."""

    class _NoneStdoutProc:
        def __init__(self, returncode: int = 0) -> None:
            self.returncode = returncode
            self.stdout = None
            self.stderr = None

    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        lambda *_a, **_kw: _NoneStdoutProc(0),
    )
    assert gitutils._stdout(["gh", "issue", "view", "1"], Path(".")) is None
    assert gitutils.working_tree_clean(Path(".")) is True

    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        lambda *_a, **_kw: _NoneStdoutProc(1),
    )
    assert gitutils.switch_branch(Path("."), "main") == (
        False,
        "git switch main failed",
    )


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


# ---------------------------------------------------------------------------
# switchback building blocks
# ---------------------------------------------------------------------------


def test_dirty_paths_lists_files(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner(
            {("git", "status"): _FakeProc(stdout=" M src/a.py\n?? new.txt\n")}
        ),
    )
    assert gitutils.dirty_paths(Path(".")) == ["src/a.py", "new.txt"]


def test_dirty_paths_empty_when_clean(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "status"): _FakeProc(stdout="")}),
    )
    assert gitutils.dirty_paths(Path(".")) == []


def test_dirty_paths_none_when_git_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitutils.shutil, "which", lambda _cmd: None)
    assert gitutils.dirty_paths(Path(".")) is None


def test_dirty_paths_expands_rename_both_sides(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner(
            {
                ("git", "status"): _FakeProc(
                    stdout="R  .issueflows/02/a.md -> .issueflows/03/a.md\n"
                )
            }
        ),
    )
    assert gitutils.dirty_paths(Path(".")) == [
        ".issueflows/02/a.md",
        ".issueflows/03/a.md",
    ]


def test_issueflows_only_dirty_empty_and_under_tree() -> None:
    assert gitutils.issueflows_only_dirty([]) is True
    assert (
        gitutils.issueflows_only_dirty(
            [".issueflows/01-current-issues/issue1_original.md"]
        )
        is True
    )
    assert gitutils.issueflows_only_dirty([".issueflows"]) is True


def test_issueflows_only_dirty_rejects_outside_and_prefix_lookalikes() -> None:
    assert (
        gitutils.issueflows_only_dirty([".issueflows/x.md", "src/issue_flow/cli.py"])
        is False
    )
    assert gitutils.issueflows_only_dirty(["issueflows_backup/x.md"]) is False
    assert gitutils.issueflows_only_dirty(["not.issueflows/x.md"]) is False


def test_issueflows_only_dirty_custom_dir_and_none() -> None:
    assert (
        gitutils.issueflows_only_dirty(["tracking/a.md"], issueflows_dir="tracking")
        is True
    )
    assert (
        gitutils.issueflows_only_dirty([".issueflows/a.md"], issueflows_dir="tracking")
        is False
    )
    assert gitutils.issueflows_only_dirty(None) is None


def test_switch_branch_success(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner(
            {("git", "switch"): _FakeProc(stdout="Switched to branch 'main'")}
        ),
    )
    assert gitutils.switch_branch(Path("."), "main") == (True, None)


def test_switch_branch_reports_error(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    proc = _FakeProc(returncode=1)
    proc.stderr = "error: pathspec 'nope' did not match"
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "switch"): proc}),
    )
    ok, message = gitutils.switch_branch(Path("."), "nope")
    assert ok is False
    assert message is not None and "pathspec" in message


def test_pull_ff_only_success(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "pull"): _FakeProc(stdout="Already up to date.")}),
    )
    assert gitutils.pull_ff_only(Path(".")) == (True, None)


def test_pull_ff_only_reports_refusal(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    proc = _FakeProc(returncode=128)
    proc.stderr = "fatal: Not possible to fast-forward, aborting."
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("git", "pull"): proc}),
    )
    ok, message = gitutils.pull_ff_only(Path("."))
    assert ok is False
    assert message is not None and "fast-forward" in message


def test_subprocess_import_is_available() -> None:
    """Guard against accidentally dropping the subprocess import."""
    assert gitutils.subprocess is subprocess


# ---------------------------------------------------------------------------
# remote branch audit helpers
# ---------------------------------------------------------------------------


def test_list_origin_branches_strips_prefix(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner(
            {
                ("git", "for-each-ref"): _FakeProc(
                    stdout="origin/HEAD\norigin/main\norigin/feat\norigin\n"
                )
            }
        ),
    )
    assert gitutils.list_origin_branches(Path(".")) == ["main", "feat"]


def test_cherry_unique_count_counts_plus_lines(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner(
            {("git", "cherry"): _FakeProc(stdout="- abc\n+ def\n+ ghi\n- jkl\n")}
        ),
    )
    assert gitutils.cherry_unique_count(Path("."), "main", "feat") == 2


def test_unique_commit_onelines_splits(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner(
            {("git", "log"): _FakeProc(stdout="abc Fix bug\ndef Add feature\n")}
        ),
    )
    assert gitutils.unique_commit_onelines(Path("."), "main", "feat") == [
        "abc Fix bug",
        "def Add feature",
    ]


def test_gh_prs_for_head_parses_json(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    payload = (
        '[{"number": 1, "title": "T", "state": "OPEN", "url": "u", "mergedAt": null}]'
    )
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("gh", "pr", "list"): _FakeProc(stdout=payload)}),
    )
    data = gitutils.gh_prs_for_head(Path("."), "feat", "octo/repo")
    assert data is not None
    assert data[0]["number"] == 1
    assert data[0]["state"] == "OPEN"


def test_branch_is_protected_true(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner({("gh", "api"): _FakeProc(stdout="true")}),
    )
    assert gitutils.branch_is_protected(Path("."), "main", "octo/repo") is True


def test_gh_issue_database_id_parses_int(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner(
            {
                ("gh", "api", "repos/octo/repo/issues/5"): _FakeProc(
                    stdout="3000028010\n"
                )
            }
        ),
    )
    assert gitutils.gh_issue_database_id(5, Path("."), "octo/repo") == 3000028010


def test_gh_list_sub_issue_numbers_parses_lines(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    monkeypatch.setattr(
        gitutils.subprocess,
        "run",
        _fake_runner(
            {
                (
                    "gh",
                    "api",
                    "repos/octo/repo/issues/12/sub_issues",
                ): _FakeProc(stdout="240\n241\n")
            }
        ),
    )
    assert gitutils.gh_list_sub_issue_numbers(12, Path("."), "octo/repo") == [240, 241]


def test_gh_add_sub_issue_sends_integer_json(
    monkeypatch: pytest.MonkeyPatch, all_tools_present: None
) -> None:
    seen: dict[str, object] = {}

    def run(argv: list[str], **kwargs: object) -> _FakeProc:
        seen["argv"] = argv
        seen["input"] = kwargs.get("input")
        return _FakeProc(stdout="{}", returncode=0)

    monkeypatch.setattr(gitutils.subprocess, "run", run)
    ok, err = gitutils.gh_add_sub_issue(12, 3000028010, Path("."), "octo/repo")
    assert ok is True
    assert err is None
    argv = seen["argv"]
    assert isinstance(argv, list)
    assert "--input" in argv
    assert "-f" not in argv
    assert seen["input"] == '{"sub_issue_id": 3000028010}'
