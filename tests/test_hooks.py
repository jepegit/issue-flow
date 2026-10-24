"""Tests for the opt-in git pre-commit hook (issue #101)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from issue_flow import hooks

CURRENT = Path(".issueflows/01-current-issues")
SOLVED = Path(".issueflows/03-solved-issues")


def _git(cwd: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=env
    )
    return result.stdout


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "commit", "-q", "--allow-empty", "-m", "root")
    return root


def _write(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _groups(root: Path) -> None:
    _write(root / CURRENT / "issue1_original.md", "# Issue #1: done one\n")
    _write(root / CURRENT / "issue1_status.md", "- [x] Done\n")
    _write(root / CURRENT / "issue2_status.md", "- [ ] Done\n")


def test_install_links_script_into_hooks_dir(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = hooks.install(root)

    target = root / ".git" / "hooks" / "pre-commit"
    script = root / ".issueflows" / "hooks" / "pre-commit"
    assert result.action in ("installed", "copied")
    assert hooks.HOOK_MARKER in script.read_text(encoding="utf-8")
    assert os.access(script, os.X_OK)
    if result.action == "installed":
        assert target.resolve() == script.resolve()
    assert hooks.install(root).action in ("already", "copied")
    assert hooks.status(root).action == result.action


def test_install_refuses_foreign_hook(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    foreign = root / ".git" / "hooks" / "pre-commit"
    _write(foreign, "#!/bin/sh\necho mine\n")

    result = hooks.install(root)

    assert result.action == "foreign"
    assert ".issueflows/hooks/pre-commit" in result.message
    assert foreign.read_text(encoding="utf-8") == "#!/bin/sh\necho mine\n"
    assert hooks.uninstall(root).action == "foreign"
    assert foreign.exists()
    assert hooks.install(root, force=True).action in ("installed", "copied")


def test_install_respects_core_hooks_path(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _git(root, "config", "core.hooksPath", ".husky")

    hooks.install(root)

    assert hooks.is_managed(root / ".husky" / "pre-commit")
    assert not (root / ".git" / "hooks" / "pre-commit").exists()


def test_install_from_linked_worktree(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    tree = tmp_path / "proj-7"
    _git(root, "worktree", "add", "-q", "-b", "7-x", str(tree))

    result = hooks.install(tree)

    assert result.action in ("installed", "copied")
    assert result.target is not None and hooks.is_managed(result.target)


def test_uninstall_removes_only_our_hook(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    hooks.install(root)

    assert hooks.uninstall(root).action == "removed"
    assert not (root / ".git" / "hooks" / "pre-commit").exists()
    assert hooks.uninstall(root).action == "absent"


def test_not_a_repo(tmp_path: Path) -> None:
    assert hooks.install(tmp_path).action == "not_repo"


def test_run_pre_commit_moves_done_and_stages(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _groups(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "groups")

    moves = hooks.run_pre_commit(root)

    assert [m.number for m in moves] == [1]
    assert (root / SOLVED / "issue1_status.md").exists()
    assert (root / CURRENT / "issue2_status.md").exists()
    staged = _git(root, "diff", "--cached", "--name-status", "-M")
    assert "issue1_status.md" in staged and "R" in staged
    assert "issue2" not in staged


def test_run_pre_commit_stages_untracked_group(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _groups(root)
    _write(root / "unrelated.txt")

    hooks.run_pre_commit(root)

    staged = _git(root, "diff", "--cached", "--name-only").split()
    assert sorted(staged) == [
        ".issueflows/03-solved-issues/issue1_original.md",
        ".issueflows/03-solved-issues/issue1_status.md",
    ]


def test_run_pre_commit_skip_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo(tmp_path)
    _groups(root)
    monkeypatch.setenv(hooks.SKIP_ENV, "1")

    assert hooks.run_pre_commit(root) == []
    assert (root / CURRENT / "issue1_status.md").exists()


def test_refresh_installed_rewrites_only_installed(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert hooks.refresh_installed(root) == []

    hooks.install(root)
    script = root / ".issueflows" / "hooks" / "pre-commit"
    script.write_text("stale\n", encoding="utf-8")

    assert hooks.refresh_installed(root) == [script]
    assert hooks.HOOK_MARKER in script.read_text(encoding="utf-8")


@pytest.mark.skipif(os.name == "nt", reason="POSIX hook script")
def test_git_commit_runs_hook_end_to_end(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    hooks.install(root)
    _groups(root)
    _git(root, "add", str(CURRENT))
    env = {
        **os.environ,
        "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}",
    }

    _git(root, "commit", "-q", "-m", "tick done", env=env)

    committed = _git(root, "show", "--name-only", "--format=", "HEAD").split()
    assert ".issueflows/03-solved-issues/issue1_status.md" in committed
    assert ".issueflows/01-current-issues/issue2_status.md" in committed
    assert _git(root, "status", "--porcelain") == "?? .issueflows/hooks/\n"
