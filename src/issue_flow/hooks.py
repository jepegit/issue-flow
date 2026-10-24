"""Opt-in git hooks for the ``.issueflows/`` tracking tree (issue #101).

One hook ships today: ``pre-commit`` moves issue groups whose status file says
``- [x] Done`` from current-issues to solved-issues and stages the move, so the
routing lands in the same commit. Unfinished groups are never moved (parking is
``/iflow-pause``'s job, and a mid-work commit on an issue branch is normal).

The script lives at ``.issueflows/hooks/<name>`` and is symlinked into the
directory ``git rev-parse --git-path hooks`` reports, which respects
``core.hooksPath`` (Husky) and linked worktrees. Where symlinks fail (Windows
without developer mode) the script is copied instead. A hook that is not ours
is never overwritten: install refuses and prints the line to chain it.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from issue_flow import gitutils, tracking
from issue_flow.config import Settings
from issue_flow.templating import render_template

# Marker line every managed hook carries; ``uninstall`` and ``status`` key off it.
HOOK_MARKER = "issue-flow managed hook"
HOOK_NAMES = ("pre-commit",)
SKIP_ENV = "ISSUEFLOW_SKIP_HOOKS"


@dataclass
class HookResult:
    """Outcome of an install / uninstall / status call for one hook."""

    name: str
    action: str  # installed | copied | already | foreign | removed | absent | not_repo
    script: Path | None = None
    target: Path | None = None
    message: str = ""


def hooks_dir(project_root: Path) -> Path | None:
    """The hooks directory git uses for ``project_root``, or ``None`` outside a repo."""
    out = gitutils._stdout(
        [gitutils.GIT, "rev-parse", "--git-path", "hooks"], project_root
    )
    if not out:
        return None
    path = Path(out)
    return path if path.is_absolute() else (project_root / path).resolve()


def script_path(
    project_root: Path, name: str, settings: Settings | None = None
) -> Path:
    """Where the managed script for ``name`` lives inside the project."""
    settings = settings or Settings()
    return project_root / settings.issueflows_dir / "hooks" / name


def render_hook(project_root: Path, name: str, settings: Settings | None = None) -> str:
    """Render the managed script for ``name``."""
    settings = settings or Settings()
    top = gitutils.repo_root(project_root)
    rel = "."
    if top is not None:
        try:
            rel = project_root.resolve().relative_to(top.resolve()).as_posix() or "."
        except ValueError:
            rel = "."
    return render_template(
        f"hooks/{name}.sh.j2",
        {
            "issueflows_dir": settings.issueflows_dir,
            "current_issues_folder": settings.current_issues_folder,
            "solved_folder": settings.solved_folder,
            "project_rel": rel,
        },
    )


def write_script(
    project_root: Path, name: str, settings: Settings | None = None
) -> Path:
    """Render and write the managed script (executable). Returns its path."""
    path = script_path(project_root, name, settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_hook(project_root, name, settings), encoding="utf-8", newline="\n"
    )
    path.chmod(path.stat().st_mode | 0o111)
    return path


def is_managed(path: Path) -> bool:
    """True iff ``path`` is (or links to) a script carrying :data:`HOOK_MARKER`."""
    if (
        path.is_symlink()
        and Path(os.readlink(path)).parent.name == "hooks"
        and not path.exists()
    ):
        return True  # dangling link to our deleted script
    try:
        return HOOK_MARKER in path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def chain_snippet(project_root: Path, name: str) -> str:
    """The line to add to a foreign hook so it also runs ours."""
    return (
        f'"$(git rev-parse --show-toplevel)/{_script_rel(project_root, name)}" || true'
    )


def _script_rel(project_root: Path, name: str) -> str:
    script = script_path(project_root, name)
    top = gitutils.repo_root(project_root)
    if top is None:
        return script.as_posix()
    try:
        return script.resolve().relative_to(top.resolve()).as_posix()
    except ValueError:
        return script.as_posix()


def install(
    project_root: Path, name: str = "pre-commit", *, force: bool = False
) -> HookResult:
    """Write the managed script and link (or copy) it into git's hooks dir."""
    target_dir = hooks_dir(project_root)
    if target_dir is None:
        return HookResult(name, "not_repo", message="not a git repository")
    target = target_dir / name
    if (
        (target.exists() or target.is_symlink())
        and not is_managed(target)
        and not force
    ):
        return HookResult(
            name,
            "foreign",
            target=target,
            message=f"{target} is not an issue-flow hook; add this line to it: "
            + chain_snippet(project_root, name),
        )

    script = write_script(project_root, name)
    if target.is_symlink() and target.resolve() == script.resolve():
        return HookResult(name, "already", script=script, target=target)

    target_dir.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        target.unlink()
    try:
        target.symlink_to(os.path.relpath(script, target_dir))
        action = "installed"
    except OSError:
        shutil.copy2(script, target)
        action = "copied"
    return HookResult(name, action, script=script, target=target)


def uninstall(project_root: Path, name: str = "pre-commit") -> HookResult:
    """Remove our hook from git's hooks dir; a foreign hook is left alone."""
    target_dir = hooks_dir(project_root)
    if target_dir is None:
        return HookResult(name, "not_repo", message="not a git repository")
    target = target_dir / name
    if not (target.exists() or target.is_symlink()):
        return HookResult(name, "absent", target=target)
    if not is_managed(target):
        return HookResult(
            name,
            "foreign",
            target=target,
            message=f"{target} is not ours; left in place",
        )
    target.unlink()
    return HookResult(
        name, "removed", target=target, script=script_path(project_root, name)
    )


def status(project_root: Path, name: str = "pre-commit") -> HookResult:
    """Report whether our hook is installed, and how."""
    target_dir = hooks_dir(project_root)
    if target_dir is None:
        return HookResult(name, "not_repo", message="not a git repository")
    target = target_dir / name
    script = script_path(project_root, name)
    if not (target.exists() or target.is_symlink()):
        return HookResult(name, "absent", script=script, target=target)
    if not is_managed(target):
        return HookResult(name, "foreign", script=script, target=target)
    action = "installed" if target.is_symlink() else "copied"
    return HookResult(name, action, script=script, target=target)


def refresh_installed(project_root: Path) -> list[Path]:
    """Re-render scripts that are already installed (``issue-flow update``).

    Never installs a hook. A copied install is re-copied so it picks up the
    new script; a symlinked one follows the script automatically.
    """
    refreshed: list[Path] = []
    for name in HOOK_NAMES:
        if not script_path(project_root, name).exists():
            continue
        script = write_script(project_root, name)
        refreshed.append(script)
        current = status(project_root, name)
        if current.action == "copied" and current.target is not None:
            shutil.copy2(script, current.target)
    return refreshed


def run_pre_commit(project_root: Path) -> list[tracking.SweepMove]:
    """Move done groups to solved-issues and stage exactly those paths."""
    if os.environ.get(SKIP_ENV):
        return []
    settings = Settings()
    base = project_root / settings.issueflows_dir
    current = base / settings.current_issues_folder
    partly = base / settings.partly_solved_folder
    solved = base / settings.solved_folder
    moves = tracking.plan_sweep(current, partly, solved, done_only=True)
    if not moves:
        return []
    old_paths = [p for m in moves for p in m.files]
    moves = tracking.apply_sweep(moves, partly, solved)
    new_paths = [solved / p.name for p in old_paths]
    # Two calls so an old path that was never tracked cannot abort the add.
    gitutils._run(
        [
            gitutils.GIT,
            "rm",
            "--cached",
            "--quiet",
            "--ignore-unmatch",
            "--",
            *(str(p) for p in old_paths),
        ],
        project_root,
    )
    gitutils._run(
        [gitutils.GIT, "add", "--", *(str(p) for p in new_paths)], project_root
    )
    return moves
