"""Integration tests for `issue-flow workspace cleanup` (issue #392).

Real git repos again (see ``test_agent_local_branches.py``): the behaviour
under test is the per-member classification plus the ``--apply`` git
plumbing, and both live or die on what git actually does.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from issue_flow import gitutils
from issue_flow.cli import app
from issue_flow.project import WORKSPACE_FILENAME

pytestmark = pytest.mark.skipif(
    not gitutils.git_available(), reason="git is not on PATH"
)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture(autouse=True)
def _no_gh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitutils, "GH", "gh-not-installed-for-tests")
    monkeypatch.delenv("ISSUEFLOW_LOCKED", raising=False)


def _scaffold(root: Path) -> None:
    base = root / ".issueflows"
    for folder in (
        "01-current-issues",
        "02-partly-solved-issues",
        "03-solved-issues",
    ):
        (base / folder).mkdir(parents=True, exist_ok=True)


def _make_upstream(path: Path, *, squashed: bool, unique: bool) -> None:
    """An upstream repo with ``ff-merged`` (+ optionally squashed / wip)."""
    path.mkdir()
    _git(path, "init", "--initial-branch=main")
    _git(path, "config", "user.name", "Test")
    _git(path, "config", "user.email", "test@example.com")
    (path / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-m", "Initial commit")

    _git(path, "switch", "-c", "ff-merged")
    (path / "ff.py").write_text("FF = 1\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-m", "Add ff module")
    _git(path, "switch", "main")
    _git(path, "merge", "--ff-only", "ff-merged")

    if squashed:
        _git(path, "switch", "-c", "squashed")
        (path / "squashed.py").write_text("SQUASHED = 1\n", encoding="utf-8")
        _git(path, "add", ".")
        _git(path, "commit", "-m", "Add squashed module")
        _git(path, "switch", "main")
        _git(path, "merge", "--squash", "squashed")
        _git(path, "commit", "-m", "Add squashed module (#1)")

    if unique:
        _git(path, "switch", "-c", "in-progress")
        (path / "wip.py").write_text("WIP = 1\n", encoding="utf-8")
        _git(path, "add", ".")
        _git(path, "commit", "-m", "Start some work")
        _git(path, "switch", "main")


def _clone(
    tmp_path: Path, upstream: Path, name: str, branches: tuple[str, ...]
) -> Path:
    clone = tmp_path / name
    _git(tmp_path, "clone", str(upstream), str(clone))
    _git(clone, "config", "user.name", "Test")
    _git(clone, "config", "user.email", "test@example.com")
    for branch in branches:
        _git(clone, "branch", branch, f"origin/{branch}")
    _scaffold(clone)
    return clone


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Two scaffolded members: ``alpha`` (all shapes) and ``beta`` (ff only)."""
    remotes = tmp_path / "remotes"
    remotes.mkdir()
    _make_upstream(remotes / "alpha", squashed=True, unique=True)
    _make_upstream(remotes / "beta", squashed=False, unique=False)
    _clone(
        tmp_path, remotes / "alpha", "alpha", ("ff-merged", "squashed", "in-progress")
    )
    _clone(tmp_path, remotes / "beta", "beta", ("ff-merged",))
    (tmp_path / WORKSPACE_FILENAME).write_text(
        '[workspace]\ndefault = "alpha"\nmembers = ["alpha", "beta"]\n',
        encoding="utf-8",
    )
    return tmp_path


def _run(workspace: Path, *extra: str) -> tuple[int, dict[str, Any]]:
    result = CliRunner().invoke(
        app,
        ["workspace", "cleanup", str(workspace), "--json", "--no-fetch", *extra],
    )
    payload = json.loads(result.stdout) if result.stdout.strip() else {}
    return result.exit_code, payload


def _local_branches(root: Path) -> dict[str, Any]:
    result = CliRunner().invoke(
        app, ["agent", "local-branches", "-C", str(root), "--json", "--no-fetch"]
    )
    return json.loads(result.stdout)


def _member(payload: dict[str, Any], name: str) -> dict[str, Any]:
    return next(m for m in payload["members"] if m["name"] == name)


def _names(items: list[dict[str, Any]]) -> list[str]:
    return [str(item["name"]) for item in items]


# ---------------------------------------------------------------------------
# classify-only
# ---------------------------------------------------------------------------


def test_buckets_match_agent_local_branches_per_member(workspace: Path) -> None:
    """AC1: per-member buckets identical to ``agent local-branches``."""
    code, payload = _run(workspace)
    assert code == 0, payload
    assert payload["apply"] is False
    for name in ("alpha", "beta"):
        member = _member(payload, name)
        assert member["ok"] is True and member["skipped"] is False
        expected = _local_branches(workspace / name)
        for bucket in (
            "reachable",
            "squash_landed",
            "merged_pr_divergent",
            "unique_work",
            "skipped",
        ):
            assert member["buckets"][bucket] == expected[bucket], (name, bucket)
    alpha = _member(payload, "alpha")
    assert _names(alpha["buckets"]["reachable"]) == ["ff-merged"]
    assert _names(alpha["buckets"]["squash_landed"]) == ["squashed"]
    assert _names(alpha["buckets"]["unique_work"]) == ["in-progress"]
    assert payload["totals"]["reachable"] == 2
    assert payload["totals"]["unique_work"] == 1


def test_plan_never_lists_unique_work(workspace: Path) -> None:
    """AC4: ``unique_work`` never shows up in any delete list."""
    _, payload = _run(workspace)
    alpha = _member(payload, "alpha")
    plan = alpha["plan"]
    assert plan["a1"]["branch_d"] == ["ff-merged"]
    assert _names(plan["a2"]["branch_D"]) == ["squashed"]
    assert "in-progress" not in plan["a1"]["branch_d"]
    assert "in-progress" not in _names(plan["a2"]["branch_D"])
    entry = plan["a2"]["branch_D"][0]
    assert entry["tip"]
    assert entry["recover"] == f"git branch squashed {entry['tip']}"


def test_classify_only_changes_nothing(workspace: Path) -> None:
    before = {
        name: gitutils.list_local_branches(workspace / name)
        for name in ("alpha", "beta")
    }
    code, _ = _run(workspace)
    assert code == 0
    for name in ("alpha", "beta"):
        assert gitutils.list_local_branches(workspace / name) == before[name]


def test_non_ff_member_skips_pull_but_others_proceed(workspace: Path) -> None:
    """AC3: a member whose default cannot fast-forward is never pulled."""
    beta = workspace / "beta"
    (beta / "extra.py").write_text("EXTRA = 1\n", encoding="utf-8")
    _git(beta, "add", ".")
    _git(beta, "commit", "-m", "Local-only commit on main")

    code, payload = _run(workspace)
    assert code == 0
    member = _member(payload, "beta")
    assert member["skipped"] is False
    assert member["default_sync"]["ahead"] == 1
    assert member["default_sync"]["action"] not in ("even", "ff_only")
    assert member["plan"]["a1"]["pull_ff_only"] is False
    assert (
        member["plan"]["a1"]["pull_skipped_reason"] == member["default_sync"]["action"]
    )
    # Classification still happened for the non-ff member and for alpha.
    assert _names(member["buckets"]["reachable"]) == ["ff-merged"]
    assert _names(_member(payload, "alpha")["buckets"]["reachable"]) == ["ff-merged"]


def test_refuse_to_loop_cases_skip_member_and_continue(tmp_path: Path) -> None:
    remotes = tmp_path / "remotes"
    remotes.mkdir()
    for name in ("clean", "dirty", "detached", "noorigin"):
        _make_upstream(remotes / name, squashed=False, unique=False)
        _clone(tmp_path, remotes / name, name, ("ff-merged",))
    (tmp_path / "dirty" / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(tmp_path / "detached", "switch", "--detach", "HEAD")
    _git(tmp_path / "noorigin", "remote", "remove", "origin")
    (tmp_path / WORKSPACE_FILENAME).write_text(
        '[workspace]\ndefault = "clean"\n'
        'members = ["clean", "dirty", "detached", "noorigin"]\n',
        encoding="utf-8",
    )

    code, payload = _run(tmp_path)
    assert code == 0, payload
    assert payload["ok_count"] == 1
    assert payload["skip_count"] == 3
    assert payload["fail_count"] == 0
    assert _member(payload, "clean")["skipped"] is False
    dirty = _member(payload, "dirty")
    assert dirty["skipped"] is True
    assert dirty["reason"] == "dirty product-code tree"
    assert dirty["dirty_paths"] == ["module.py"]
    assert _member(payload, "detached")["reason"] == "detached HEAD"
    assert _member(payload, "noorigin")["reason"] == "missing origin remote"


def test_issueflows_only_dirt_blocks_switch_not_classification(workspace: Path) -> None:
    alpha = workspace / "alpha"
    _git(alpha, "switch", "in-progress")
    (alpha / ".issueflows" / "01-current-issues" / "note.md").write_text(
        "wip\n", encoding="utf-8"
    )
    _, payload = _run(workspace)
    member = _member(payload, "alpha")
    assert member["skipped"] is False
    assert member["dirty_class"] == "issueflows_only"
    assert member["plan"]["a1"]["switch_default"] is False
    assert "issueflows-only" in member["plan"]["a1"]["switch_blocked_reason"]
    assert _names(member["buckets"]["reachable"]) == ["ff-merged"]


def test_unique_work_worktree_is_refused_not_member(workspace: Path) -> None:
    alpha = workspace / "alpha"
    wt = workspace / "alpha-wip"
    _git(alpha, "worktree", "add", str(wt), "in-progress")

    _, payload = _run(workspace)
    member = _member(payload, "alpha")
    assert member["skipped"] is False
    assert any("unique work" in line for line in member["refusals"])
    worktree = next(w for w in member["worktrees"] if w["branch"] == "in-progress")
    assert worktree["bucket"] == "unique_work"
    assert str(wt.resolve()) not in member["plan"]["a1"]["worktree_remove"]
    assert str(wt.resolve()) not in member["plan"]["a2"]["worktree_remove"]


def test_extra_root_and_locked_member(workspace: Path, tmp_path: Path) -> None:
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    _make_upstream(tmp_path / "remotes" / "gamma", squashed=False, unique=False)
    gamma = _clone(outside, tmp_path / "remotes" / "gamma", "gamma", ("ff-merged",))
    (workspace / "beta" / ".issueflows" / "config.toml").write_text(
        "[issueflow]\nlocked = true\n", encoding="utf-8"
    )

    code, payload = _run(workspace, "--extra-root", str(gamma))
    assert code == 0, payload
    names = [m["name"] for m in payload["members"]]
    assert names == ["alpha", "beta", "gamma"]
    assert _member(payload, "beta")["reason"] == "locked"
    assert _names(_member(payload, "gamma")["buckets"]["reachable"]) == ["ff-merged"]


def test_missing_workspace_toml_errors(tmp_path: Path) -> None:
    code, payload = _run(tmp_path)
    assert code == 1
    assert payload["ok"] is False
    assert WORKSPACE_FILENAME in payload["error"]


# ---------------------------------------------------------------------------
# --apply
# ---------------------------------------------------------------------------


def test_dry_run_with_apply_mutates_nothing(workspace: Path) -> None:
    before = gitutils.list_local_branches(workspace / "alpha")
    code, payload = _run(
        workspace, "--apply", "--yes-delete-squash-landed", "--dry-run"
    )
    assert code == 0
    assert payload["apply"] is False
    assert payload["yes_delete_squash_landed"] is False
    assert gitutils.list_local_branches(workspace / "alpha") == before
    assert _member(payload, "alpha")["applied"] is None


def test_apply_deletes_reachable_only_without_a2_flag(workspace: Path) -> None:
    alpha = workspace / "alpha"
    # Merging a PR deletes the remote branch; the next fetch --prune drops the
    # tracking ref — the state cleanup actually runs in (see #243).
    _git(workspace / "remotes" / "alpha", "branch", "-D", "squashed")
    _git(alpha, "update-ref", "-d", "refs/remotes/origin/squashed")

    code, payload = _run(workspace, "--apply")
    assert code == 0, payload
    assert payload["apply"] is True
    member = _member(payload, "alpha")
    a1 = member["applied"]["a1"]
    assert [d["name"] for d in a1["deleted"]] == ["ff-merged"]
    assert a1["deleted"][0]["flag"] == "-d"
    assert a1["pulled"] is True
    assert member["applied"]["a2"]["authorised"] is False
    assert member["applied"]["a2"]["deleted"] == []
    remaining = gitutils.list_local_branches(alpha) or []
    assert "ff-merged" not in remaining
    assert "squashed" in remaining
    assert "in-progress" in remaining
    assert any("--yes-delete-squash-landed" in note for note in member["notes"])
    beta = _member(payload, "beta")
    assert [d["name"] for d in beta["applied"]["a1"]["deleted"]] == ["ff-merged"]


def test_apply_with_a2_flag_force_deletes_and_reports_tips(workspace: Path) -> None:
    alpha = workspace / "alpha"
    # The merged PR deleted the remote branch; the A1 pull's implicit fetch
    # must not resurrect the tracking ref that would let plain -d succeed.
    _git(workspace / "remotes" / "alpha", "branch", "-D", "squashed")
    _git(alpha, "update-ref", "-d", "refs/remotes/origin/squashed")
    tip = gitutils.branch_tip(alpha, "squashed")

    code, payload = _run(workspace, "--apply", "--yes-delete-squash-landed")
    assert code == 0, payload
    assert payload["yes_delete_squash_landed"] is True
    member = _member(payload, "alpha")
    a2 = member["applied"]["a2"]
    assert a2["authorised"] is True
    assert a2["deleted"] == [{"name": "squashed", "tip": tip, "flag": "-D"}]
    remaining = gitutils.list_local_branches(alpha) or []
    assert "squashed" not in remaining
    assert "ff-merged" not in remaining
    assert "in-progress" in remaining  # AC4: unique work survives -D runs
    # Recovery line really works.
    _git(alpha, "branch", "squashed", tip or "")
    assert "squashed" in (gitutils.list_local_branches(alpha) or [])


def test_apply_switches_to_default_when_on_issue_branch(workspace: Path) -> None:
    beta = workspace / "beta"
    _git(beta, "switch", "-c", "7-some-issue")

    code, payload = _run(workspace, "--apply")
    assert code == 0, payload
    member = _member(payload, "beta")
    assert member["plan"]["a1"]["switch_default"] is True
    assert member["applied"]["a1"]["switched"] is True
    assert gitutils.current_branch(beta) == "main"
    # The issue branch was the current branch at classification time, so it
    # was skipped — not deleted behind the user's back.
    assert "7-some-issue" in (gitutils.list_local_branches(beta) or [])


def test_apply_never_pulls_non_ff_member(workspace: Path) -> None:
    beta = workspace / "beta"
    (beta / "extra.py").write_text("EXTRA = 1\n", encoding="utf-8")
    _git(beta, "add", ".")
    _git(beta, "commit", "-m", "Local-only commit on main")
    head_before = gitutils.head_sha(beta)

    code, payload = _run(workspace, "--apply")
    assert code == 0, payload
    member = _member(payload, "beta")
    assert member["applied"]["a1"]["pulled"] is False
    assert gitutils.head_sha(beta) == head_before
    # Reachable deletes still happen; the member is not refused outright.
    assert [d["name"] for d in member["applied"]["a1"]["deleted"]] == ["ff-merged"]


def test_cli_help_lists_cleanup_and_flags() -> None:
    result = CliRunner().invoke(app, ["workspace", "--help"])
    assert result.exit_code == 0
    assert "cleanup" in result.stdout
    result = CliRunner().invoke(app, ["workspace", "cleanup", "--help"])
    assert result.exit_code == 0
    assert "--apply" in result.stdout
    assert "--yes-delete-squash-landed" in result.stdout
    assert "--extra-root" in result.stdout


def test_text_output_groups_by_member(workspace: Path) -> None:
    result = CliRunner().invoke(
        app, ["workspace", "cleanup", str(workspace), "--no-fetch"]
    )
    assert result.exit_code == 0, result.stdout
    out = result.stdout
    assert "Workspace cleanup" in out
    assert "alpha" in out and "beta" in out
    assert "classify-only" in out
    assert "squashed" in out
    assert "-D" in out
