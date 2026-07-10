"""Tests for issue_flow.project — scaffold root and workspace discovery."""

from __future__ import annotations

from pathlib import Path

from issue_flow.project import (
    WORKSPACE_FILENAME,
    discover_workspace,
    find_project_root,
    find_workspace_file,
    list_scaffolded_siblings,
    load_workspace,
)


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


# ---------------------------------------------------------------------------
# workspace registry (issue #126)
# ---------------------------------------------------------------------------


def _make_workspace(
    tmp_path: Path,
    *,
    body: str,
    scaffolded: tuple[str, ...] = ("alpha", "beta"),
    plain: tuple[str, ...] = ("plain",),
) -> Path:
    """Create a workspace dir with member repos and a registry file."""
    for name in scaffolded:
        (tmp_path / name / ".issueflows").mkdir(parents=True)
    for name in plain:
        (tmp_path / name).mkdir()
    workspace_file = tmp_path / WORKSPACE_FILENAME
    workspace_file.write_text(body, encoding="utf-8")
    return workspace_file


def test_find_workspace_file_walks_up(tmp_path: Path) -> None:
    workspace_file = _make_workspace(tmp_path, body="[workspace]\n")
    nested = tmp_path / "alpha" / "src"
    nested.mkdir(parents=True)
    assert find_workspace_file(nested) == workspace_file
    assert find_workspace_file(tmp_path) == workspace_file


def test_find_workspace_file_none_when_absent(tmp_path: Path) -> None:
    assert find_workspace_file(tmp_path) is None


def test_load_workspace_auto_discovers_members(tmp_path: Path) -> None:
    workspace_file = _make_workspace(tmp_path, body='[workspace]\ndefault = "alpha"\n')
    workspace = load_workspace(workspace_file)
    assert workspace is not None
    # Auto-discovery includes scaffolded children only, sorted.
    assert workspace.members == ["alpha", "beta"]
    assert workspace.default == "alpha"
    assert workspace.default_root() == tmp_path / "alpha"


def test_load_workspace_explicit_members_filter_unscaffolded(
    tmp_path: Path,
) -> None:
    workspace_file = _make_workspace(
        tmp_path,
        body=('[workspace]\ndefault = "beta"\nmembers = ["beta", "plain", "ghost"]\n'),
    )
    workspace = load_workspace(workspace_file)
    assert workspace is not None
    # "plain" has no scaffold and "ghost" does not exist.
    assert workspace.members == ["beta"]
    assert workspace.default_root() == tmp_path / "beta"


def test_load_workspace_ignores_unscaffolded_default(tmp_path: Path) -> None:
    workspace_file = _make_workspace(tmp_path, body='[workspace]\ndefault = "plain"\n')
    workspace = load_workspace(workspace_file)
    assert workspace is not None
    # A default that is not a scaffolded member must never resolve.
    assert workspace.default == "plain"
    assert workspace.default_root() is None


def test_load_workspace_broken_toml_degrades_to_none(tmp_path: Path) -> None:
    workspace_file = _make_workspace(tmp_path, body="[workspace\nnot toml")
    assert load_workspace(workspace_file) is None


def test_discover_workspace_from_nested_start(tmp_path: Path) -> None:
    _make_workspace(tmp_path, body='[workspace]\ndefault = "alpha"\n')
    nested = tmp_path / "beta" / "docs"
    nested.mkdir(parents=True)
    workspace = discover_workspace(nested)
    assert workspace is not None
    assert workspace.root == tmp_path.resolve()
    assert workspace.default == "alpha"
