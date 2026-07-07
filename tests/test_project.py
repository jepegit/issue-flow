"""Tests for issue_flow.project — scaffold root discovery."""

from __future__ import annotations

from pathlib import Path

from issue_flow.project import find_project_root, list_scaffolded_siblings


def test_find_project_root_at_scaffold_root(tmp_path: Path) -> None:
    (tmp_path / ".issueflows" / "01-current-issues").mkdir(parents=True)
    assert find_project_root(tmp_path) == tmp_path.resolve()


def test_find_project_root_walks_up_from_nested_file(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)
    (tmp_path / ".issueflows").mkdir(parents=True)
    (tmp_path / ".issueflows" / "config.toml").write_text(
        "[issueflow]\n", encoding="utf-8"
    )
    assert find_project_root(nested / "mod.py") == tmp_path.resolve()


def test_find_project_root_none_outside_tree(tmp_path: Path) -> None:
    orphan = tmp_path / "orphan"
    orphan.mkdir()
    assert find_project_root(orphan) is None


def test_find_project_root_respects_custom_issueflows_dir(tmp_path: Path) -> None:
    custom = tmp_path / "tracker"
    (custom / "01-current-issues").mkdir(parents=True)
    assert find_project_root(tmp_path, issueflows_dir="tracker") == tmp_path.resolve()


def test_list_scaffolded_siblings(tmp_path: Path) -> None:
    repo_a = tmp_path / "alpha"
    repo_b = tmp_path / "beta"
    repo_c = tmp_path / "plain"
    for repo in (repo_a, repo_b, repo_c):
        repo.mkdir()
    (repo_a / ".issueflows").mkdir()
    (repo_b / ".issueflows").mkdir()

    siblings = list_scaffolded_siblings(repo_a)
    assert siblings == [str(repo_b.resolve())]
