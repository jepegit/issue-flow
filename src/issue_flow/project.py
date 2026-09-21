"""Project-root and workspace discovery for issue-flow scaffolds."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from issue_flow import gitutils


def unique_resolved_paths(paths: Iterable[Path]) -> list[Path]:
    """Absolute resolved paths, first-seen order (symlinks collapse)."""
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


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


DISCOVER_MAX_DEPTH = 4


def discover_issueflow_roots(
    start: Path,
    *,
    issueflows_dir: str = ".issueflows",
    max_depth: int = DISCOVER_MAX_DEPTH,
) -> list[Path]:
    """Find scaffold roots under ``start`` (no symlink follow, depth-capped)."""
    start = start.resolve()
    found: list[Path] = []

    def _is_scaffold(root: Path) -> bool:
        marker = root / issueflows_dir
        return marker.is_dir() and not marker.is_symlink()

    def walk(current: Path, depth: int) -> None:
        if depth > max_depth:
            return
        if _is_scaffold(current):
            found.append(current)
        if depth == max_depth:
            return
        try:
            children = sorted(current.iterdir())
        except OSError:
            return
        for child in children:
            if child.is_symlink() or not child.is_dir():
                continue
            walk(child.resolve(), depth + 1)

    if start.is_dir() and not start.is_symlink():
        walk(start, 0)
    return unique_resolved_paths(found)


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


CHILD_SCAFFOLDED = "scaffolded"
CHILD_UNSCAFFOLDED = "unscaffolded"
CHILD_SKIPPED = "skipped"


@dataclass(frozen=True)
class WorkspaceChild:
    """One immediate child of a workspace root during bootstrap classify."""

    name: str
    path: Path
    status: str
    reason: str | None = None


def classify_immediate_children(
    workspace_dir: Path,
    *,
    issueflows_dir: str = ".issueflows",
) -> list[WorkspaceChild]:
    """Classify immediate children as own-git members or skips.

    A member is an immediate child directory whose ``git`` top-level is that
    child (not an enclosing parent repo). Scaffolded vs unscaffolded is
    ``<issueflows_dir>/``. Non-dirs, symlinks, and non-git folders are
    skipped — bootstrap never ``git init`` s them.
    """
    root = workspace_dir.resolve()
    found: list[WorkspaceChild] = []
    try:
        children = sorted(root.iterdir())
    except OSError:
        return found

    for child in children:
        if not child.is_dir():
            continue
        if child.is_symlink():
            found.append(
                WorkspaceChild(
                    name=child.name,
                    path=child.resolve(),
                    status=CHILD_SKIPPED,
                    reason="symlink",
                )
            )
            continue
        resolved = child.resolve()
        toplevel = gitutils.repo_root(resolved)
        if toplevel is None:
            found.append(
                WorkspaceChild(
                    name=child.name,
                    path=resolved,
                    status=CHILD_SKIPPED,
                    reason="not a git repository",
                )
            )
            continue
        if toplevel.resolve() != resolved:
            found.append(
                WorkspaceChild(
                    name=child.name,
                    path=resolved,
                    status=CHILD_SKIPPED,
                    reason="enclosing repository",
                )
            )
            continue
        if (resolved / issueflows_dir).is_dir():
            found.append(
                WorkspaceChild(
                    name=child.name,
                    path=resolved,
                    status=CHILD_SCAFFOLDED,
                )
            )
        else:
            found.append(
                WorkspaceChild(
                    name=child.name,
                    path=resolved,
                    status=CHILD_UNSCAFFOLDED,
                )
            )
    return found


class CodeWorkspaceError(ValueError):
    """Invalid or unusable ``*.code-workspace`` file."""


class AmbiguousCodeWorkspaceError(CodeWorkspaceError):
    """More than one ``*.code-workspace`` and no explicit path."""


def resolve_code_workspace_path(
    workspace_root: Path, explicit: str | Path | None = None
) -> Path:
    """Pick the multi-root file to sync.

    Explicit path wins (relative to ``workspace_root``). Else the sole
    ``*.code-workspace`` in the root, else ``<root.name>.code-workspace``.
    Two or more matches with no explicit path raise
    :class:`AmbiguousCodeWorkspaceError`.
    """
    root = workspace_root.resolve()
    if explicit is not None and str(explicit) != "":
        path = Path(explicit)
        return path if path.is_absolute() else root / path
    matches = sorted(path for path in root.glob("*.code-workspace") if path.is_file())
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise AmbiguousCodeWorkspaceError(
            f"multiple *.code-workspace files ({names}); "
            "pass --code-workspace-path <file>"
        )
    return root / f"{root.name}.code-workspace"


def load_code_workspace(path: Path) -> dict[str, Any]:
    """Read an existing multi-root file, or return ``{}`` if missing.

    Raises :class:`CodeWorkspaceError` on invalid JSON so callers never
    clobber settings / extensions / launch by treating the file as empty.
    """
    if not path.is_file():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CodeWorkspaceError(f"invalid JSON in {path.name}: {exc.msg}") from exc
    if not isinstance(loaded, dict):
        raise CodeWorkspaceError(f"{path.name} must be a JSON object")
    return loaded


def sync_code_workspace(
    path: Path,
    members: list[str],
    *,
    drop_unknown: bool = False,
) -> dict[str, Any]:
    """Add missing member folders; keep settings and extra folders.

    ``drop_unknown`` (``--force``) removes relative folder entries that are
    not in ``members``. Absolute extra folders are left alone.
    """
    data = load_code_workspace(path)
    folders = data.get("folders")
    if not isinstance(folders, list):
        folders = []
    kept: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in folders:
        if not isinstance(item, dict):
            continue
        folder_path = str(item.get("path") or "")
        if not folder_path:
            continue
        if (
            drop_unknown
            and folder_path not in members
            and not Path(folder_path).is_absolute()
        ):
            continue
        kept.append(item)
        seen.add(folder_path)
    for name in members:
        if name not in seen:
            kept.append({"path": name})
            seen.add(name)
    data["folders"] = kept
    path.write_text(json.dumps(data, indent="\t") + "\n", encoding="utf-8")
    return {
        "path": str(path),
        "written": True,
        "folders": [str(item.get("path")) for item in kept],
    }
