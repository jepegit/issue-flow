"""Thin, best-effort wrappers around the ``git`` and ``gh`` CLIs.

The scaffolded workflow leans on a handful of read-only ``git`` / ``gh``
queries over and over (current branch, default branch, ahead/behind,
``owner/repo`` of the remote, fetching a GitHub issue). The ``issue-flow
status`` / ``issue-flow agent ...`` commands centralise those calls here so the
behaviour matches the templates exactly and degrades the same way: a missing
or unauthenticated ``gh`` must never hard-fail a command, it just yields
``None`` and the caller notes the gap.

The shell-out style mirrors :mod:`issue_flow.graphify`: ``shutil.which`` to
check availability, build an explicit argv, ``subprocess.run(check=False)``,
and translate failures into ``None`` rather than exceptions.
"""

from __future__ import annotations

import os

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

GIT = "git"
GH = "gh"

# Accepts the common remote URL shapes:
#   https://github.com/owner/repo(.git)
#   git@github.com:owner/repo(.git)
#   ssh://git@github.com/owner/repo(.git)
_REMOTE_RE = re.compile(
    r"""
    (?:[\w.+-]+@)?              # optional user@
    [\w.-]+                     # host
    [:/]                        # ':' for scp-style, '/' for URLs
    (?P<owner>[^/]+)/
    (?P<repo>[^/]+?)
    (?:\.git)?/?$
    """,
    re.VERBOSE,
)


def git_available() -> bool:
    """True iff the ``git`` CLI is on PATH."""
    return shutil.which(GIT) is not None


def gh_available() -> bool:
    """True iff the ``gh`` CLI is on PATH."""
    return shutil.which(GH) is not None


def _run(
    argv: list[str],
    cwd: Path,
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str] | None:
    """Run ``argv`` in ``cwd`` capturing text output.

    Returns ``None`` if the executable is missing or cannot be spawned;
    otherwise the completed process (even on a non-zero exit, so callers can
    inspect ``returncode``).

    Always decode as UTF-8 with ``errors="replace"``. Relying on the locale
    (Windows ``cp1252``) blows up on UTF-8 issue bodies from ``gh`` — see
    issue #216.
    """
    if shutil.which(argv[0]) is None:
        return None
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            input=input_text,
        )
    except (OSError, UnicodeError):
        return None


def _stream_text(value: str | None) -> str:
    """Strip a captured stream; treat ``None`` as empty (decode edge cases)."""
    return (value or "").strip()


def _stdout(argv: list[str], cwd: Path) -> str | None:
    """Return stripped stdout for a successful command, else ``None``."""
    result = _run(argv, cwd)
    if result is None or result.returncode != 0:
        return None
    if result.stdout is None:
        return None
    return result.stdout.strip()


def current_branch(cwd: Path) -> str | None:
    """Current branch name, or ``None`` (detached HEAD / not a repo / no git)."""
    branch = _stdout([GIT, "branch", "--show-current"], cwd)
    return branch or None


def default_branch(cwd: Path) -> str:
    """Best-effort default branch name.

    Prefers ``gh repo view``; falls back to the local ``origin/HEAD`` symbolic
    ref; finally defaults to ``main``. This mirrors the detection logic the
    slash commands describe.
    """
    gh_default = _stdout(
        [
            GH,
            "repo",
            "view",
            "--json",
            "defaultBranchRef",
            "-q",
            ".defaultBranchRef.name",
        ],
        cwd,
    )
    if gh_default:
        return gh_default

    symbolic = _stdout(
        [GIT, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        cwd,
    )
    if symbolic:
        return symbolic.removeprefix("origin/")

    return "main"


def head_sha(cwd: Path) -> str | None:
    """Full sha of HEAD, or ``None`` (no commits / not a repo / no git)."""
    return _stdout([GIT, "rev-parse", "HEAD"], cwd)


def latest_tag(cwd: Path) -> str | None:
    """Most recent version tag (best effort).

    Prefers the nearest tag reachable from HEAD (`git describe`), falling back
    to the highest version-sorted tag in the repo, else ``None``.
    """
    tag = _stdout([GIT, "describe", "--tags", "--abbrev=0"], cwd)
    if tag:
        return tag
    out = _stdout([GIT, "tag", "--list", "--sort=-v:refname"], cwd)
    if not out:
        return None
    first = out.splitlines()[0].strip()
    return first or None


def working_tree_clean(cwd: Path) -> bool | None:
    """True for a clean tree, False if dirty, ``None`` if git is unavailable."""
    result = _run([GIT, "status", "--porcelain"], cwd)
    if result is None or result.returncode != 0:
        return None
    return _stream_text(result.stdout) == ""


def fetch_prune(cwd: Path) -> bool:
    """Run ``git fetch --prune`` (best effort). True on success."""
    result = _run([GIT, "fetch", "--prune"], cwd)
    return result is not None and result.returncode == 0


def _unquote_porcelain_path(path: str) -> str:
    """Strip optional git porcelain double-quotes around a path."""
    path = path.strip()
    if len(path) >= 2 and path[0] == '"' and path[-1] == '"':
        return path[1:-1]
    return path


def _paths_from_porcelain_line(line: str) -> list[str]:
    """Extract path(s) from one ``git status --porcelain`` line.

    Rename/copy lines use ``XY old -> new`` (both sides matter for
    issueflows-only checks). Ordinary lines contribute a single path.
    """
    if not line.strip() or len(line) < 4:
        return []
    rest = line[3:].strip()
    if " -> " in rest:
        left, right = rest.split(" -> ", 1)
        return [
            _unquote_porcelain_path(left),
            _unquote_porcelain_path(right),
        ]
    return [_unquote_porcelain_path(rest)]


def dirty_paths(cwd: Path) -> list[str] | None:
    """Paths reported by ``git status --porcelain`` (empty list == clean).

    Rename/copy entries contribute **both** the old and new path. Returns
    ``None`` when git is unavailable or the command fails, so callers can
    distinguish "clean" from "unknown".
    """
    result = _run([GIT, "status", "--porcelain"], cwd)
    if result is None or result.returncode != 0:
        return None
    stdout = result.stdout or ""
    paths: list[str] = []
    for line in stdout.splitlines():
        paths.extend(_paths_from_porcelain_line(line))
    return paths


def issueflows_only_dirty(
    paths: list[str] | None,
    issueflows_dir: str = ".issueflows",
) -> bool | None:
    """True when every dirty path lives under ``issueflows_dir``.

    Empty ``paths`` is vacuously True (nothing outside the tree). ``None``
    paths (git unknown) returns ``None`` so callers can degrade.
    """
    if paths is None:
        return None
    root = issueflows_dir.replace("\\", "/").strip()
    while root.startswith("./"):
        root = root[2:]
    root = root.rstrip("/")
    if not root:
        return False
    prefix = root + "/"
    for raw in paths:
        normalized = raw.replace("\\", "/").strip()
        while normalized.startswith("./"):
            normalized = normalized[2:]
        if normalized == root or normalized.startswith(prefix):
            continue
        return False
    return True


def switch_branch(cwd: Path, branch: str) -> tuple[bool, str | None]:
    """Run ``git switch <branch>``. Returns ``(ok, error_message)``."""
    result = _run([GIT, "switch", branch], cwd)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or f"git switch {branch} failed"
    return True, None


def pull_ff_only(cwd: Path) -> tuple[bool, str | None]:
    """Run ``git pull --ff-only``. Returns ``(ok, error_message)``.

    A refusal here usually means the local branch and its upstream diverged;
    callers should surface the message and stop rather than force anything.
    """
    result = _run([GIT, "pull", "--ff-only"], cwd)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or "git pull --ff-only failed"
    return True, None


def repo_root(cwd: Path) -> Path | None:
    """Absolute path of the enclosing work tree, or ``None`` when unknown.

    Unmerged paths from ``git diff`` are reported relative to this, which may
    differ from the issue-flow project root in a nested layout.
    """
    out = _stdout([GIT, "rev-parse", "--show-toplevel"], cwd)
    return Path(out) if out else None


def has_commits(cwd: Path) -> bool:
    """True iff the repo has at least one commit reachable from HEAD."""
    return _stdout([GIT, "rev-parse", "--verify", "HEAD"], cwd) is not None


def gh_authenticated(cwd: Path) -> bool:
    """True iff ``gh auth status`` reports a logged-in account.

    ``gh auth status`` exits non-zero when no account is configured and never
    prompts, which makes it safe to probe. A missing ``gh`` reads as ``False``.
    """
    result = _run([GH, "auth", "status"], cwd)
    return result is not None and result.returncode == 0


def gh_account(cwd: Path) -> str | None:
    """Logged-in GitHub account name, or ``None`` when unauthenticated."""
    out = _stdout([GH, "api", "user", "-q", ".login"], cwd)
    return out or None


def rebase_onto(
    cwd: Path, ref: str, *, base: str | None = None
) -> tuple[bool, str | None]:
    """Run ``git rebase <ref>`` (or ``git rebase --onto <ref> <base>``).

    With ``base`` only the commits *after* ``base`` are replayed onto ``ref``
    — the stacked-PR case (issue #386): a child branch that still carries its
    parent's commits after the parent was squash-merged. Returns
    ``(ok, error_message)``.

    A non-zero exit is normally a conflict, not a broken repo: the caller
    inspects :func:`unmerged_paths` and decides whether to resolve or abort.
    """
    argv = [GIT, "rebase", "--onto", ref, base] if base else [GIT, "rebase", ref]
    result = _run(argv, cwd)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or f"git rebase {ref} failed"
    return True, None


def rev_list_count(cwd: Path, base_ref: str, target_ref: str) -> int | None:
    """Number of commits in ``base_ref..target_ref`` (``None`` when unknown)."""
    text = _stdout([GIT, "rev-list", "--count", f"{base_ref}..{target_ref}"], cwd)
    if text is None:
        return None
    try:
        return int(text.strip())
    except ValueError:
        return None


def rev_parse_verify(cwd: Path, ref: str) -> str | None:
    """Full SHA for ``ref`` when it resolves to a commit, else ``None``."""
    return _stdout([GIT, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], cwd)


def rebase_continue(cwd: Path) -> tuple[bool, str | None]:
    """Run ``git rebase --continue`` without opening an editor.

    ``core.editor=true`` keeps the replayed commit message as-is; an
    interactive editor would hang a non-interactive agent run.
    """
    result = _run([GIT, "-c", "core.editor=true", "rebase", "--continue"], cwd)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or "git rebase --continue failed"
    return True, None


def rebase_abort(cwd: Path) -> bool:
    """Run ``git rebase --abort`` (best effort). True on success."""
    result = _run([GIT, "rebase", "--abort"], cwd)
    return result is not None and result.returncode == 0


def rebase_in_progress(cwd: Path) -> bool:
    """True while a rebase is still stopped mid-way (conflict or edit)."""
    for name in ("rebase-merge", "rebase-apply"):
        path = _stdout([GIT, "rev-parse", "--git-path", name], cwd)
        if path and (cwd / path).exists():
            return True
    return False


def merge_ref(cwd: Path, ref: str) -> tuple[bool, str | None]:
    """Run ``git merge --no-edit <ref>``. Returns ``(ok, error_message)``."""
    result = _run([GIT, "merge", "--no-edit", ref], cwd)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or f"git merge {ref} failed"
    return True, None


def merge_abort(cwd: Path) -> bool:
    """Run ``git merge --abort`` (best effort). True on success."""
    result = _run([GIT, "merge", "--abort"], cwd)
    return result is not None and result.returncode == 0


def merge_continue(cwd: Path) -> tuple[bool, str | None]:
    """Commit a merge whose conflicts have just been staged."""
    result = _run([GIT, "-c", "core.editor=true", "commit", "--no-edit"], cwd)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or "git commit --no-edit failed"
    return True, None


def unmerged_paths(cwd: Path) -> list[str] | None:
    """Paths git reports as unmerged (``U``), or ``None`` when unknown."""
    result = _run([GIT, "diff", "--name-only", "--diff-filter=U"], cwd)
    if result is None or result.returncode != 0:
        return None
    stdout = result.stdout or ""
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def stage_paths(cwd: Path, paths: list[str]) -> tuple[bool, str | None]:
    """Run ``git add -- <paths>``. Returns ``(ok, error_message)``."""
    if not paths:
        return True, None
    result = _run([GIT, "add", "--", *paths], cwd)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or "git add failed"
    return True, None


def ahead_behind(cwd: Path, default: str) -> tuple[int, int] | None:
    """Return ``(ahead, behind)`` of HEAD vs ``origin/<default>``.

    Uses ``git rev-list --left-right --count origin/<default>...HEAD`` whose
    output is ``<behind>\\t<ahead>`` (left side is the upstream). Returns
    ``None`` when the comparison cannot be made (e.g. no remote-tracking ref).
    """
    out = _stdout(
        [GIT, "rev-list", "--left-right", "--count", f"origin/{default}...HEAD"],
        cwd,
    )
    if not out:
        return None
    parts = out.split()
    if len(parts) != 2:
        return None
    try:
        behind, ahead = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    return ahead, behind


DEFAULT_SYNC_NEVER = (
    "rebase default",
    "push --force default",
    "push default to skip CI",
)


def diff_name_only(
    cwd: Path, a: str, b: str, paths: list[str] | None = None
) -> list[str] | None:
    """Paths that differ between ``a`` and ``b``, or ``None`` on failure.

    ``paths`` limits the comparison to those pathspecs.
    """
    argv = [GIT, "diff", "--name-only", a, b]
    if paths:
        argv.extend(["--", *paths])
    out = _stdout(argv, cwd)
    if out is None:
        return None
    return [line.strip() for line in out.splitlines() if line.strip()]


def merge_base(cwd: Path, a: str, b: str) -> str | None:
    """Best common ancestor of ``a`` and ``b`` (``None`` when unrelated)."""
    return _stdout([GIT, "merge-base", a, b], cwd) or None


def content_landed(cwd: Path, ref: str, base_ref: str) -> bool | None:
    """True when every file ``ref`` changed since forking off ``base_ref`` is
    byte-identical on ``base_ref`` now.

    This is the squash-merge signature: the branch's commits have different
    patch-ids from the single squash commit, but the *end state* of the files
    it touched is exactly what landed. A file later edited upstream makes this
    ``False`` (a safe false negative — callers fall back to PR evidence).
    Returns ``None`` when the comparison cannot be made.
    """
    fork = merge_base(cwd, ref, base_ref)
    if fork is None:
        return None
    touched = diff_name_only(cwd, fork, ref)
    if touched is None:
        return None
    if not touched:
        return False
    remaining = diff_name_only(cwd, ref, base_ref, touched)
    if remaining is None:
        return None
    return not remaining


def unique_commit_details(
    cwd: Path,
    base_ref: str,
    target_ref: str = "HEAD",
) -> list[dict[str, Any]] | None:
    """Commits on ``target_ref`` not in ``base_ref`` with merge flag + paths.

    Returns ``None`` when the range cannot be listed.
    """
    out = _stdout(
        [GIT, "log", "--format=%h%x00%P%x00%s", f"{base_ref}..{target_ref}"],
        cwd,
    )
    if out is None:
        return None
    commits: list[dict[str, Any]] = []
    if not out:
        return commits
    for line in out.splitlines():
        parts = line.split("\0")
        if len(parts) < 3:
            continue
        sha, parents, subject = parts[0], parts[1], parts[2]
        is_merge = len([p for p in parents.split() if p]) > 1
        names = _stdout(
            [GIT, "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            cwd,
        )
        paths = [p.strip() for p in names.splitlines() if p.strip()] if names else []
        commits.append(
            {
                "sha": sha,
                "subject": subject,
                "is_merge": is_merge,
                "paths": paths,
            }
        )
    return commits


def classify_default_sync(
    cwd: Path,
    *,
    issueflows_dir: str = ".issueflows",
    default: str | None = None,
    fetch: bool = True,
) -> dict[str, Any]:
    """Classify unique commits on the default branch vs ``origin/<default>``.

    Read-only. Never mutates. Used by ``issue-flow agent default-sync`` and by
    switchback notes when ``git pull --ff-only`` fails or home is ahead.
    """
    notes: list[str] = []
    if fetch:
        fetch_prune(cwd)
    branch = default or default_branch(cwd)
    origin_ref = f"origin/{branch}"
    counts = ahead_behind(cwd, branch)
    ahead = counts[0] if counts else None
    behind = counts[1] if counts else None
    commits = unique_commit_details(cwd, origin_ref) or []
    tree_paths = diff_name_only(cwd, origin_ref, "HEAD")
    if tree_paths is None:
        tree_paths = []
        if counts is None:
            notes.append(f"could not compare HEAD to {origin_ref}")

    tracking = bool(issueflows_only_dirty(tree_paths, issueflows_dir))
    has_merge = any(bool(item.get("is_merge")) for item in commits)
    if not tracking:
        tree_class = "product"
    elif has_merge:
        tree_class = "obsolete_merge"
    else:
        tree_class = "tracking"

    ff_possible = ahead == 0
    if counts is None:
        action = "unknown"
    elif ahead == 0 and behind == 0:
        action = "even"
    elif ahead == 0 and behind is not None and behind > 0:
        action = "ff_only"
    elif behind == 0 and ahead is not None and ahead > 0:
        action = "report_ahead"
    elif tree_class == "product":
        action = "stop_product"
    elif tree_class == "obsolete_merge":
        action = "replay_tracking"
    else:
        action = "tracking_pr"

    return {
        "default_branch": branch,
        "ahead": ahead,
        "behind": behind,
        "ff_possible": ff_possible,
        "class": tree_class,
        "action": action,
        "commits": commits,
        "tree_paths": tree_paths,
        "never": list(DEFAULT_SYNC_NEVER),
        "notes": notes,
    }


def has_remote(cwd: Path, name: str = "origin") -> bool:
    """True when the repo at ``cwd`` has a remote called ``name``."""
    return bool(_stdout([GIT, "remote", "get-url", name], cwd))


def is_detached_head(cwd: Path) -> bool:
    """True when ``cwd`` is a repo with commits whose HEAD is detached."""
    if head_sha(cwd) is None:
        return False
    return current_branch(cwd) is None


def remote_owner_repo(cwd: Path) -> tuple[str, str] | None:
    """Parse ``owner``/``repo`` from the ``origin`` remote URL."""
    url = _stdout([GIT, "remote", "get-url", "origin"], cwd)
    if not url:
        return None
    match = _REMOTE_RE.search(url.strip())
    if not match:
        return None
    return match.group("owner"), match.group("repo")


def _owner_repo(cwd: Path, repo: str | None) -> tuple[str, str] | None:
    """Resolve ``(owner, name)`` from an explicit ``owner/repo`` or origin."""
    if repo and "/" in repo:
        owner, name = repo.split("/", 1)
        owner, name = owner.strip(), name.strip()
        if owner and name:
            return owner, name
    return remote_owner_repo(cwd)


def gh_issue_view(
    number: int, cwd: Path, repo: str | None = None
) -> dict[str, Any] | None:
    """Fetch a single GitHub issue as a dict (``title``/``body``/``url``/...).

    Returns ``None`` if ``gh`` is missing, unauthenticated, or the call fails.
    """
    argv = [
        GH,
        "issue",
        "view",
        str(number),
        "--json",
        "title,body,url,number,comments",
    ]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def gh_issue_state(number: int, cwd: Path, repo: str | None = None) -> str | None:
    """State (``open`` / ``closed``, lowercased) of one GitHub issue.

    Returns ``None`` when ``gh`` is missing, unauthenticated, or the issue
    cannot be fetched.
    """
    argv = [GH, "issue", "view", str(number), "--json", "state"]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        state = json.loads(out).get("state")
    except json.JSONDecodeError:
        return None
    return state.lower() if isinstance(state, str) else None


def gh_issue_meta(
    number: int, cwd: Path, repo: str | None = None
) -> dict[str, Any] | None:
    """Queue-planning metadata for one issue: number/title/state/body/labels/milestone."""
    argv = [
        GH,
        "issue",
        "view",
        str(number),
        "--json",
        "number,title,state,body,labels,milestone",
    ]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def gh_issue_list_meta(
    cwd: Path,
    repo: str | None = None,
    label: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]] | None:
    """Open issues with queue-planning metadata, optionally filtered by label."""
    argv = [
        GH,
        "issue",
        "list",
        "--state",
        "open",
        "--limit",
        str(limit),
        "--json",
        "number,title,state,body,labels",
    ]
    if label:
        argv += ["--label", label]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def gh_issue_list(
    cwd: Path, repo: str | None = None, limit: int = 100
) -> list[dict[str, Any]] | None:
    """List open GitHub issues as dicts, or ``None`` when unavailable."""
    argv = [
        GH,
        "issue",
        "list",
        "--state",
        "open",
        "--limit",
        str(limit),
        "--json",
        "number,title,labels,milestone,updatedAt",
    ]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def gh_issue_edit(
    number: int,
    cwd: Path,
    *,
    repo: str | None = None,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
    milestone: str | None = None,
) -> tuple[bool, str | None]:
    """Edit one issue's labels and/or milestone via ``gh issue edit``.

    Returns ``(success, error_message)``. ``error_message`` is stderr (or a
    short fallback) when ``gh`` fails.
    """
    argv = [GH, "issue", "edit", str(number)]
    if repo:
        argv += ["--repo", repo]
    for label in remove_labels or []:
        argv += ["--remove-label", label]
    for label in add_labels or []:
        argv += ["--add-label", label]
    if milestone:
        argv += ["--milestone", milestone]
    if len(argv) == 3 + (1 if repo else 0):
        return True, None
    result = _run(argv, cwd)
    if result is None:
        return False, "gh is not available"
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "gh issue edit failed").strip()
        return False, err
    return True, None


def gh_issue_close(
    number: int,
    cwd: Path,
    repo: str | None = None,
) -> tuple[bool, str | None]:
    """Close one GitHub issue. Returns ``(success, error_message)``."""
    argv = [GH, "issue", "close", str(number)]
    if repo:
        argv += ["--repo", repo]
    result = _run(argv, cwd)
    if result is None:
        return False, "gh is not available"
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "gh issue close failed").strip()
        return False, err
    return True, None


def gh_label_names(cwd: Path, repo: str | None = None) -> set[str] | None:
    """Return label names for the repo, or ``None`` when unavailable."""
    argv = [GH, "label", "list", "--json", "name", "--limit", "200"]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    return {
        str(item["name"])
        for item in data
        if isinstance(item, dict) and item.get("name")
    }


def gh_issue_database_id(number: int, cwd: Path, repo: str | None = None) -> int | None:
    """REST database id for an issue (not the issue number).

    GitHub's add-sub-issue endpoint requires this integer ``id``. ``gh api -f``
    stringifies values and 422s — callers must send JSON.
    """
    owner_repo = _owner_repo(cwd, repo)
    if owner_repo is None:
        return None
    owner, name = owner_repo
    out = _stdout(
        [GH, "api", f"repos/{owner}/{name}/issues/{number}", "--jq", ".id"],
        cwd,
    )
    if out is None:
        return None
    try:
        return int(out)
    except ValueError:
        return None


def gh_list_sub_issue_numbers(
    parent: int, cwd: Path, repo: str | None = None
) -> list[int] | None:
    """Issue numbers already linked as native sub-issues of ``parent``.

    Returns ``None`` when the API call fails (missing gh, 404, auth). An
    empty list means the parent currently has no sub-issues.
    """
    owner_repo = _owner_repo(cwd, repo)
    if owner_repo is None:
        return None
    owner, name = owner_repo
    out = _stdout(
        [
            GH,
            "api",
            f"repos/{owner}/{name}/issues/{parent}/sub_issues",
            "--jq",
            ".[].number",
        ],
        cwd,
    )
    if out is None:
        return None
    if not out:
        return []
    numbers: list[int] = []
    for line in out.splitlines():
        line = line.strip().strip('"')
        if not line:
            continue
        try:
            numbers.append(int(line))
        except ValueError:
            return None
    return numbers


def gh_add_sub_issue(
    parent: int,
    child_database_id: int,
    cwd: Path,
    repo: str | None = None,
) -> tuple[bool, str | None]:
    """Link an existing issue as a native GitHub sub-issue of ``parent``.

    ``child_database_id`` is the REST ``id``, not the issue number. Sends
    JSON on stdin via ``gh api --input -`` so the id stays an integer.
    """
    owner_repo = _owner_repo(cwd, repo)
    if owner_repo is None:
        return False, "could not resolve owner/repo"
    owner, name = owner_repo
    payload = json.dumps({"sub_issue_id": int(child_database_id)})
    result = _run(
        [
            GH,
            "api",
            f"repos/{owner}/{name}/issues/{parent}/sub_issues",
            "-X",
            "POST",
            "--input",
            "-",
        ],
        cwd,
        input_text=payload,
    )
    if result is None:
        return False, "gh is not available"
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "gh api sub_issues failed").strip()
        return False, err
    return True, None


def gh_label_create(
    name: str,
    cwd: Path,
    *,
    color: str,
    repo: str | None = None,
) -> tuple[bool, str | None]:
    """Create a GitHub label. Returns ``(success, error_message)``."""
    argv = [GH, "label", "create", name, "--color", color]
    if repo:
        argv += ["--repo", repo]
    result = _run(argv, cwd)
    if result is None:
        return False, "gh is not available"
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "gh label create failed").strip()
        return False, err
    return True, None


def gh_milestone_titles(cwd: Path, repo: str | None = None) -> list[str] | None:
    """Return open milestone titles for the repo, or ``None`` when unavailable."""
    if repo and "/" in repo:
        owner, name = repo.split("/", 1)
    else:
        remote = remote_owner_repo(cwd)
        if remote is None:
            return None
        owner, name = remote
    argv = [
        GH,
        "api",
        f"repos/{owner}/{name}/milestones",
        "--jq",
        ".[].title",
    ]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    if not out:
        return []
    return [line.strip().strip('"') for line in out.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Remote branch audit helpers (``/iflow-cleanup include GitHub``)
# ---------------------------------------------------------------------------


def list_origin_branches(cwd: Path) -> list[str] | None:
    """Short names of ``origin/*`` remote-tracking branches (no ``HEAD``).

    Returns ``None`` when git is unavailable or the query fails; an empty
    list when the remote has no branches yet.
    """
    out = _stdout(
        [
            GIT,
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/remotes/origin",
        ],
        cwd,
    )
    if out is None:
        return None
    names: list[str] = []
    for line in out.splitlines():
        ref = line.strip()
        if not ref or ref == "origin" or ref == "origin/HEAD":
            continue
        name = ref.removeprefix("origin/")
        if name and name != "HEAD":
            names.append(name)
    return names


def cherry_unique_count(cwd: Path, base_ref: str, target_ref: str) -> int | None:
    """Count commits on ``target_ref`` whose patch is not in ``base_ref``.

    Uses ``git cherry <base_ref> <target_ref>``: lines starting with ``+`` are
    unique; ``-`` means an equivalent patch is already upstream (which is how a
    squash-merged branch shows up). Both refs are passed through verbatim, so
    callers compare either remotes (``origin/foo``) or local branches. Returns
    ``None`` when the comparison cannot be made.
    """
    result = _run(
        [GIT, "cherry", base_ref, target_ref],
        cwd,
    )
    if result is None or result.returncode != 0:
        return None
    stdout = result.stdout or ""
    return sum(1 for line in stdout.splitlines() if line.startswith("+"))


def unique_commit_onelines(
    cwd: Path,
    base_ref: str,
    target_ref: str,
    *,
    limit: int = 20,
    no_merges: bool = False,
) -> list[str] | None:
    """``git log --oneline`` for commits on ``target_ref`` not in ``base_ref``.

    ``no_merges`` drops merge commits so the list matches what
    :func:`cherry_unique_count` counts (``git cherry`` ignores merges).
    """
    if limit < 1:
        limit = 20
    argv = [GIT, "log", "--oneline"]
    if no_merges:
        argv.append("--no-merges")
    argv += [f"{base_ref}..{target_ref}", f"-{limit}"]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def latest_unique_commit_date(cwd: Path, base_ref: str, target_ref: str) -> str | None:
    """Newest committer date (ISO 8601) among commits unique to ``target_ref``.

    Lets callers tell a squash-rewrite apart from work added *after* a PR
    merged: the former has no commit newer than the merge, the latter does.
    """
    out = _stdout(
        [
            GIT,
            "log",
            "--no-merges",
            "--format=%cI",
            f"{base_ref}..{target_ref}",
        ],
        cwd,
    )
    if not out:
        return None
    best: datetime | None = None
    best_raw: str | None = None
    for line in out.splitlines():
        raw = line.strip()
        if not raw:
            continue
        parsed = parse_iso8601(raw)
        if parsed is None:
            continue
        if best is None or parsed > best:
            best, best_raw = parsed, raw
    return best_raw


def parse_iso8601(value: str) -> datetime | None:
    """Parse an ISO 8601 timestamp (``Z`` suffix included) or return ``None``."""
    text = value.strip()
    if not text:
        return None
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def unique_diff_shortstat(cwd: Path, base_ref: str, target_ref: str) -> str | None:
    """``git diff --shortstat`` between ``base_ref...target_ref``."""
    out = _stdout(
        [
            GIT,
            "diff",
            "--shortstat",
            f"{base_ref}...{target_ref}",
        ],
        cwd,
    )
    if out is None:
        return None
    return out


def gh_prs_for_head(
    cwd: Path,
    head: str,
    repo: str | None = None,
    *,
    limit: int = 20,
) -> list[dict[str, Any]] | None:
    """PRs whose head ref is ``head`` (any state), or ``None`` if ``gh`` fails."""
    argv = [
        GH,
        "pr",
        "list",
        "--state",
        "all",
        "--head",
        head,
        "--limit",
        str(limit),
        "--json",
        "number,title,state,url,mergedAt",
    ]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def branch_is_protected(cwd: Path, branch: str, repo: str | None = None) -> bool | None:
    """Whether GitHub marks ``branch`` as protected.

    Returns ``None`` when the API call fails (callers treat as unknown and
    rely on push-delete failure reporting per the #163 plan).
    """
    if repo and "/" in repo:
        owner, name = repo.split("/", 1)
    else:
        remote = remote_owner_repo(cwd)
        if remote is None:
            return None
        owner, name = remote
    argv = [
        GH,
        "api",
        f"repos/{owner}/{name}/branches/{branch}",
        "--jq",
        ".protected",
    ]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    return out.strip().lower() == "true"


# ---------------------------------------------------------------------------
# Local branch audit helpers (``/iflow-cleanup`` Phase A, issue #243)
# ---------------------------------------------------------------------------


def list_local_branches(cwd: Path) -> list[str] | None:
    """Short names of local branches (``refs/heads/*``).

    Returns ``None`` when git is unavailable or the query fails.
    """
    out = _stdout(
        [
            GIT,
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/heads",
        ],
        cwd,
    )
    if out is None:
        return None
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_ancestor(cwd: Path, ref: str, upstream: str) -> bool | None:
    """Whether ``ref`` is reachable from ``upstream``.

    This is the same reachability test ``git branch -d`` applies, so a ``True``
    answer means a plain ``-d`` will succeed. Returns ``None`` when either ref
    cannot be resolved.
    """
    result = _run([GIT, "merge-base", "--is-ancestor", ref, upstream], cwd)
    if result is None:
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def branch_tip(cwd: Path, branch: str) -> str | None:
    """Short SHA at the tip of ``branch`` (the recovery handle for a delete)."""
    out = _stdout([GIT, "rev-parse", "--short", branch], cwd)
    if not out:
        return None
    return out.strip().splitlines()[0].strip() or None


def delete_branch(
    cwd: Path, branch: str, *, force: bool = False
) -> tuple[bool, str | None]:
    """Delete a local branch. ``force`` selects ``-D`` over ``-d``.

    Callers must gate ``force=True`` behind its own confirmation: it discards
    the reachability check that protects unmerged work.
    """
    flag = "-D" if force else "-d"
    result = _run([GIT, "branch", flag, branch], cwd)
    if result is None:
        return False, "git is not available"
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "git branch delete failed").strip()
        return False, err
    return True, None


def gh_prs_by_head(
    cwd: Path,
    repo: str | None = None,
    *,
    limit: int = 100,
) -> dict[str, list[dict[str, Any]]] | None:
    """All PRs indexed by head ref name, or ``None`` when ``gh`` fails.

    One ``gh pr list`` call for the whole repo, unlike per-branch
    :func:`gh_prs_for_head`: auditing every local branch otherwise costs one
    round trip per branch.
    """
    argv = [
        GH,
        "pr",
        "list",
        "--state",
        "all",
        "--limit",
        str(limit),
        "--json",
        "number,title,state,url,mergedAt,headRefName",
    ]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    by_head: dict[str, list[dict[str, Any]]] = {}
    for pr in data:
        if not isinstance(pr, dict):
            continue
        head = pr.get("headRefName")
        if not head:
            continue
        by_head.setdefault(str(head), []).append(pr)
    return by_head


# ---------------------------------------------------------------------------
# Worktrees (issue #255)
# ---------------------------------------------------------------------------


def _abs_rev_parse(cwd: Path, flag: str) -> Path | None:
    """Resolve a ``git rev-parse`` path flag to an absolute path."""
    out = _stdout([GIT, "rev-parse", flag], cwd)
    if not out:
        return None
    path = Path(out)
    if not path.is_absolute():
        path = cwd.resolve() / path
    return path.resolve()


def is_linked_worktree(cwd: Path) -> bool:
    """True when ``cwd`` is an added worktree, not the main checkout.

    Compares ``--git-dir`` to ``--git-common-dir``. Equal (or unreadable)
    means the main tree or not a repo.
    """
    git_dir = _abs_rev_parse(cwd, "--git-dir")
    common = _abs_rev_parse(cwd, "--git-common-dir")
    if git_dir is None or common is None:
        return False
    return git_dir != common


def worktree_home_path(cwd: Path) -> Path | None:
    """Absolute path of the main worktree (the folder that holds ``.git/``)."""
    common = _abs_rev_parse(cwd, "--git-common-dir")
    if common is None:
        return None
    if common.name == ".git":
        return common.parent
    listed = list_worktrees(cwd)
    if listed:
        return listed[0].path
    return None


@dataclass
class WorktreeInfo:
    path: Path
    branch: str | None
    head: str | None
    is_main: bool


def list_worktrees(cwd: Path) -> list[WorktreeInfo]:
    """Parse ``git worktree list --porcelain``. Empty list on failure."""
    result = _run([GIT, "worktree", "list", "--porcelain"], cwd)
    if result is None or result.returncode != 0 or not result.stdout:
        return []
    entries: list[WorktreeInfo] = []
    path: Path | None = None
    branch: str | None = None
    head: str | None = None

    def flush() -> None:
        nonlocal path, branch, head
        if path is None:
            return
        entries.append(
            WorktreeInfo(
                path=path,
                branch=branch,
                head=head,
                is_main=len(entries) == 0,
            )
        )
        path = None
        branch = None
        head = None

    for raw in result.stdout.splitlines():
        line = raw.rstrip("\n")
        if not line:
            flush()
            continue
        if line.startswith("worktree "):
            path = Path(line[len("worktree ") :]).resolve()
        elif line.startswith("HEAD "):
            head = line[len("HEAD ") :].strip()
        elif line.startswith("branch "):
            ref = line[len("branch ") :].strip()
            branch = ref.removeprefix("refs/heads/")
        elif line == "detached":
            branch = None
    flush()
    return entries


@dataclass(frozen=True)
class WorktreeLocation:
    """Where an issue worktree goes, and why (#328).

    ``reason`` is ``"sibling"`` (default, next to the repo), ``"workspace"``
    (next to the repo because it sits in a workspace folder), ``"worktrees_dir"``
    (inside the common worktrees folder), or ``"fallback"`` (a common folder
    was configured but unusable; ``note`` says why).
    """

    path: Path
    reason: str
    note: str | None = None


def resolve_worktree_location(
    home: Path,
    number: int,
    *,
    worktrees_dir: str = "",
    in_workspace: bool = True,
) -> WorktreeLocation:
    """Resolve the folder for issue ``number``'s worktree of the repo at ``home``.

    1. Repo inside a workspace folder (``issueflow-workspace.toml`` above it)
       and ``in_workspace`` → next to the repo (inside that folder).
    2. ``worktrees_dir`` set, absolute after ``~`` / env expansion, and an
       existing directory → ``<worktrees_dir>/<repo>-<N>``.
    3. Otherwise next to the repo (``../<repo>-<N>``). A configured but unusable
       ``worktrees_dir`` yields ``reason="fallback"`` with a ``note``. The
       folder is never created here.
    """
    from issue_flow.project import find_workspace_file

    resolved = home.resolve()
    name = f"{resolved.name}-{number}"
    sibling = resolved.parent / name

    if in_workspace and find_workspace_file(resolved.parent) is not None:
        return WorktreeLocation(sibling, "workspace")

    raw = (worktrees_dir or "").strip()
    if not raw:
        return WorktreeLocation(sibling, "sibling")

    expanded = Path(os.path.expandvars(os.path.expanduser(raw)))
    if not expanded.is_absolute():
        return WorktreeLocation(
            sibling,
            "fallback",
            f"worktrees_dir {raw!r} is not an absolute path; using the repo's parent folder",
        )
    if not expanded.is_dir():
        return WorktreeLocation(
            sibling,
            "fallback",
            f"worktrees_dir {str(expanded)!r} does not exist; using the repo's parent folder",
        )
    return WorktreeLocation(expanded.resolve() / name, "worktrees_dir")


def worktree_path_for_issue(
    home: Path,
    number: int,
    *,
    worktrees_dir: str = "",
    in_workspace: bool = True,
) -> Path:
    """Folder for issue ``number``'s worktree (``../<repo>-<N>`` by default)."""
    return resolve_worktree_location(
        home, number, worktrees_dir=worktrees_dir, in_workspace=in_workspace
    ).path


def add_worktree(
    home: Path,
    *,
    number: int,
    slug: str,
    start_point: str | None = None,
    target: Path | None = None,
) -> tuple[Path | None, bool, str | None]:
    """Add the issue worktree checked out at ``<N>-<slug>``.

    ``target`` defaults to ``../<repo>-<N>``; callers pass the result of
    :func:`resolve_worktree_location` to honour ``worktrees_dir`` (#328).
    Returns ``(path, created, error)``. Idempotent when that branch is already
    in a worktree or the target path is already that worktree. Never switches
    ``home``.
    """
    home = home.resolve()
    branch = f"{number}-{slug}"
    if target is None:
        target = worktree_path_for_issue(home, number)

    existing = list_worktrees(home)
    for info in existing:
        if info.branch == branch:
            return info.path, False, None
        if info.path == target:
            return info.path, False, None

    if target.exists():
        return None, False, f"target path already exists: {target}"

    fetch_prune(home)
    start = start_point or _worktree_start_point(home)
    if branch_exists(home, branch):
        result = _run([GIT, "worktree", "add", str(target), branch], home)
    else:
        result = _run(
            [GIT, "worktree", "add", "-b", branch, str(target), start],
            home,
        )
    if result is None:
        return None, False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return None, False, message or "git worktree add failed"
    return target, True, None


def branch_exists(cwd: Path, name: str) -> bool:
    """True iff ``refs/heads/<name>`` resolves."""
    return (
        _stdout([GIT, "rev-parse", "--verify", f"refs/heads/{name}"], cwd) is not None
    )


def _worktree_start_point(home: Path) -> str:
    default = default_branch(home)
    if _stdout([GIT, "rev-parse", "--verify", f"origin/{default}"], home):
        return f"origin/{default}"
    if _stdout([GIT, "rev-parse", "--verify", default], home):
        return default
    return "HEAD"


def remove_worktree(
    home: Path, path: Path, *, force: bool = False
) -> tuple[bool, str | None]:
    """``git worktree remove`` from the main repo. Refuses a dirty tree."""
    home = home.resolve()
    target = path.resolve()
    dirty = dirty_paths(target)
    if dirty is None:
        return False, f"not a git worktree: {target}"
    if dirty and not force:
        return False, f"worktree is dirty: {', '.join(dirty[:8])}"
    argv = [GIT, "worktree", "remove"]
    if force:
        argv.append("--force")
    argv.append(str(target))
    result = _run(argv, home)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or "git worktree remove failed"
    return True, None


def push_force_with_lease(
    cwd: Path,
    *,
    remote: str = "origin",
    branch: str | None = None,
) -> tuple[bool, str | None]:
    """``git push --force-with-lease`` for ``branch`` (or current HEAD)."""
    ref = branch or current_branch(cwd)
    if not ref:
        return False, "no branch to push (detached HEAD?)"
    result = _run(
        [GIT, "push", "--force-with-lease", remote, f"HEAD:refs/heads/{ref}"],
        cwd,
    )
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or "git push --force-with-lease failed"
    return True, None


def ensure_branch_worktree(
    home: Path,
    branch: str,
    *,
    remote: str = "origin",
) -> tuple[Path | None, bool, bool, str | None]:
    """Ensure ``branch`` is checked out in some worktree.

    Returns ``(path, created, ephemeral, error)``. ``ephemeral`` is true when
    this call created a temporary ``*-prsync-*`` worktree the caller may remove.
    Fetches ``refs/heads/<branch>`` from ``remote`` when the local ref is missing.
    """
    home = home.resolve()
    for info in list_worktrees(home):
        if info.branch == branch:
            return info.path, False, False, None

    if not branch_exists(home, branch):
        fetch = _run(
            [
                GIT,
                "fetch",
                remote,
                f"+refs/heads/{branch}:refs/heads/{branch}",
            ],
            home,
        )
        if fetch is None:
            return None, False, False, "git is not on PATH"
        if fetch.returncode != 0 and not branch_exists(home, branch):
            # Fall back to remote-tracking checkout name.
            if _stdout([GIT, "rev-parse", "--verify", f"{remote}/{branch}"], home):
                result = _run(
                    [
                        GIT,
                        "branch",
                        "--track",
                        branch,
                        f"{remote}/{branch}",
                    ],
                    home,
                )
                if result is None or result.returncode != 0:
                    message = (
                        _stream_text(result.stderr) if result else None
                    ) or f"missing branch {branch!r} on {remote}"
                    return None, False, False, message
            else:
                message = _stream_text(fetch.stderr) or f"cannot fetch {branch!r}"
                return None, False, False, message

    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-") or "branch"
    target = home.parent / f"{home.name}-prsync-{safe}"
    if target.exists():
        return None, False, False, f"target path already exists: {target}"

    result = _run([GIT, "worktree", "add", str(target), branch], home)
    if result is None:
        return None, False, False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return None, False, False, message or "git worktree add failed"
    return target, True, True, None


def gh_open_prs(
    cwd: Path,
    repo: str | None = None,
    *,
    limit: int = 50,
) -> list[dict[str, Any]] | None:
    """Open PRs with mergeability fields, or ``None`` if ``gh`` fails."""
    argv = [
        GH,
        "pr",
        "list",
        "--state",
        "open",
        "--limit",
        str(limit),
        "--json",
        "number,title,url,headRefName,mergeable,mergeStateStatus,baseRefName",
    ]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def gh_pr_view(
    cwd: Path,
    number: int | None = None,
    repo: str | None = None,
) -> dict[str, Any] | None:
    """One PR by number (or the current branch) with merge-ready fields."""
    argv = [GH, "pr", "view"]
    if number is not None:
        argv.append(str(number))
    argv += [
        "--json",
        "number,title,url,headRefName,mergeable,mergeStateStatus,"
        "baseRefName,state,isDraft,reviewDecision,statusCheckRollup",
    ]
    if repo:
        argv += ["--repo", repo]
    out = _stdout(argv, cwd)
    if out is None:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
