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


def rebase_onto(cwd: Path, ref: str) -> tuple[bool, str | None]:
    """Run ``git rebase <ref>``. Returns ``(ok, error_message)``.

    A non-zero exit is normally a conflict, not a broken repo: the caller
    inspects :func:`unmerged_paths` and decides whether to resolve or abort.
    """
    result = _run([GIT, "rebase", ref], cwd)
    if result is None:
        return False, "git is not on PATH"
    if result.returncode != 0:
        message = _stream_text(result.stderr) or _stream_text(result.stdout)
        return False, message or f"git rebase {ref} failed"
    return True, None


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
