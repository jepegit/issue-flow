"""Project-root and workspace discovery for issue-flow scaffolds."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# The multi-repo workspace registry (issue #126). Lives at the workspace
# root — the directory that *contains* the member repos — and names the
# member the lifecycle commands default to when invoked from outside any
# single scaffold. Deliberately not hidden: it is user-owned configuration.
WORKSPACE_FILENAME = "issueflow-workspace.toml"


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


def find_workspace_file(start: Path) -> Path | None:
    """Walk parents from ``start`` until an ``issueflow-workspace.toml`` is found.

    Mirrors :func:`find_project_root` so the two discoveries compose: a
    lifecycle command may sit inside a member repo (project root found first)
    or at the workspace root (only the workspace file is found).
    """
    current = start.resolve()
    if current.is_file():
        current = current.parent

    while True:
        candidate = current / WORKSPACE_FILENAME
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


@dataclass
class Workspace:
    """Parsed multi-repo workspace registry.

    ``members`` holds the *names* (relative folder names under the workspace
    root) of member repos that actually carry a scaffold; ``default`` is the
    configured default member name, or ``None`` when not set.
    """

    root: Path
    default: str | None = None
    members: list[str] = field(default_factory=list)

    def member_roots(self) -> list[Path]:
        return [self.root / name for name in self.members]

    def default_root(self) -> Path | None:
        """Absolute root of the default member, or ``None``.

        A configured default that is not a scaffolded member is ignored (the
        caller reports the gap) so a typo can never redirect git operations
        to an arbitrary directory.
        """
        if self.default is None or self.default not in self.members:
            return None
        return self.root / self.default


def load_workspace(
    workspace_file: Path,
    *,
    issueflows_dir: str = ".issueflows",
) -> Workspace | None:
    """Parse a workspace registry file into a :class:`Workspace`.

    Members listed in the file are kept only when they exist and carry an
    ``<issueflows_dir>/`` tree; when the ``members`` key is omitted, immediate
    child directories with a scaffold are auto-discovered. Returns ``None``
    when the file cannot be parsed (a broken registry must degrade to the
    pre-registry behaviour, never crash resolution).
    """
    root = workspace_file.parent.resolve()
    try:
        data = tomllib.loads(workspace_file.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None

    table = data.get("workspace")
    if not isinstance(table, dict):
        table = {}

    def _scaffolded(name: str) -> bool:
        return (root / name / issueflows_dir).is_dir()

    raw_members = table.get("members")
    members: list[str] = []
    if isinstance(raw_members, list):
        members = [m for m in raw_members if isinstance(m, str) and _scaffolded(m)]
    else:
        try:
            children = sorted(root.iterdir())
        except OSError:
            children = []
        members = [
            child.name
            for child in children
            if child.is_dir() and _scaffolded(child.name)
        ]

    default = table.get("default")
    if not isinstance(default, str):
        default = None

    return Workspace(root=root, default=default, members=members)


def discover_workspace(
    start: Path,
    *,
    issueflows_dir: str = ".issueflows",
) -> Workspace | None:
    """Find and parse the nearest workspace registry above ``start``."""
    workspace_file = find_workspace_file(start)
    if workspace_file is None:
        return None
    return load_workspace(workspace_file, issueflows_dir=issueflows_dir)


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
