"""Integration tests for `issue-flow agent local-branches` on real git repos.

These reproduce issue #243: in a squash-merging repo, `git branch -d` refuses
every landed branch because a squash merge leaves the branch tip unreachable
from the default branch. Classification therefore has to lean on patch
equivalence (`git cherry`) and PR evidence, not reachability alone.

Real repositories are used because the behaviour under test *is* the git
plumbing — a faked `subprocess` would only assert that squash merges work the
way the mock says they do.
"""

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


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture(autouse=True)
def _no_gh(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep default-branch detection offline and PR evidence absent by default.

    A temp repo with a filesystem remote is not a GitHub repo, so `gh` would
    fail slowly or behave differently depending on the dev machine's auth.
    """
    monkeypatch.setattr(gitutils, "GH", "gh-not-installed-for-tests")


@pytest.fixture
def work(tmp_path: Path) -> Path:
    """A clone holding one branch of every interesting shape.

    - ``ff-merged`` — fast-forward merged upstream, so its tip is reachable.
    - ``squashed`` — landed via ``git merge --squash``: same patch, new commit.
    - ``divergent`` — squash-landed, then amended so the tip differs.
    - ``in-progress`` — real unique work that must never be deleted.
    """
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "--initial-branch=main")
    _git(upstream, "config", "user.name", "Test")
    _git(upstream, "config", "user.email", "test@example.com")
    (upstream / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-m", "Initial commit")

    # A branch whose commit is merged with a plain fast-forward.
    _git(upstream, "switch", "-c", "ff-merged")
    (upstream / "ff.py").write_text("FF = 1\n", encoding="utf-8")
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-m", "Add ff module")
    _git(upstream, "switch", "main")
    _git(upstream, "merge", "--ff-only", "ff-merged")

    # A branch squash-merged into main: the patch lands under a new commit,
    # so the branch tip is not an ancestor of main.
    _git(upstream, "switch", "-c", "squashed")
    (upstream / "squashed.py").write_text("SQUASHED = 1\n", encoding="utf-8")
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-m", "Add squashed module")
    _git(upstream, "switch", "main")
    _git(upstream, "merge", "--squash", "squashed")
    _git(upstream, "commit", "-m", "Add squashed module (#1)")

    # Same, but the branch keeps a commit that never landed in that form.
    _git(upstream, "switch", "-c", "divergent")
    (upstream / "divergent.py").write_text("DIVERGENT = 1\n", encoding="utf-8")
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-m", "Add divergent module")
    _git(upstream, "switch", "main")
    _git(upstream, "merge", "--squash", "divergent")
    _git(upstream, "commit", "-m", "Add divergent module (#2)")
    _git(upstream, "switch", "divergent")
    (upstream / "divergent.py").write_text("DIVERGENT = 2\n", encoding="utf-8")
    _git(upstream, "commit", "-am", "Tweak divergent module")

    # Unique, unlanded work.
    _git(upstream, "switch", "main")
    _git(upstream, "switch", "-c", "in-progress")
    (upstream / "wip.py").write_text("WIP = 1\n", encoding="utf-8")
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-m", "Start some work")

    _git(upstream, "switch", "main")

    clone = tmp_path / "work"
    _git(tmp_path, "clone", str(upstream), str(clone))
    _git(clone, "config", "user.name", "Test")
    _git(clone, "config", "user.email", "test@example.com")
    for branch in ("ff-merged", "squashed", "divergent", "in-progress"):
        _git(clone, "branch", branch, f"origin/{branch}")
    return clone


def _run(work: Path, *extra: str) -> tuple[int, dict]:
    result = CliRunner().invoke(
        app,
        ["agent", "local-branches", "-C", str(work), "--json", "--no-fetch", *extra],
    )
    payload = json.loads(result.stdout) if result.stdout.strip() else {}
    return result.exit_code, payload


def _names(payload: dict, bucket: str) -> list[str]:
    return [entry["name"] for entry in payload.get(bucket) or []]


def test_classifies_reachable_squashed_and_unique_work(work: Path) -> None:
    exit_code, payload = _run(work)

    assert exit_code == 0, payload
    assert payload["base_ref"] == "origin/main"
    assert _names(payload, "reachable") == ["ff-merged"]
    assert _names(payload, "squash_landed") == ["squashed"]
    assert _names(payload, "unique_work") == ["divergent", "in-progress"]
    # `main` is checked out in the clone, so it is skipped as both.
    assert _names(payload, "skipped") == ["main"]


def test_squash_landed_entries_carry_tip_sha_for_recovery(work: Path) -> None:
    _, payload = _run(work)

    entry = payload["squash_landed"][0]
    assert entry["tip"] == gitutils.branch_tip(work, "squashed")
    assert "patch-equivalent" in entry["reason"]


def test_plain_d_refuses_squash_landed_once_the_remote_ref_is_gone(
    work: Path,
) -> None:
    """The premise of #243, with git's actual `-d` rule.

    ``git branch -d`` accepts a branch merged into *either* HEAD or its own
    upstream, so it still works while ``origin/squashed`` exists. Merging a PR
    deletes the remote branch, and the next ``git fetch --prune`` drops that
    remote-tracking ref — from then on only reachability from the default
    branch counts, and a squash-landed branch has none. That is the state
    cleanup actually runs in.
    """
    _, payload = _run(work)
    assert _names(payload, "squash_landed") == ["squashed"]

    _git(work, "update-ref", "-d", "refs/remotes/origin/squashed")

    ok, err = gitutils.delete_branch(work, "squashed")
    assert ok is False
    assert "not fully merged" in (err or "")

    ok, err = gitutils.delete_branch(work, "squashed", force=True)
    assert ok is True, err


def test_squash_landed_survives_losing_its_remote_tracking_ref(work: Path) -> None:
    """Classification must not depend on the remote ref still being there."""
    _git(work, "update-ref", "-d", "refs/remotes/origin/squashed")

    _, payload = _run(work)

    assert _names(payload, "squash_landed") == ["squashed"]


def test_the_command_never_deletes_anything(work: Path) -> None:
    before = gitutils.list_local_branches(work)

    exit_code, _ = _run(work)

    assert exit_code == 0
    assert gitutils.list_local_branches(work) == before


def test_current_branch_is_never_a_delete_candidate(work: Path) -> None:
    _git(work, "switch", "squashed")

    _, payload = _run(work)

    assert _names(payload, "squash_landed") == []
    skipped = {entry["name"]: entry["reason"] for entry in payload["skipped"]}
    assert "current branch" in skipped["squashed"]


def test_merged_pr_with_no_newer_commit_is_divergent_not_unique(
    work: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A squash rewrite is safe to force-delete; the PR is the evidence."""
    merged_at = "2099-01-01T00:00:00Z"
    monkeypatch.setattr(
        gitutils,
        "gh_available",
        lambda: True,
    )
    monkeypatch.setattr(
        gitutils,
        "gh_prs_by_head",
        lambda *_args, **_kwargs: {
            "divergent": [
                {
                    "number": 2,
                    "title": "Add divergent module",
                    "state": "MERGED",
                    "url": "https://example.invalid/pr/2",
                    "mergedAt": merged_at,
                }
            ]
        },
    )
    monkeypatch.setattr(gitutils, "branch_is_protected", lambda *_a, **_k: None)

    _, payload = _run(work)

    assert _names(payload, "merged_pr_divergent") == ["divergent"]
    assert _names(payload, "unique_work") == ["in-progress"]
    entry = payload["merged_pr_divergent"][0]
    assert entry["unique_commits"] == 1
    assert entry["commits"], "unique commit subjects are needed for the confirm"
    assert entry["tip"] == gitutils.branch_tip(work, "divergent")


def test_commits_pushed_after_the_merge_stay_unique_work(
    work: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Work added *after* a PR merged is not a squash artefact — never offer it.

    Same bucket counts as the divergent case, opposite verdict: the deciding
    evidence is that a unique commit is newer than the merge.
    """
    monkeypatch.setattr(gitutils, "gh_available", lambda: True)
    monkeypatch.setattr(
        gitutils,
        "gh_prs_by_head",
        lambda *_args, **_kwargs: {
            "divergent": [
                {
                    "number": 2,
                    "title": "Add divergent module",
                    "state": "MERGED",
                    "url": "https://example.invalid/pr/2",
                    "mergedAt": "1999-01-01T00:00:00Z",
                }
            ]
        },
    )
    monkeypatch.setattr(gitutils, "branch_is_protected", lambda *_a, **_k: None)

    _, payload = _run(work)

    assert _names(payload, "merged_pr_divergent") == []
    entry = next(item for item in payload["unique_work"] if item["name"] == "divergent")
    assert entry["committed_after_merge"] is True
    assert "after PR #2 merged" in entry["reason"]


def test_missing_git_exits_one_with_a_note(
    work: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gitutils, "git_available", lambda: False)

    exit_code, payload = _run(work)

    assert exit_code == 1
    assert any("git is not on PATH" in note for note in payload["notes"])
