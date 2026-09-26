"""Integration tests for `issue-flow agent sync-branch` on real git repos.

These reproduce the scenario from issue #240: an unrelated PR lands on the
default branch while one issue is in flight, and the only collision is a new
bullet in the changelog's ``[Unreleased]`` section. The command must absorb
that automatically, and must refuse — leaving the branch exactly as it was —
for any other conflict.

Real repositories are used because the interesting behaviour *is* the git
plumbing (rebase, conflict staging, `rebase --continue`, abort-on-refusal);
faking `subprocess` would only test the mock.
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

_HISTORY = """# History

## [Unreleased]

## [0.1.0] - 2026-01-01

- First release.
"""

_LANDED = "- Fix the ghost cell in the store. (#952)"
_IN_FLIGHT = "- Clearer otherpath error messages. (#961)"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _write_unreleased(root: Path, bullet: str) -> None:
    """Insert ``bullet`` as the sole entry under ``## [Unreleased]``."""
    path = root / "HISTORY.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "## [Unreleased]\n", f"## [Unreleased]\n\n{bullet}\n"
        ),
        encoding="utf-8",
    )


@pytest.fixture(autouse=True)
def _no_gh(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force default-branch detection down the `origin/HEAD` path.

    A temp repo with a filesystem remote is not a GitHub repo, so `gh repo
    view` would just fail slowly (or behave differently depending on whether
    the dev machine has `gh` authenticated). Pointing `GH` at a name that is
    not on PATH keeps detection deterministic and offline.
    """
    monkeypatch.setattr(gitutils, "GH", "gh-not-installed-for-tests")


@pytest.fixture
def work(tmp_path: Path) -> Path:
    """A clone whose issue branch adds a changelog bullet, with `main` moved on.

    Layout: ``upstream`` (holds `main`) and ``work`` (the clone, on branch
    ``240-changelog-conflicts``). Both added a different `[Unreleased]`
    bullet, so a rebase conflicts on `HISTORY.md` only.
    """
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "--initial-branch=main")
    _git(upstream, "config", "user.name", "Test")
    _git(upstream, "config", "user.email", "test@example.com")
    (upstream / "HISTORY.md").write_text(_HISTORY, encoding="utf-8")
    (upstream / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-m", "Initial commit")

    clone = tmp_path / "work"
    _git(tmp_path, "clone", str(upstream), str(clone))
    _git(clone, "config", "user.name", "Test")
    _git(clone, "config", "user.email", "test@example.com")
    _git(clone, "switch", "-c", "240-changelog-conflicts")
    _write_unreleased(clone, _IN_FLIGHT)
    _git(clone, "commit", "-am", "Improve otherpath error messages")

    _write_unreleased(upstream, _LANDED)
    _git(upstream, "commit", "-am", "Fix ghost cell")

    return clone


def _run(work: Path, *extra: str) -> tuple[int, dict]:
    result = CliRunner().invoke(
        app, ["agent", "sync-branch", "-C", str(work), "--json", *extra]
    )
    payload = json.loads(result.stdout) if result.stdout.strip() else {}
    return result.exit_code, payload


def test_changelog_only_conflict_is_resolved_keeping_both(work: Path) -> None:
    exit_code, payload = _run(work)

    assert exit_code == 0, payload
    assert payload["changelog_resolved"] is True
    assert payload["resolved_paths"] == ["HISTORY.md"]
    assert payload["action"] == "rebased"
    assert payload["needs_force_push"] is True

    text = (work / "HISTORY.md").read_text(encoding="utf-8")
    assert "<<<<<<<" not in text
    lines = text.splitlines()
    assert lines.index(_LANDED) < lines.index(_IN_FLIGHT)
    assert gitutils.dirty_paths(work) == []
    assert gitutils.unmerged_paths(work) == []


def test_merge_strategy_also_resolves_and_needs_no_force_push(work: Path) -> None:
    exit_code, payload = _run(work, "--strategy", "merge")

    assert exit_code == 0, payload
    assert payload["action"] == "merged"
    assert payload["changelog_resolved"] is True
    assert payload["needs_force_push"] is False

    lines = (work / "HISTORY.md").read_text(encoding="utf-8").splitlines()
    assert lines.index(_LANDED) < lines.index(_IN_FLIGHT)


def test_code_conflict_aborts_and_stops(work: Path) -> None:
    """A conflict outside the changelog leaves the branch untouched.

    The changelog conflict is hit first here (it is the earlier commit) and
    resolved, then the code conflict forces an abort — which rewinds that
    resolve too, so the payload must not claim the changelog was kept.
    """
    upstream = work.parent / "upstream"
    (upstream / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(upstream, "commit", "-am", "Bump value upstream")
    (work / "module.py").write_text("VALUE = 3\n", encoding="utf-8")
    _git(work, "commit", "-am", "Bump value on the issue branch")
    before = gitutils.head_sha(work)

    exit_code, payload = _run(work)

    assert exit_code == 1
    assert "module.py" in payload["conflicts"]
    assert payload["changelog_resolved"] is False
    assert gitutils.head_sha(work) == before
    assert gitutils.dirty_paths(work) == []
    assert not gitutils.rebase_in_progress(work)


def test_promoted_version_heading_aborts_and_stops(work: Path) -> None:
    """A changelog conflict that is not two bullet lists is still a stop."""
    _git(work, "switch", "main")
    _git(work, "switch", "-c", "241-release")
    path = work / "HISTORY.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "## [Unreleased]\n",
            "## [Unreleased]\n\n## [0.2.0] - 2026-09-01\n\n- Release notes.\n",
        ),
        encoding="utf-8",
    )
    _git(work, "commit", "-am", "Promote the unreleased section")
    before = gitutils.head_sha(work)

    exit_code, payload = _run(work)

    assert exit_code == 1
    assert payload["changelog_resolved"] is False
    assert any("not two additive" in note for note in payload["notes"])
    assert gitutils.head_sha(work) == before
    assert not gitutils.rebase_in_progress(work)


def test_up_to_date_branch_is_a_no_op(work: Path) -> None:
    """Branching off `origin/main` itself leaves nothing to take on."""
    _git(work, "fetch", "origin")
    _git(work, "switch", "-c", "242-noop", "origin/main")

    exit_code, payload = _run(work)

    assert exit_code == 0
    assert payload["action"] == "none"
    assert payload["behind"] == 0
    assert payload["changelog_resolved"] is False


def test_refuses_on_the_default_branch(work: Path) -> None:
    _git(work, "switch", "main")

    exit_code, payload = _run(work)

    assert exit_code == 1
    assert payload["branch"] == "main"
    assert any("default branch" in note for note in payload["notes"])


def test_refuses_with_a_dirty_tree(work: Path) -> None:
    (work / "module.py").write_text("VALUE = 99\n", encoding="utf-8")

    exit_code, payload = _run(work)

    assert exit_code == 1
    assert payload["dirty_paths"] == ["module.py"]
    assert payload["changelog_resolved"] is False


def test_rejects_an_unknown_strategy(work: Path) -> None:
    exit_code, payload = _run(work, "--strategy", "cherry-pick")

    assert exit_code == 1
    assert any("unknown strategy" in note for note in payload["notes"])


# ---------------------------------------------------------------------------
# issue #386 — bookkeeping files beyond HISTORY.md, stacked / squash parents
# ---------------------------------------------------------------------------

_REGISTRY = ".issueflows/04-designs-and-guides/test-registry.md"
_STATUS = ".issueflows/01-current-issues/issue961_status.md"


def _append(root: Path, rel: str, line: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(text + line + "\n", encoding="utf-8")


@pytest.fixture
def bookkeeping(tmp_path: Path) -> Path:
    """Upstream and branch both append rows / bullets to tracking files only."""
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "--initial-branch=main")
    _git(upstream, "config", "user.name", "Test")
    _git(upstream, "config", "user.email", "test@example.com")
    (upstream / "HISTORY.md").write_text(_HISTORY, encoding="utf-8")
    (upstream / _REGISTRY).parent.mkdir(parents=True)
    (upstream / _REGISTRY).write_text(
        "# Test registry\n\n| Test | Why |\n|---|---|\n| test_a | base |\n",
        encoding="utf-8",
    )
    (upstream / _STATUS).parent.mkdir(parents=True)
    (upstream / _STATUS).write_text(
        "# Status\n\n- [ ] Done\n\n## Log\n\n- started\n", encoding="utf-8"
    )
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-m", "Initial commit")

    clone = tmp_path / "work"
    _git(tmp_path, "clone", str(upstream), str(clone))
    _git(clone, "config", "user.name", "Test")
    _git(clone, "config", "user.email", "test@example.com")
    _git(clone, "switch", "-c", "961-child")
    _append(clone, _REGISTRY, "| test_c | in flight |")
    _append(clone, _STATUS, "- in-flight note")
    _git(clone, "commit", "-am", "In-flight bookkeeping")

    _append(upstream, _REGISTRY, "| test_b | landed |")
    _append(upstream, _STATUS, "- landed note")
    _git(upstream, "commit", "-am", "Landed bookkeeping")
    return clone


def test_design_guide_and_status_conflicts_resolve_keep_both(
    bookkeeping: Path,
) -> None:
    exit_code, payload = _run(bookkeeping)

    assert exit_code == 0, payload
    assert sorted(payload["resolved_paths"]) == sorted([_REGISTRY, _STATUS])
    assert payload["resolvers"][_REGISTRY] == "additive"
    assert payload["changelog_resolved"] is False
    registry = (bookkeeping / _REGISTRY).read_text(encoding="utf-8")
    assert "<<<<<<<" not in registry
    assert registry.index("| test_b |") < registry.index("| test_c |")
    status = (bookkeeping / _STATUS).read_text(encoding="utf-8")
    assert status.index("- landed note") < status.index("- in-flight note")
    assert gitutils.unmerged_paths(bookkeeping) == []


def test_design_guide_heading_conflict_still_aborts(bookkeeping: Path) -> None:
    """A duplicated `## Link` section is not additive — stop, branch untouched."""
    _append(bookkeeping, _REGISTRY, "\n## Link\n\nIssue #961.")
    _git(bookkeeping, "commit", "-am", "Add link section")
    upstream = bookkeeping.parent / "upstream"
    _append(upstream, _REGISTRY, "\n## Link\n\nIssue #952.")
    _git(upstream, "commit", "-am", "Add link section upstream")
    before = gitutils.head_sha(bookkeeping)

    exit_code, payload = _run(bookkeeping)

    assert exit_code == 1
    assert payload["resolved_paths"] == []
    assert gitutils.head_sha(bookkeeping) == before
    assert not gitutils.rebase_in_progress(bookkeeping)


def test_product_conflict_next_to_bookkeeping_aborts(bookkeeping: Path) -> None:
    upstream = bookkeeping.parent / "upstream"
    (upstream / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(upstream, "add", "module.py")
    _git(upstream, "commit", "-m", "Upstream module")
    (bookkeeping / "module.py").write_text("VALUE = 3\n", encoding="utf-8")
    _git(bookkeeping, "add", "module.py")
    _git(bookkeeping, "commit", "-m", "Branch module")
    before = gitutils.head_sha(bookkeeping)

    exit_code, payload = _run(bookkeeping)

    assert exit_code == 1
    assert any("bookkeeping set" in note for note in payload["notes"])
    assert gitutils.head_sha(bookkeeping) == before


@pytest.fixture
def stacked(tmp_path: Path) -> Path:
    """A child branch stacked on a parent that was then squash-merged.

    ``parent`` adds two commits; upstream ``main`` receives them as **one**
    squash commit (different patch-id, so ``git rebase`` alone cannot skip
    them). ``child`` sits on top of the unsquashed parent tip.
    """
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "--initial-branch=main")
    _git(upstream, "config", "user.name", "Test")
    _git(upstream, "config", "user.email", "test@example.com")
    (upstream / "HISTORY.md").write_text(_HISTORY, encoding="utf-8")
    (upstream / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(upstream, "add", ".")
    _git(upstream, "commit", "-m", "Initial commit")

    clone = tmp_path / "work"
    _git(tmp_path, "clone", str(upstream), str(clone))
    _git(clone, "config", "user.name", "Test")
    _git(clone, "config", "user.email", "test@example.com")

    _git(clone, "switch", "-c", "100-parent")
    (clone / "module.py").write_text("VALUE = 1\nPARENT_A = True\n", encoding="utf-8")
    _git(clone, "commit", "-am", "parent a")
    (clone / "module.py").write_text(
        "VALUE = 1\nPARENT_A = True\nPARENT_B = True\n", encoding="utf-8"
    )
    _git(clone, "commit", "-am", "parent b")

    _git(clone, "switch", "-c", "101-child")
    (clone / "child.py").write_text("CHILD = True\n", encoding="utf-8")
    _git(clone, "add", "child.py")
    _git(clone, "commit", "-m", "child work")

    # Squash-merge the parent upstream: one commit with the parent's final tree.
    (upstream / "module.py").write_text(
        "VALUE = 1\nPARENT_A = True\nPARENT_B = True\n", encoding="utf-8"
    )
    _git(upstream, "commit", "-am", "parent squash (#100)")
    return clone


def test_stacked_child_auto_detects_squash_landed_parent(stacked: Path) -> None:
    exit_code, payload = _run(stacked)

    assert exit_code == 0, payload
    assert payload["base_detected"] is True
    assert payload["base"] == "100-parent"
    assert payload["dropped_commits"] == 2
    assert payload["action"] == "rebased"
    assert gitutils.rev_list_count(stacked, "origin/main", "HEAD") == 1
    assert (stacked / "child.py").exists()
    assert "PARENT_B" in (stacked / "module.py").read_text(encoding="utf-8")


def test_stacked_child_honours_explicit_base(stacked: Path) -> None:
    parent_tip = gitutils.branch_tip(stacked, "100-parent")
    assert parent_tip is not None
    _git(stacked, "branch", "-D", "100-parent")

    exit_code, payload = _run(stacked, "--base", parent_tip)

    assert exit_code == 0, payload
    assert payload["base_detected"] is False
    assert payload["dropped_commits"] == 2
    assert gitutils.rev_list_count(stacked, "origin/main", "HEAD") == 1


def test_explicit_base_must_be_an_ancestor(stacked: Path) -> None:
    exit_code, payload = _run(stacked, "--base", "origin/main")

    assert exit_code == 1
    assert any("not an ancestor" in note for note in payload["notes"])
