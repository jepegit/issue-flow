"""Project-root discovery for issue-flow scaffolds."""

from __future__ import annotations

from pathlib import Path


def find_project_root(
    start: Path,
    *,
    issueflows_dir: str = ".issueflows",
    current_issues_folder: str = "01-current-issues",
) -> Path | None:
    """Walk parents from ``start`` until an issue-flow scaffold is found.

    A directory qualifies when ``<issueflows_dir>/config.toml`` exists or
    ``<issueflows_dir>/<current_issues_folder>/`` is a directory.
    """
    current = start.resolve()
    if current.is_file():
        current = current.parent

    while True:
        base = current / issueflows_dir
        if (base / "config.toml").is_file() or (base / current_issues_folder).is_dir():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def list_scaffolded_siblings(
    project_root: Path,
    *,
    issueflows_dir: str = ".issueflows",
) -> list[str]:
    """Return absolute paths of sibling dirs that also contain ``issueflows_dir/``."""
    root = project_root.resolve()
    parent = root.parent
    siblings: list[str] = []
    try:
        entries = sorted(parent.iterdir())
    except OSError:
        return siblings
    for child in entries:
        if not child.is_dir():
            continue
        if child.resolve() == root:
            continue
        if (child / issueflows_dir).is_dir():
            siblings.append(str(child.resolve()))
    return siblings
