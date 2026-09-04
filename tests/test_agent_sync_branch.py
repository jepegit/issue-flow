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
