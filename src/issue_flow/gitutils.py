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

import json
import re
import shutil
import subprocess
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


def _run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str] | None:
    """Run ``argv`` in ``cwd`` capturing text output.

    Returns ``None`` if the executable is missing or cannot be spawned;
    otherwise the completed process (even on a non-zero exit, so callers can
    inspect ``returncode``).
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
        )
    except OSError:
        return None


def _stdout(argv: list[str], cwd: Path) -> str | None:
    """Return stripped stdout for a successful command, else ``None``."""
    result = _run(argv, cwd)
    if result is None or result.returncode != 0:
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
    return result.stdout.strip() == ""


def fetch_prune(cwd: Path) -> bool:
    """Run ``git fetch --prune`` (best effort). True on success."""
    result = _run([GIT, "fetch", "--prune"], cwd)
    return result is not None and result.returncode == 0


def dirty_paths(cwd: Path) -> list[str] | None:
    """Paths reported by ``git status --porcelain`` (empty list == clean).

    Returns ``None`` when git is unavailable or the command fails, so callers
    can distinguish "clean" from "unknown".
    """
    result = _run([GIT, "status", "--porcelain"], cwd)
    if result is None or result.returncode != 0:
        return None
    return [line[3:].strip() for line in result.stdout.splitlines() if line.strip()]


def switch_branch(cwd: Path, branch: str) -> tuple[bool, str | None]:
    """Run ``git switch <branch>``. Returns ``(ok, error_message)``."""
    result = _run([GIT, "switch", branch], cwd)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
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
        message = result.stderr.strip() or result.stdout.strip()
        return False, message or "git pull --ff-only failed"
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


def remote_owner_repo(cwd: Path) -> tuple[str, str] | None:
    """Parse ``owner``/``repo`` from the ``origin`` remote URL."""
    url = _stdout([GIT, "remote", "get-url", "origin"], cwd)
    if not url:
        return None
    match = _REMOTE_RE.search(url.strip())
    if not match:
        return None
    return match.group("owner"), match.group("repo")


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


def cherry_unique_count(cwd: Path, default: str, branch: str) -> int | None:
    """Count commits on ``origin/<branch>`` not in ``origin/<default>``.

    Uses ``git cherry origin/<default> origin/<branch>``: lines starting with
    ``+`` are unique; ``-`` means already in the upstream. Returns ``None``
    when the comparison cannot be made.
    """
    result = _run(
        [GIT, "cherry", f"origin/{default}", f"origin/{branch}"],
        cwd,
    )
    if result is None or result.returncode != 0:
        return None
    return sum(1 for line in result.stdout.splitlines() if line.startswith("+"))


def unique_commit_onelines(
    cwd: Path, default: str, branch: str, *, limit: int = 20
) -> list[str] | None:
    """``git log --oneline`` for commits on ``origin/<branch>`` not in default."""
    if limit < 1:
        limit = 20
    out = _stdout(
        [
            GIT,
            "log",
            "--oneline",
            f"origin/{default}..origin/{branch}",
            f"-{limit}",
        ],
        cwd,
    )
    if out is None:
        return None
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def unique_diff_shortstat(cwd: Path, default: str, branch: str) -> str | None:
    """``git diff --shortstat`` between ``origin/<default>...origin/<branch>``."""
    out = _stdout(
        [
            GIT,
            "diff",
            "--shortstat",
            f"origin/{default}...origin/{branch}",
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
