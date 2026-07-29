"""Orchestrators behind the agent-facing CLI surface.

These functions back ``issue-flow status`` (human-facing, top-level) and the
``issue-flow agent ...`` sub-commands (``state`` / ``preflight`` / ``switchback`` /
``branches`` / ``version-plan`` / ``resolve`` / ``sweep`` / ``archive`` /
``capture``) that exist so AI agents can ask the tool for a deterministic
answer instead of re-deriving lifecycle state by hand on every run.

Each ``run_*`` returns a process exit code and emits either a short human
report (via :class:`rich.console.Console`) or a stable JSON object on stdout
when ``as_json`` is set. They all degrade gracefully: a missing/unauthenticated
``gh`` never hard-fails a read-only command, it just trims the GitHub section
and notes the gap — mirroring the scaffolded ``/iflow-status`` contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.markup import escape

from issue_flow import gitutils, modes, project, tracking
from issue_flow.config import Settings


def _folders(project_root: Path, settings: Settings) -> dict[str, Path]:
    base = project_root / settings.issueflows_dir
    return {
        "current": base / settings.current_issues_folder,
        "partly": base / settings.partly_solved_folder,
        "solved": base / settings.solved_folder,
    }


def _emit_json(console: Console, payload: dict[str, Any]) -> None:
    """Print a JSON payload to stdout without Rich markup interpretation."""
    console.print_json(json.dumps(payload))


# ---------------------------------------------------------------------------
# agent state
# ---------------------------------------------------------------------------


def run_state(project_root: Path, console: Console, as_json: bool) -> int:
    """Resolve the focus issue + lifecycle stage and the suggested next step."""
    settings = Settings()
    folders = _folders(project_root, settings)
    branch = gitutils.current_branch(project_root)
    focus = tracking.resolve_focus(folders["current"], branch)

    payload: dict[str, Any] = {
        "focus": focus.number,
        "resolved_via": focus.resolved_via,
        "branch": branch,
        "candidates": focus.candidates,
        "stage": None,
        "next_command": None,
        "files": {"original": False, "plan": False, "status": False, "done": False},
        "ambiguous": focus.resolved_via == "ambiguous",
    }

    if focus.number is not None:
        group = _focus_group(folders, focus.number)
        payload["stage"] = group.stage
        payload["next_command"] = group.next_command
        payload["files"] = {
            "original": group.original is not None,
            "plan": group.plan is not None,
            "status": bool(group.status_files),
            "done": group.is_done,
        }

    if as_json:
        _emit_json(console, payload)
        return 0

    if focus.resolved_via == "ambiguous":
        console.print(
            "[yellow]Ambiguous focus[/yellow]: multiple issue groups in "
            f"{settings.current_issues_folder} -> "
            f"{', '.join(f'#{n}' for n in focus.candidates)}. "
            "Specify which issue to act on."
        )
        return 0
    if focus.number is None:
        console.print(
            "[dim]No focus issue found.[/dim] Next step: "
            f"{tracking.STAGE_NEXT_COMMAND[tracking.STAGE_INIT]}"
        )
        return 0

    console.print(
        f"Focus #{payload['focus']} (via {payload['resolved_via']}) — "
        f"stage [bold]{payload['stage']}[/bold] -> {payload['next_command']}"
    )
    return 0


def _focus_group(folders: dict[str, Path], number: int) -> tracking.IssueGroup:
    """Build the focus group from current-issues files (empty group if none)."""
    groups = tracking.group_issue_files(folders["current"])
    return groups.get(
        number, tracking.IssueGroup(number=number, location=folders["current"].name)
    )


# ---------------------------------------------------------------------------
# agent preflight
# ---------------------------------------------------------------------------


def run_preflight(project_root: Path, console: Console, as_json: bool) -> int:
    """Report branch hygiene: default branch, clean/dirty, ahead/behind, stale."""
    settings = Settings()
    folders = _folders(project_root, settings)

    if not gitutils.git_available():
        payload = {"git_available": False, "notes": ["git is not on PATH"]}
        if as_json:
            _emit_json(console, payload)
        else:
            console.print("[yellow]git is not available[/yellow]; preflight skipped.")
        return 0

    gitutils.fetch_prune(project_root)
    branch = gitutils.current_branch(project_root)
    default = gitutils.default_branch(project_root)
    clean = gitutils.working_tree_clean(project_root)
    dirty = gitutils.dirty_paths(project_root)
    issueflows_only = gitutils.issueflows_only_dirty(dirty, settings.issueflows_dir)
    counts = gitutils.ahead_behind(project_root, default)
    issue_number = tracking.issue_number_from_branch(branch)

    notes: list[str] = []
    stale = False
    if issue_number is not None:
        partly = tracking.group_issue_files(folders["partly"])
        solved = tracking.group_issue_files(folders["solved"])
        if issue_number in partly or issue_number in solved:
            stale = True
            notes.append(
                f"branch looks stale: issue #{issue_number} is already archived "
                "under partly/solved — switch to the default branch before resuming."
            )

    payload = {
        "git_available": True,
        "current_branch": branch,
        "default_branch": default,
        "clean": clean,
        "dirty_paths": dirty if dirty is not None else [],
        "issueflows_only": issueflows_only,
        "ahead": counts[0] if counts else None,
        "behind": counts[1] if counts else None,
        "issue_number": issue_number,
        "stale": stale,
        "notes": notes,
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    tree = "clean" if clean else "dirty" if clean is not None else "unknown"
    counts_str = (
        f"{counts[0]} ahead / {counts[1]} behind" if counts else "ahead/behind unknown"
    )
    console.print(
        f"Branch [bold]{escape(branch) if branch else '(detached)'}[/bold] vs "
        f"origin/{escape(default)}: {counts_str}, working tree {tree}."
    )
    for note in notes:
        console.print(f"  [yellow]warn[/yellow]  {note}")
    return 0


# ---------------------------------------------------------------------------
# agent branches (remote audit for ``/iflow-cleanup include GitHub``)
# ---------------------------------------------------------------------------


def _pr_bucket(
    prs: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split PR dicts into (open, merged) summary rows."""
    open_prs: list[dict[str, Any]] = []
    merged_prs: list[dict[str, Any]] = []
    if not prs:
        return open_prs, merged_prs
    for pr in prs:
        if not isinstance(pr, dict):
            continue
        row = {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "url": pr.get("url"),
            "state": pr.get("state"),
            "mergedAt": pr.get("mergedAt"),
        }
        state = str(pr.get("state") or "").upper()
        if state == "OPEN":
            open_prs.append(row)
        elif state == "MERGED" or pr.get("mergedAt"):
            merged_prs.append(row)
    return open_prs, merged_prs


def run_branches(
    project_root: Path,
    console: Console,
    as_json: bool,
    *,
    fetch: bool = True,
    commit_limit: int = 20,
) -> int:
    """Classify ``origin/*`` remotes as deletable / unique-work / skipped.

    Read-only: never deletes remotes. Agents use the JSON payload for the
    Phase B confirm in ``/iflow-cleanup include GitHub``.
    """
    notes: list[str] = []
    remote = gitutils.remote_owner_repo(project_root)
    repo = f"{remote[0]}/{remote[1]}" if remote else None
    payload: dict[str, Any] = {
        "git_available": gitutils.git_available(),
        "gh_available": gitutils.gh_available(),
        "repo": repo,
        "default_branch": None,
        "fetched": False,
        "deletable": [],
        "unique_work": [],
        "skipped": [],
        "notes": notes,
    }

    def emit(exit_code: int) -> int:
        if as_json:
            _emit_json(console, payload)
            return exit_code
        return _render_branches_text(console, payload, exit_code)

    if not gitutils.git_available():
        notes.append("git is not on PATH")
        return emit(1)

    if fetch:
        payload["fetched"] = gitutils.fetch_prune(project_root)
        if not payload["fetched"]:
            notes.append("git fetch --prune failed or was skipped")

    default = gitutils.default_branch(project_root)
    payload["default_branch"] = default
    names = gitutils.list_origin_branches(project_root)
    if names is None:
        notes.append("could not list origin/* remote-tracking branches")
        return emit(1)

    current = gitutils.current_branch(project_root)

    for name in sorted(names):
        if name == default:
            payload["skipped"].append({"name": name, "reason": "default branch"})
            continue

        protected = gitutils.branch_is_protected(project_root, name, repo)
        if protected is True:
            payload["skipped"].append(
                {"name": name, "reason": "GitHub protected branch"}
            )
            continue

        prs = gitutils.gh_prs_for_head(project_root, name, repo)
        if prs is None and gitutils.gh_available():
            notes.append(f"gh pr list failed for head {name}")
        open_prs, merged_prs = _pr_bucket(prs)

        unique = gitutils.cherry_unique_count(project_root, default, name)
        if unique is None:
            payload["skipped"].append(
                {
                    "name": name,
                    "reason": f"could not compare to origin/{default}",
                }
            )
            continue

        if open_prs:
            commits = gitutils.unique_commit_onelines(
                project_root, default, name, limit=commit_limit
            )
            shortstat = gitutils.unique_diff_shortstat(project_root, default, name)
            payload["unique_work"].append(
                {
                    "name": name,
                    "unique_commits": unique,
                    "commits": commits or [],
                    "shortstat": shortstat or "",
                    "open_prs": open_prs,
                    "merged_prs": merged_prs,
                    "reason": "open pull request on this head",
                }
            )
            continue

        if unique == 0:
            reason = f"fully merged into origin/{default}"
            if merged_prs:
                reason += " (merged PR on GitHub)"
            entry: dict[str, Any] = {
                "name": name,
                "reason": reason,
                "merged_prs": merged_prs,
            }
            if current and name == current:
                entry["note"] = (
                    "matches current local branch name; delete remote only "
                    "after Phase A local cleanup if desired"
                )
            payload["deletable"].append(entry)
            continue

        commits = gitutils.unique_commit_onelines(
            project_root, default, name, limit=commit_limit
        )
        shortstat = gitutils.unique_diff_shortstat(project_root, default, name)
        payload["unique_work"].append(
            {
                "name": name,
                "unique_commits": unique,
                "commits": commits or [],
                "shortstat": shortstat or "",
                "open_prs": open_prs,
                "merged_prs": merged_prs,
                "reason": f"{unique} commit(s) not in origin/{default}",
            }
        )

    return emit(0)


def _render_branches_text(
    console: Console, payload: dict[str, Any], exit_code: int
) -> int:
    if exit_code != 0 and not payload.get("default_branch"):
        for note in payload.get("notes") or []:
            console.print(f"[yellow]{escape(str(note))}[/yellow]")
        return exit_code

    default = payload.get("default_branch") or "?"
    repo = payload.get("repo") or "(unknown repo)"
    console.print(
        f"Remote branch audit for [bold]{escape(str(repo))}[/bold] "
        f"vs origin/{escape(str(default))}:"
    )
    deletable = payload.get("deletable") or []
    unique = payload.get("unique_work") or []
    skipped = payload.get("skipped") or []
    console.print(
        f"  [green]deletable[/green] {len(deletable)}  ·  "
        f"[cyan]unique work[/cyan] {len(unique)}  ·  "
        f"[dim]skipped[/dim] {len(skipped)}"
    )
    for item in deletable:
        console.print(
            f"  [green]deletable[/green]  {escape(str(item.get('name')))} — "
            f"{escape(str(item.get('reason')))}"
        )
    for item in unique:
        console.print(
            f"  [cyan]unique[/cyan]     {escape(str(item.get('name')))} — "
            f"{escape(str(item.get('reason')))}"
        )
        for line in (item.get("commits") or [])[:5]:
            console.print(f"               {escape(str(line))}")
    for item in skipped:
        console.print(
            f"  [dim]skipped[/dim]    {escape(str(item.get('name')))} — "
            f"{escape(str(item.get('reason')))}"
        )
    for note in payload.get("notes") or []:
        console.print(f"  [yellow]note[/yellow]  {escape(str(note))}")
    return exit_code


# ---------------------------------------------------------------------------
# agent switchback
# ---------------------------------------------------------------------------


def run_switchback(project_root: Path, console: Console, as_json: bool) -> int:
    """Return to the default branch and fast-forward it — the mechanical half
    of ``/iflow-close``'s "switch back when safe" step.

    Mirrors the manual instructions exactly: refuse (exit 1) while the working
    tree is dirty so switching can never strand uncommitted work, otherwise
    ``git switch <default>`` followed by ``git pull --ff-only``. A refused
    fast-forward is surfaced, never forced. Branch deletion is deliberately
    out of scope — that stays in ``/iflow-cleanup``.
    """
    notes: list[str] = []
    payload: dict[str, Any] = {
        "git_available": gitutils.git_available(),
        "previous_branch": None,
        "default_branch": None,
        "switched": False,
        "pulled": False,
        "dirty_paths": [],
        "notes": notes,
    }

    def emit(exit_code: int) -> int:
        if as_json:
            _emit_json(console, payload)
        else:
            _render_switchback_text(console, payload, exit_code)
        return exit_code

    if not payload["git_available"]:
        notes.append("git is not on PATH")
        return emit(1)

    branch = gitutils.current_branch(project_root)
    default = gitutils.default_branch(project_root)
    dirty = gitutils.dirty_paths(project_root)
    payload["previous_branch"] = branch
    payload["default_branch"] = default

    if dirty is None:
        notes.append("could not read the working tree state (not a git repo?)")
        return emit(1)
    if dirty:
        payload["dirty_paths"] = dirty
        notes.append(
            "working tree is dirty; switching is unsafe until these changes "
            "are committed, stashed, or discarded."
        )
        return emit(1)

    if branch == default:
        notes.append(f"already on {default}")
    else:
        ok, error = gitutils.switch_branch(project_root, default)
        if not ok:
            notes.append(f"git switch {default} failed: {error}")
            return emit(1)
        payload["switched"] = True

    ok, error = gitutils.pull_ff_only(project_root)
    payload["pulled"] = ok
    if not ok:
        notes.append(
            f"git pull --ff-only refused: {error} — reconcile manually before "
            "continuing."
        )
        return emit(1)

    return emit(0)


def _render_switchback_text(
    console: Console, payload: dict[str, Any], exit_code: int
) -> None:
    if exit_code == 0:
        previous = payload["previous_branch"]
        came_from = (
            f" (from {escape(previous)})" if payload["switched"] and previous else ""
        )
        console.print(
            f"[green]ok[/green]  on [bold]{escape(payload['default_branch'])}[/bold]"
            f"{came_from}, fast-forwarded."
        )
    for path in payload["dirty_paths"]:
        console.print(f"  [yellow]dirty[/yellow]  {escape(path)}")
    for note in payload["notes"]:
        style = "red" if exit_code != 0 else "dim"
        console.print(f"  [{style}]{escape(note)}[/{style}]")


# ---------------------------------------------------------------------------
# agent resolve
# ---------------------------------------------------------------------------


def run_resolve(
    project_root: Path,
    console: Console,
    from_file: Path | None,
    as_json: bool,
) -> int:
    """Resolve the issue-flow project root, GitHub repo slug, and branch context.

    A nearest scaffold (walking up from the start directory / active file)
    always wins. Only when none is found does the workspace registry's
    ``default`` member kick in — the registry replaces the final "stop and
    ask" step of the resolution order, never an earlier one.
    """
    settings = Settings()
    start = from_file if from_file is not None else project_root
    resolved = project.find_project_root(
        start,
        issueflows_dir=settings.issueflows_dir,
        current_issues_folder=settings.current_issues_folder,
    )
    if resolved is None and from_file is not None:
        resolved = project.find_project_root(
            project_root,
            issueflows_dir=settings.issueflows_dir,
            current_issues_folder=settings.current_issues_folder,
        )

    workspace = project.discover_workspace(
        start, issueflows_dir=settings.issueflows_dir
    )
    if workspace is None and from_file is not None:
        workspace = project.discover_workspace(
            project_root, issueflows_dir=settings.issueflows_dir
        )

    via_workspace_default = False
    if resolved is None and workspace is not None:
        default_root = workspace.default_root()
        if default_root is not None:
            resolved = default_root
            via_workspace_default = True

    repo: str | None = None
    branch: str | None = None
    default_branch: str | None = None
    sibling_roots: list[str] = []

    if resolved is not None:
        owner_repo = gitutils.remote_owner_repo(resolved)
        if owner_repo:
            repo = f"{owner_repo[0]}/{owner_repo[1]}"
        if gitutils.git_available():
            branch = gitutils.current_branch(resolved)
            default_branch = gitutils.default_branch(resolved)
        sibling_roots = project.list_scaffolded_siblings(
            resolved, issueflows_dir=settings.issueflows_dir
        )

    payload: dict[str, Any] = {
        "project_root": str(resolved) if resolved else None,
        "repo": repo,
        "branch": branch,
        "default_branch": default_branch,
        "issueflows_dir": settings.issueflows_dir,
        "sibling_roots": sibling_roots,
        "workspace_root": str(workspace.root) if workspace else None,
        "workspace_default": workspace.default if workspace else None,
        "workspace_members": (
            [str(p) for p in workspace.member_roots()] if workspace else []
        ),
        "resolved_via_workspace_default": via_workspace_default,
    }

    if as_json:
        _emit_json(console, payload)
        return 0 if resolved is not None else 1

    if resolved is None:
        console.print(
            "[red]No issue-flow scaffold found[/red] walking up from "
            f"{start.resolve()}."
        )
        if workspace is not None and workspace.default is not None:
            console.print(
                f"  [yellow]warn[/yellow]  workspace registry names "
                f"'{escape(workspace.default)}' as default, but it is not a "
                "scaffolded member."
            )
        return 1

    console.print(f"[bold]Project root[/bold]: {resolved}")
    if via_workspace_default:
        console.print(
            f"  [dim](workspace default from {project.WORKSPACE_FILENAME})[/dim]"
        )
    if repo:
        console.print(f"[bold]Repo[/bold]: {repo}")
    if branch:
        console.print(f"[bold]Branch[/bold]: {branch}")
    if default_branch:
        console.print(f"[bold]Default branch[/bold]: {default_branch}")
    if sibling_roots:
        console.print(
            f"[bold]Sibling scaffolds[/bold]: {len(sibling_roots)} "
            "(run lifecycle commands once per repo)"
        )
    if workspace is not None and len(workspace.members) > 1:
        console.print(
            f"[bold]Workspace members[/bold]: {len(workspace.members)} "
            f"(default: {escape(workspace.default) if workspace.default else 'none'})"
        )
    return 0


# ---------------------------------------------------------------------------
# agent version-plan
# ---------------------------------------------------------------------------


def run_version_plan(
    project_root: Path,
    console: Console,
    levels: list[str],
    as_json: bool,
) -> int:
    """Plan the next version deterministically — the mechanical half of the
    release-strategy work in the iflow-version-bump skill.

    Read-only: detects the strategy from ``pyproject.toml``, reads the current
    version (static field, or latest git tag), applies the PEP 440 bump
    arithmetic, and reports the exact commands. It never edits files and never
    creates tags. The ``this-project.md`` release section still beats
    detection — that judgment stays agent-side; ``brief_release_section``
    tells the agent whether there is a section to read.
    """
    from issue_flow import versionplan

    settings = Settings()
    notes: list[str] = []

    strategy, reason, static_version = versionplan.detect_strategy(project_root)

    brief = (
        project_root
        / settings.issueflows_dir
        / settings.designs_folder
        / "this-project.md"
    )
    brief_section = "missing"
    if brief.is_file():
        try:
            text = brief.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if "## Release & version bump" in text:
            section = text.split("## Release & version bump", 1)[1]
            section = section.split("\n## ", 1)[0]
            brief_section = "todo" if "TODO" in section else "filled"
    if brief_section == "filled":
        notes.append(
            "this-project.md has a filled-in 'Release & version bump' section — "
            "it wins over the detected strategy; read it before acting."
        )

    payload: dict[str, Any] = {
        "strategy": strategy,
        "reason": reason,
        "brief_release_section": brief_section,
        "current_version": None,
        "latest_tag": None,
        "levels": [],
        "planned_version": None,
        "planned_tag": None,
        "commands": [],
        "notes": notes,
    }

    def emit(exit_code: int) -> int:
        if as_json:
            _emit_json(console, payload)
        else:
            _render_version_plan_text(console, payload, exit_code)
        return exit_code

    if strategy == "unknown":
        notes.append("no plan produced; resolve the strategy manually.")
        return emit(1)

    if strategy == "uv":
        current_text = static_version or ""
    else:
        tag = gitutils.latest_tag(project_root)
        payload["latest_tag"] = tag
        if tag is None:
            notes.append(
                "no git tags found; seed the series manually (e.g. "
                "`git tag v0.1.0`) before planning bumps."
            )
            return emit(1)
        current_text = tag

    current = versionplan.parse_version(current_text)
    payload["current_version"] = (
        current.formatted().lstrip("v") if current else current_text
    )
    if current is None:
        notes.append(
            f"could not parse '{current_text}' as a version; plan it manually."
        )
        return emit(1)

    if not levels:
        levels = versionplan.default_levels(current)
        notes.append(f"no level given; pre-release-aware default: {', '.join(levels)}.")
    payload["levels"] = sorted(levels, key=versionplan.LEVELS.index)

    planned, bump_notes = versionplan.bump(current, levels)
    notes.extend(bump_notes)
    if planned is None:
        return emit(1)

    if strategy == "uv":
        payload["planned_version"] = planned.formatted().lstrip("v")
        payload["commands"] = [
            "uv version " + " ".join(f"--bump {level}" for level in payload["levels"])
        ]
        notes.append(
            "uv is authoritative for static versions; the planned version is "
            "advisory (verify with `uv version --dry-run`)."
        )
    else:
        planned_tag = planned.formatted()
        payload["planned_version"] = planned_tag.lstrip("v")
        payload["planned_tag"] = planned_tag
        payload["commands"] = [
            f"git tag {planned_tag}",
            f"git push origin {planned_tag}",
            f"gh release create {planned_tag} --generate-notes  # optional",
        ]
        notes.append(
            "create the tag only after the PR merges, standing on the updated "
            "default branch — never on the issue branch."
        )

    return emit(0)


def _render_version_plan_text(
    console: Console, payload: dict[str, Any], exit_code: int
) -> None:
    console.print(
        f"[bold]Strategy[/bold]: {payload['strategy']} "
        f"[dim]({escape(str(payload['reason']))})[/dim]"
    )
    if payload["current_version"]:
        current = payload["current_version"]
        tag = payload["latest_tag"]
        suffix = f" (latest tag {escape(tag)})" if tag else ""
        console.print(f"[bold]Current[/bold]: {escape(str(current))}{suffix}")
    if payload["planned_version"]:
        levels = ", ".join(payload["levels"])
        console.print(
            f"[bold]Planned[/bold]: {escape(str(payload['planned_version']))} "
            f"[dim](levels: {levels})[/dim]"
        )
    for command in payload["commands"]:
        console.print(f"  $ {escape(command)}")
    for note in payload["notes"]:
        style = "yellow" if exit_code != 0 else "dim"
        console.print(f"  [{style}]{escape(note)}[/{style}]")


# ---------------------------------------------------------------------------
# agent epic-status
# ---------------------------------------------------------------------------


def run_epic_status(
    project_root: Path,
    console: Console,
    number: int,
    local: bool,
    as_json: bool,
) -> int:
    """Deterministic epic progress: stages, per-issue state, next candidates.

    Read-only. Parses ``epic<N>_plan.md`` (the contract the /iflow-epic skill
    writes) and — unless ``local`` — resolves each published issue's state via
    ``gh``. A missing/unauthenticated ``gh`` degrades to ``state: "unknown"``
    per issue rather than failing the command.
    """
    from issue_flow import epicplan

    settings = Settings()
    plan_path = (
        project_root
        / settings.issueflows_dir
        / settings.epics_folder
        / f"epic{number}_plan.md"
    )
    plan = epicplan.parse_epic_plan(plan_path)
    if plan is None:
        msg = f"no epic plan found at {plan_path}; draft one with /iflow-epic {number}."
        if as_json:
            _emit_json(console, {"epic": number, "error": msg})
        else:
            console.print(f"[red]error[/red]  {escape(msg)}")
        return 1

    repo_slug: str | None = None
    owner_repo = gitutils.remote_owner_repo(project_root)
    if owner_repo is not None:
        repo_slug = f"{owner_repo[0]}/{owner_repo[1]}"

    states: dict[int, str | None] = {}
    if not local:
        for stage in plan.stages:
            for spec in stage.issues:
                if spec.published is not None:
                    states[spec.published] = gitutils.gh_issue_state(
                        spec.published, project_root, repo_slug
                    )

    def spec_state(spec: epicplan.IssueSpec) -> str:
        if spec.published is None:
            return "unpublished"
        if local:
            return "published"
        state = states.get(spec.published)
        return state if state in ("open", "closed") else "unknown"

    def dep_closed(dep: int) -> bool:
        # A dependency counts as satisfied only when provably closed.
        return (not local) and states.get(dep) == "closed"

    stage_payloads: list[dict[str, Any]] = []
    current_stage: int | None = None
    next_candidates: list[int] = []
    for stage in plan.stages:
        issues: list[dict[str, Any]] = []
        done = bool(stage.issues)
        for spec in stage.issues:
            state = spec_state(spec)
            blocked_by = [dep for dep in spec.depends_on if not dep_closed(dep)]
            issues.append(
                {
                    "number": spec.published,
                    "title": spec.title,
                    "state": state,
                    "depends_on": spec.depends_on,
                    "placeholder_deps": [
                        f"stage {j} issue {k}" for j, k in spec.placeholder_deps
                    ],
                    "blocked_by": blocked_by,
                    "yolo": spec.yolo,
                    "goal": spec.goal,
                    "model": spec.model,
                }
            )
            if state != "closed":
                done = False
        stage_payloads.append(
            {
                "index": stage.index,
                "title": stage.title,
                "goal": stage.goal,
                "issues": issues,
                "done": done,
            }
        )
        if not done and current_stage is None:
            current_stage = stage.index
            for item in issues:
                if (
                    item["state"] == "open"
                    and not item["blocked_by"]
                    and not item["placeholder_deps"]
                ):
                    next_candidates.append(item["number"])

    payload: dict[str, Any] = {
        "epic": plan.number if plan.number is not None else number,
        "title": plan.title,
        "plan_status": plan.status,
        "local": local,
        "stages": stage_payloads,
        "current_stage": current_stage,
        "next_candidates": next_candidates,
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    console.print(
        f"[bold]Epic #{payload['epic']}[/bold] — {escape(plan.title)} "
        f"[dim](plan: {plan.status})[/dim]"
    )
    for stage in stage_payloads:
        marker = (
            "done"
            if stage["done"]
            else ("current" if stage["index"] == current_stage else "pending")
        )
        console.print(f"  Stage {stage['index']} — {escape(stage['title'])} [{marker}]")
        for item in stage["issues"]:
            number_str = f"#{item['number']}" if item["number"] else "(unpublished)"
            flags = " yolo" if item["yolo"] else ""
            blocked = (
                f" blocked by {', '.join(f'#{d}' for d in item['blocked_by'])}"
                if item["blocked_by"]
                else ""
            )
            console.print(
                f"    {number_str} [{item['state']}]{flags}{blocked} "
                f"{escape(item['title'])}"
            )
    if next_candidates:
        console.print(
            "[bold]Next candidates[/bold]: "
            + ", ".join(f"#{n}" for n in next_candidates)
        )
    return 0


# ---------------------------------------------------------------------------
# agent queue
# ---------------------------------------------------------------------------


def _label_names(labels: object) -> list[str]:
    """Normalize a ``gh`` labels field to a list of label name strings."""
    if not isinstance(labels, list):
        return []
    names: list[str] = []
    for label in labels:
        name = label.get("name") if isinstance(label, dict) else label
        if isinstance(name, str) and name:
            names.append(name)
    return names


def _has_label(labels: object, target: str) -> bool:
    """Return True when ``labels`` contains ``target`` (case-insensitive)."""
    needle = target.casefold()
    return any(name.casefold() == needle for name in _label_names(labels))


def _yolo_from_labels(labels: object, yolo_label: str = "yolo") -> bool:
    """Return True when the issue carries the configured yolo trigger label."""
    return _has_label(labels, yolo_label)


def run_label_candidates(
    project_root: Path,
    console: Console,
    kind: str,
    as_json: bool,
) -> int:
    """List open issues for a review kind (deterministic; no fitness judgment).

    ``kind`` selects which label to check. v1 supports ``yolo`` only (uses the
    project's resolved ``yolo_label``). Every open issue is returned, tagged
    with whether it already carries the target label.
    """
    settings = Settings()
    kind_norm = kind.strip().lower()
    if kind_norm != "yolo":
        msg = f"unknown review kind {kind!r}; supported: yolo."
        if as_json:
            _emit_json(console, {"error": msg, "kind": kind})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 2

    target_label = settings.resolve_yolo_label(project_root)
    label_flows = settings.resolve_label_flows(project_root)
    repo_slug: str | None = None
    owner_repo = gitutils.remote_owner_repo(project_root)
    if owner_repo is not None:
        repo_slug = f"{owner_repo[0]}/{owner_repo[1]}"

    listing = gitutils.gh_issue_list_meta(project_root, repo_slug)
    if listing is None:
        msg = "gh is unavailable or unauthenticated; cannot list issues."
        if as_json:
            _emit_json(console, {"error": msg, "kind": kind_norm})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 1

    repo_labels = gitutils.gh_label_names(project_root, repo_slug)
    label_exists: bool | None
    if repo_labels is None:
        label_exists = None
    else:
        label_exists = any(
            name.casefold() == target_label.casefold() for name in repo_labels
        )

    candidates: list[dict[str, Any]] = []
    for meta in listing:
        labels = _label_names(meta.get("labels"))
        candidates.append(
            {
                "number": meta.get("number", 0),
                "title": meta.get("title", ""),
                "labels": labels,
                "has_label": _has_label(meta.get("labels"), target_label),
            }
        )

    payload: dict[str, Any] = {
        "kind": kind_norm,
        "label": target_label,
        "label_exists": label_exists,
        "label_flows": label_flows,
        "repo": repo_slug,
        "candidates": candidates,
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    exists_note = (
        "present"
        if label_exists is True
        else "missing"
        if label_exists is False
        else "unknown (gh label list unavailable)"
    )
    console.print(
        f"kind={kind_norm} label={target_label!r} ({exists_note}) "
        f"label_flows={label_flows} open={len(candidates)}"
    )
    for entry in candidates:
        flag = " [has]" if entry["has_label"] else ""
        label_list = ", ".join(entry["labels"]) if entry["labels"] else "-"
        console.print(
            f"  #{entry['number']}{flag} {escape(str(entry['title']))} "
            f"({escape(label_list)})"
        )
    return 0


def run_label_apply(
    project_root: Path,
    console: Console,
    numbers: list[int],
    label: str,
    dry_run: bool,
    as_json: bool,
) -> int:
    """Apply one label to many issues (no judgment; idempotent add)."""
    if not numbers:
        msg = "give at least one issue number."
        if as_json:
            _emit_json(console, {"error": msg})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 2

    label_clean = label.strip()
    if not label_clean:
        msg = "--label must be a non-empty label name."
        if as_json:
            _emit_json(console, {"error": msg})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 2

    repo_slug: str | None = None
    owner_repo = gitutils.remote_owner_repo(project_root)
    if owner_repo is not None:
        repo_slug = f"{owner_repo[0]}/{owner_repo[1]}"

    results: list[dict[str, Any]] = []
    failures = 0
    for number in numbers:
        if dry_run:
            results.append(
                {
                    "number": number,
                    "ok": True,
                    "dry_run": True,
                    "error": None,
                }
            )
            continue
        ok, err = gitutils.gh_issue_edit(
            number,
            project_root,
            repo=repo_slug,
            add_labels=[label_clean],
        )
        if not ok:
            failures += 1
        results.append(
            {
                "number": number,
                "ok": ok,
                "dry_run": False,
                "error": err,
            }
        )

    payload: dict[str, Any] = {
        "label": label_clean,
        "repo": repo_slug,
        "dry_run": dry_run,
        "results": results,
    }

    if as_json:
        _emit_json(console, payload)
        return 1 if failures else 0

    mode = "dry-run" if dry_run else "apply"
    console.print(f"{mode} label={label_clean!r} on {len(numbers)} issue(s)")
    for entry in results:
        if entry["ok"]:
            console.print(f"  [green]ok[/green]  #{entry['number']}")
        else:
            console.print(
                f"  [red]fail[/red] #{entry['number']} — "
                f"{escape(str(entry['error'] or 'unknown error'))}"
            )
    return 1 if failures else 0


def run_queue(
    project_root: Path,
    console: Console,
    numbers: list[int],
    label: str | None,
    epic: int | None,
    as_json: bool,
) -> int:
    """Plan an execution queue for the cycling workflow (read-only).

    Exactly one source: explicit issue numbers, a label, or an epic's current
    stage. Dependencies come from ``Depends on #N`` / ``Blocked by #N`` lines
    (or the epic plan); the result is a deterministic topological order plus
    blocked / skipped / independent sets. Cycles abort with exit 1.
    """
    from issue_flow import epicplan, queueplan

    settings = Settings()
    yolo_label = settings.resolve_yolo_label(project_root)
    sources = sum(1 for source in (numbers, label, epic) if source)
    if sources != 1:
        msg = "give exactly one source: issue numbers, --label, or --epic."
        if as_json:
            _emit_json(console, {"error": msg})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 2

    repo_slug: str | None = None
    owner_repo = gitutils.remote_owner_repo(project_root)
    if owner_repo is not None:
        repo_slug = f"{owner_repo[0]}/{owner_repo[1]}"

    notes: list[str] = []
    items: list[queueplan.QueueItem] = []
    source: dict[str, Any]

    if numbers:
        source = {"type": "numbers", "value": numbers}
        missing: list[int] = []
        for number in numbers:
            meta = gitutils.gh_issue_meta(number, project_root, repo_slug)
            if meta is None:
                missing.append(number)
                continue
            items.append(
                queueplan.QueueItem(
                    number=meta.get("number", number),
                    title=meta.get("title", ""),
                    state=str(meta.get("state", "unknown")).lower(),
                    yolo=_yolo_from_labels(meta.get("labels"), yolo_label),
                    depends_on=queueplan.parse_dependencies(meta.get("body") or ""),
                )
            )
        if missing:
            # A typo must never shrink the confirmed queue silently.
            msg = (
                "could not fetch issue(s) "
                + ", ".join(f"#{n}" for n in missing)
                + " (gh missing/unauthenticated, or wrong number); refusing to "
                "plan a partial queue."
            )
            if as_json:
                _emit_json(console, {"source": source, "error": msg})
            else:
                console.print(f"[red]error[/red]  {msg}")
            return 1
    elif label:
        source = {"type": "label", "value": label}
        listing = gitutils.gh_issue_list_meta(project_root, repo_slug, label=label)
        if listing is None:
            msg = "gh is unavailable or unauthenticated; cannot list issues."
            if as_json:
                _emit_json(console, {"source": source, "error": msg})
            else:
                console.print(f"[red]error[/red]  {msg}")
            return 1
        for meta in listing:
            items.append(
                queueplan.QueueItem(
                    number=meta.get("number", 0),
                    title=meta.get("title", ""),
                    state=str(meta.get("state", "open")).lower(),
                    yolo=_yolo_from_labels(meta.get("labels"), yolo_label),
                    depends_on=queueplan.parse_dependencies(meta.get("body") or ""),
                )
            )
    else:
        source = {"type": "epic", "value": epic}
        plan_path = (
            project_root
            / settings.issueflows_dir
            / settings.epics_folder
            / f"epic{epic}_plan.md"
        )
        epic_plan = epicplan.parse_epic_plan(plan_path)
        if epic_plan is None:
            msg = f"no epic plan found at {plan_path}."
            if as_json:
                _emit_json(console, {"source": source, "error": msg})
            else:
                console.print(f"[red]error[/red]  {msg}")
            return 1
        # Current stage: the first stage whose published specs are not all
        # closed (or that still has unpublished specs).
        states: dict[int, str] = {}
        chosen = None
        for stage in epic_plan.stages:
            stage_done = bool(stage.issues)
            for spec in stage.issues:
                if spec.published is None:
                    stage_done = False
                    continue
                state = gitutils.gh_issue_state(spec.published, project_root, repo_slug)
                states[spec.published] = state or "unknown"
                if state != "closed":
                    stage_done = False
            if not stage_done:
                chosen = stage
                break
        if chosen is None:
            notes.append("every stage of the epic is complete; nothing to queue.")
        else:
            source["stage"] = chosen.index
            unpublished = [
                spec.title for spec in chosen.issues if spec.published is None
            ]
            if unpublished:
                notes.append(
                    "unpublished specs are not queueable: "
                    + "; ".join(unpublished)
                    + " — run the epic publish action first."
                )
            for spec in chosen.issues:
                if spec.published is None:
                    continue
                items.append(
                    queueplan.QueueItem(
                        number=spec.published,
                        title=spec.title,
                        state=states.get(spec.published, "unknown"),
                        yolo=spec.yolo,
                        depends_on=list(spec.depends_on),
                    )
                )

    plan = queueplan.build_queue(items)

    if plan.cycle:
        payload = {
            "source": source,
            "error": "dependency cycle detected",
            "cycle": plan.cycle,
        }
        if as_json:
            _emit_json(console, payload)
        else:
            console.print(
                "[red]error[/red]  dependency cycle detected among "
                + ", ".join(f"#{n}" for n in plan.cycle)
                + " — fix the Depends on lines; nothing was planned."
            )
        return 1

    payload = {
        "source": source,
        "queue": [
            {
                "order": position + 1,
                "number": item.number,
                "title": item.title,
                "yolo": item.yolo,
                "depends_on": item.depends_on,
            }
            for position, item in enumerate(plan.ordered)
        ],
        "blocked": [
            {
                "number": item.number,
                "title": item.title,
                "open_external_deps": deps,
            }
            for item, deps in plan.blocked
        ],
        "skipped_closed": [item.number for item in plan.skipped_closed],
        "independent": plan.independent,
        "notes": notes,
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    if not plan.ordered:
        console.print("[dim]Nothing to queue.[/dim]")
    for entry in payload["queue"]:
        flags = " [yolo]" if entry["yolo"] else ""
        deps = (
            f" (after {', '.join(f'#{d}' for d in entry['depends_on'])})"
            if entry["depends_on"]
            else ""
        )
        console.print(
            f"  {entry['order']}. #{entry['number']}{flags} "
            f"{escape(entry['title'])}{deps}"
        )
    for entry in payload["blocked"]:
        console.print(
            f"  [yellow]blocked[/yellow] #{entry['number']} "
            f"{escape(entry['title'])} — waiting on "
            + ", ".join(f"#{d}" for d in entry["open_external_deps"])
        )
    if plan.skipped_closed:
        console.print(
            "  [dim]skipped (closed): "
            + ", ".join(f"#{n}" for n in payload["skipped_closed"])
            + "[/dim]"
        )
    if plan.independent:
        console.print(
            "  [dim]independent (parallel-safe): "
            + ", ".join(f"#{n}" for n in plan.independent)
            + "[/dim]"
        )
    for note in notes:
        console.print(f"  [dim]{escape(note)}[/dim]")
    return 0


# ---------------------------------------------------------------------------
# workspace init
# ---------------------------------------------------------------------------


def run_workspace_init(
    workspace_dir: Path,
    console: Console,
    default: str | None,
    force: bool,
    as_json: bool,
) -> int:
    """Create the multi-repo workspace registry (``issueflow-workspace.toml``).

    Members are auto-discovered: immediate child directories that carry an
    ``<issueflows_dir>/`` tree. Refuses when there are none (the command was
    probably run in the wrong directory) and when ``--default`` names
    something that is not a scaffolded member (a typo must never redirect
    lifecycle commands). An existing file is kept unless ``--force``.
    """
    import tomlkit

    settings = Settings()
    root = workspace_dir.resolve()
    target = root / project.WORKSPACE_FILENAME

    try:
        children = sorted(root.iterdir())
    except OSError:
        children = []
    members = [
        child.name
        for child in children
        if child.is_dir() and (child / settings.issueflows_dir).is_dir()
    ]

    def _fail(msg: str) -> int:
        if as_json:
            _emit_json(
                console,
                {"written": False, "path": str(target), "error": msg},
            )
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 1

    if not members:
        return _fail(
            f"no scaffolded member repos found under {root} — run "
            "`issue-flow init` inside the member repos first, and run this "
            "command from the workspace root (the folder that contains them)."
        )

    if default is not None and default not in members:
        return _fail(
            f"--default '{default}' is not a scaffolded member; "
            f"available members: {', '.join(members)}."
        )

    if target.exists() and not force:
        return _fail(f"{target} already exists; pass --force to overwrite it.")

    if default is None and len(members) == 1:
        default = members[0]

    doc = tomlkit.document()
    doc.add(tomlkit.comment("issue-flow multi-repo workspace registry."))
    doc.add(
        tomlkit.comment(
            "`default` names the member repo lifecycle commands target when"
        )
    )
    doc.add(
        tomlkit.comment(
            "invoked from the workspace root; explicit root:/repo: hints and"
        )
    )
    doc.add(
        tomlkit.comment(
            "the nearest scaffold always win. Omit `members` to auto-discover."
        )
    )
    table = tomlkit.table()
    if default is not None:
        table["default"] = default
    else:
        table.add(tomlkit.comment('default = "<one of the members below>"'))
    table["members"] = members
    doc["workspace"] = table
    target.write_text(tomlkit.dumps(doc), encoding="utf-8")

    payload = {
        "written": True,
        "path": str(target),
        "workspace_root": str(root),
        "default": default,
        "members": members,
    }
    if as_json:
        _emit_json(console, payload)
        return 0

    console.print(f"[green]wrote[/green]  {target}")
    console.print(
        f"  members: {', '.join(members)} — default: "
        f"{escape(default) if default else '(none; edit the file to set one)'}"
    )
    return 0


def run_workspace_update(
    workspace_dir: Path,
    console: Console,
    skip_dep_check: bool,
    editors: list[str] | None,
    as_json: bool,
) -> int:
    """Refresh issue-flow scaffolds in every scaffolded workspace member.

      Discovers ``issueflow-workspace.toml`` above ``workspace_dir``, runs
      :func:`issue_flow.init.run_update` on each member that carries a
      ``.issueflows/`` tree, and aggregates per-member success. One dependency
      check runs up front (unless ``skip_dep_check``); individual member
    failures do not abort the rest.
    """
    import typer

    from issue_flow.init import _dependency_gate, run_update

    start = workspace_dir.resolve()
    workspace = project.discover_workspace(start)

    def _fail(msg: str) -> int:
        if as_json:
            _emit_json(
                console,
                {
                    "ok": False,
                    "error": msg,
                    "workspace_root": None,
                    "members": [],
                    "ok_count": 0,
                    "fail_count": 0,
                },
            )
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 1

    if workspace is None:
        return _fail(
            f"no {project.WORKSPACE_FILENAME} found above {start} — run "
            f"`issue-flow workspace init` from the workspace root first."
        )

    member_roots = workspace.member_roots()
    if not member_roots:
        return _fail(
            f"no scaffolded member repos found under {workspace.root} — run "
            "`issue-flow init` inside the member repos first."
        )

    if not skip_dep_check and not _dependency_gate(skip_dep_check=False):
        return 1

    import issue_flow.console_io as console_module

    def _run_member_update(root: Path) -> None:
        if as_json:
            quiet = Console(quiet=True)
            saved = console_module.console
            console_module.console = quiet
            try:
                run_update(root, skip_dep_check=True, editors=editors)
            finally:
                console_module.console = saved
        else:
            run_update(root, skip_dep_check=True, editors=editors)

    if not as_json:
        console.print(
            f"\n[bold]Updating issue-flow scaffolds in workspace "
            f"[cyan]{workspace.root}[/cyan][/bold]"
        )
        console.print(f"[dim]{len(member_roots)} member(s)[/dim]\n")

    results: list[dict[str, Any]] = []
    ok_count = 0
    fail_count = 0

    for name, root in zip(workspace.members, member_roots, strict=True):
        entry: dict[str, Any] = {"name": name, "path": str(root)}
        try:
            _run_member_update(root)
            entry["ok"] = True
            ok_count += 1
        except typer.Exit as exc:
            entry["ok"] = False
            entry["error"] = f"update failed (exit {exc.exit_code})"
            fail_count += 1
        results.append(entry)

    payload = {
        "ok": fail_count == 0,
        "workspace_root": str(workspace.root),
        "members": results,
        "ok_count": ok_count,
        "fail_count": fail_count,
    }

    if as_json:
        _emit_json(console, payload)
        return 0 if fail_count == 0 else 1

    console.print()
    if fail_count == 0:
        console.print(
            f"[bold green]Updated {ok_count}/{len(member_roots)} member(s).[/bold green]"
        )
    else:
        console.print(
            f"[bold yellow]Updated {ok_count}/{len(member_roots)} member(s); "
            f"{fail_count} failed.[/bold yellow]"
        )
        for entry in results:
            if not entry.get("ok"):
                console.print(
                    f"  [red]fail[/red]  {escape(entry['name'])}: "
                    f"{escape(str(entry.get('error', 'unknown error')))}"
                )
    return 0 if fail_count == 0 else 1


# ---------------------------------------------------------------------------
# agent sweep
# ---------------------------------------------------------------------------


def run_sweep(
    project_root: Path,
    console: Console,
    except_number: int | None,
    dry_run: bool,
    as_json: bool,
) -> int:
    """Archive non-focus issue groups from current-issues to partly/solved."""
    settings = Settings()
    folders = _folders(project_root, settings)

    moves = tracking.plan_sweep(
        folders["current"], folders["partly"], folders["solved"], except_number
    )
    if not dry_run and moves:
        moves = tracking.apply_sweep(moves, folders["partly"], folders["solved"])

    payload = {
        "dry_run": dry_run,
        "except": except_number,
        "moves": [
            {
                "issue": m.number,
                "done": m.done,
                "from": m.source,
                "to": m.destination,
                "files": [p.name for p in m.files],
            }
            for m in moves
        ],
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    if not moves:
        console.print("[dim]Nothing to sweep.[/dim]")
        return 0
    verb = "Would move" if dry_run else "Moved"
    for m in moves:
        console.print(
            f"  {verb} #{m.number} ({'done' if m.done else 'not done'}): "
            f"{m.source} -> {m.destination}"
        )
    return 0


# ---------------------------------------------------------------------------
# doctor / agent audit + repair
# ---------------------------------------------------------------------------


def _finding_payload(finding: tracking.DirtyFinding) -> dict[str, Any]:
    return {
        "code": finding.code,
        "severity": finding.severity,
        "message": finding.message,
        "issue_numbers": finding.issue_numbers,
        "repairable": finding.repairable,
        "suggested_command": finding.suggested_command,
    }


def _audit_context(
    project_root: Path, settings: Settings
) -> tuple[dict[str, Path], Path, str | None]:
    folders = _folders(project_root, settings)
    base = project_root / settings.issueflows_dir
    branch = gitutils.current_branch(project_root)
    return folders, base, branch


def run_audit(project_root: Path, console: Console, as_json: bool) -> int:
    """Audit ``.issueflows/`` for dirty conditions."""
    settings = Settings()
    folders, base, branch = _audit_context(project_root, settings)
    findings = tracking.audit_issueflows(
        base,
        folders["current"],
        folders["partly"],
        folders["solved"],
        branch,
        expected_subdirs=settings.issueflows_subdirs,
    )
    has_error = any(f.severity == tracking.SEVERITY_ERROR for f in findings)
    payload: dict[str, Any] = {
        "findings": [_finding_payload(f) for f in findings],
        "has_error": has_error,
        "count": len(findings),
    }

    if as_json:
        _emit_json(console, payload)
        return 1 if has_error else 0

    if not findings:
        console.print("[green]OK[/green]  No dirty conditions detected.")
        return 0

    for finding in findings:
        color = {
            tracking.SEVERITY_ERROR: "red",
            tracking.SEVERITY_WARN: "yellow",
            tracking.SEVERITY_INFO: "dim",
        }.get(finding.severity, "white")
        console.print(
            f"  [{color}]{finding.severity}[/{color}]  "
            f"{escape(finding.code)}: {escape(finding.message)}"
        )
        if finding.suggested_command:
            console.print(f"         -> {escape(finding.suggested_command)}")
    return 1 if has_error else 0


def run_repair(
    project_root: Path,
    console: Console,
    except_number: int | None,
    dry_run: bool,
    as_json: bool,
) -> int:
    """Apply safe repairs: mkdir missing folders + sweep non-focus groups."""
    settings = Settings()
    folders, base, branch = _audit_context(project_root, settings)

    plan, error = tracking.plan_repairs(
        base,
        folders["current"],
        folders["partly"],
        folders["solved"],
        branch,
        except_number,
        expected_subdirs=settings.issueflows_subdirs,
    )
    if error:
        if as_json:
            _emit_json(console, {"repaired": False, "error": error})
        else:
            console.print(f"[red]error[/red]  {escape(error)}")
        return 1

    assert plan is not None
    tracking.apply_repairs(plan, folders["partly"], folders["solved"], dry_run=dry_run)

    payload: dict[str, Any] = {
        "dry_run": dry_run,
        "focus": plan.focus,
        "mkdirs": [m.folder_name for m in plan.mkdirs],
        "moves": [
            {
                "issue": m.number,
                "done": m.done,
                "from": m.source,
                "to": m.destination,
                "files": [p.name for p in m.files],
            }
            for m in plan.sweep_moves
        ],
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    if not plan.mkdirs and not plan.sweep_moves:
        console.print("[dim]Nothing to repair.[/dim]")
        return 0

    verb = "Would" if dry_run else ""
    for mkdir in plan.mkdirs:
        console.print(f"  {verb} create folder {mkdir.folder_name}/".strip())
    move_verb = "Would move" if dry_run else "Moved"
    for move in plan.sweep_moves:
        console.print(
            f"  {move_verb} #{move.number} "
            f"({'done' if move.done else 'not done'}): "
            f"{move.source} -> {move.destination}"
        )
    return 0


# ---------------------------------------------------------------------------
# agent archive
# ---------------------------------------------------------------------------


def run_archive(
    project_root: Path,
    console: Console,
    issues: list[int],
    dry_run: bool,
    as_json: bool,
) -> int:
    """Delete the named solved issue groups (the mechanical half of archiving).

    Summarising the issues into the dated archive file is interpretive and
    stays agent-side; this command only removes the ``issue<N>_*`` files from
    the solved folder and reports the pre-archive HEAD sha so the summaries
    can record a recovery point. Refuses (exit 1) when any requested issue has
    no group in the solved folder, so a typo never silently archives less
    than the user confirmed.
    """
    settings = Settings()
    folders = _folders(project_root, settings)

    moves, missing = tracking.plan_archive(folders["solved"], issues)
    sha = gitutils.head_sha(project_root)

    if missing:
        msg = (
            "no files found in "
            f"{settings.solved_folder} for issue(s) "
            f"{', '.join(f'#{n}' for n in missing)}; nothing was archived."
        )
        if as_json:
            _emit_json(
                console,
                {"archived": False, "missing": missing, "error": msg},
            )
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 1

    removed: list[Path] = []
    if not dry_run and moves:
        removed = tracking.apply_archive(moves)

    payload = {
        "dry_run": dry_run,
        "head_sha": sha,
        "issues": [
            {
                "issue": m.number,
                "title": m.title,
                "files": [p.name for p in m.files],
            }
            for m in moves
        ],
        "removed": [p.name for p in removed],
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    if not moves:
        console.print("[dim]Nothing to archive.[/dim]")
        return 0
    if sha:
        console.print(f"Pre-archive HEAD: [bold]{sha}[/bold]")
    verb = "Would remove" if dry_run else "Removed"
    for m in moves:
        title = f" — {escape(m.title)}" if m.title else ""
        console.print(
            f"  {verb} #{m.number}{title}: {', '.join(p.name for p in m.files)}"
        )
    if not dry_run:
        console.print(
            "  [dim]Write the summaries into the dated archive file and "
            "commit so the pre-archive sha stays meaningful.[/dim]"
        )
    return 0


# ---------------------------------------------------------------------------
# agent capture
# ---------------------------------------------------------------------------

_ORIGINAL_TEMPLATE = """# Issue #{number}: {title}

Source: {url}

## Original issue text

{body}
"""


def run_capture(
    project_root: Path,
    console: Console,
    number: int,
    repo: str | None,
    force: bool,
    as_json: bool,
) -> int:
    """Fetch a GitHub issue and write ``issue<N>_original.md`` (body only).

    Comment *triage* is intentionally left to the agent — it is interpretive,
    not mechanical — so this command also surfaces the raw comments payload
    (count in text mode, full array in JSON) for the agent to summarise.
    """
    settings = Settings()
    folders = _folders(project_root, settings)

    if not gitutils.gh_available():
        msg = "gh is not on PATH; cannot fetch the issue. Try `gh auth login`."
        if as_json:
            _emit_json(console, {"written": False, "error": msg})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 1

    resolved_repo = repo
    if resolved_repo is None:
        owner_repo = gitutils.remote_owner_repo(project_root)
        if owner_repo is not None:
            resolved_repo = f"{owner_repo[0]}/{owner_repo[1]}"

    data = gitutils.gh_issue_view(number, project_root, resolved_repo)
    if data is None:
        msg = (
            f"could not fetch issue #{number}"
            + (f" from {resolved_repo}" if resolved_repo else "")
            + " (gh failed or unauthenticated)."
        )
        if as_json:
            _emit_json(console, {"written": False, "error": msg})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 1

    target_dir = folders["current"]
    target = target_dir / f"issue{number}_original.md"
    if target.exists() and not force:
        msg = f"{target} already exists; pass --force to overwrite."
        if as_json:
            _emit_json(console, {"written": False, "path": str(target), "error": msg})
        else:
            console.print(f"[yellow]exists[/yellow]  {msg}")
        return 1

    comments = data.get("comments") or []
    content = _ORIGINAL_TEMPLATE.format(
        number=data.get("number", number),
        title=data.get("title", "").strip(),
        url=data.get("url", ""),
        body=(data.get("body") or "").strip(),
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    payload = {
        "written": True,
        "issue": data.get("number", number),
        "repo": resolved_repo,
        "path": str(target),
        "comments_count": len(comments),
        "comments": comments,
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    console.print(f"[green]wrote[/green]  {target}")
    if comments:
        console.print(
            f"  [dim]{len(comments)} comment(s) fetched — triage them into the "
            "'## Comments (curated summary)' section.[/dim]"
        )
    return 0


# ---------------------------------------------------------------------------
# config add
# ---------------------------------------------------------------------------


def _print_config_guide(console: Console, cfg_path: Path) -> None:
    """Print a short guide on hand-editing ``config.toml`` later."""
    console.print(
        f"  [dim]Edit [bold]{escape(str(cfg_path))}[/bold] later to tune the "
        "project:[/dim]"
    )
    console.print(
        "  [dim]- [bold]mode[/bold]: 'standard' (full) or 'simple' (markdown-only); "
        "switch via 'issue-flow init --mode <id>'.[/dim]"
    )
    console.print(
        "  [dim]- [bold]caveman_default[/bold] / [bold]grill_me_default[/bold]: "
        "true/false; re-run 'issue-flow update' so the rule re-renders.[/dim]"
    )
    console.print(
        "  [dim]- [bold]label_flows[/bold] / [bold]yolo_label[/bold]: let issue "
        "labels pick the flow (e.g. a 'yolo' label runs /iflow-yolo); re-run "
        "'issue-flow update' so the commands re-render.[/dim]"
    )
    console.print(
        "  [dim]- [bold]checks_watch_minutes[/bold]: hard wall-clock budget "
        "(default 15) for `gh pr checks --watch` during /iflow-close yolo; "
        "re-run 'issue-flow update' so close/yolo re-render.[/dim]"
    )
    console.print(
        "  [dim]- [bold]step_directives[/bold] / [bold]model_label_flows[/bold]: "
        "bake MODEL & EXECUTION DIRECTIVE sections into lifecycle skills; optional "
        "label hints during /iflow-pick; re-run 'issue-flow update' after changing.[/dim]"
    )
    console.print(
        "  [dim]- [bold]linguist_attributes[/bold]: true/false (default false); "
        "when true, 'issue-flow update' writes a managed .gitattributes block for "
        "GitHub Linguist.[/dim]"
    )
    console.print(
        "  [dim]- [bold]remind_cleanup[/bold] / [bold]suggest_graphify[/bold] / "
        "[bold]auto_graphify_on_plan[/bold]; "
        "[bold]auto_switchback[/bold] / [bold]auto_close[/bold] / "
        "[bold]early_pr[/bold]; "
        "[bold]confirm_version_bump[/bold] / [bold]confirm_changelog_update[/bold]; "
        "[bold]ruff_autofix[/bold]: skill-behaviour toggles; re-run "
        "'issue-flow update' so skills re-render.[/dim]"
    )
    console.print(
        "  [dim]- [bold]pr_merge_method[/bold]: squash|merge|rebase for yolo "
        "close (default squash); [bold]cycle_max_issues[/bold]: /iflow-cycle "
        "queue cap (default 10); [bold]auto_adversarial_loops[/bold]: "
        "/iflow-auto inter-epoch budget (default 2; trailing loops:<n>).[/dim]"
    )
    console.print(
        "  [dim]Other ISSUEFLOW_* settings are environment-only (set them in "
        ".env), not in config.toml.[/dim]"
    )


def run_config_add(
    project_root: Path, console: Console, force: bool, as_json: bool
) -> int:
    """Create ``.issueflows/config.toml`` seeded from ``.env`` or defaults.

    Writes the ``[issueflow]`` keys issue-flow reads from ``config.toml``.
    Refuses to clobber an existing file unless ``force`` is set (which upserts
    those keys while preserving other content).
    """
    settings = Settings()
    cfg_path = settings.config_path(project_root)
    values = settings.seed_config_values()
    existed = cfg_path.is_file()

    if existed and not force:
        msg = (
            f"{cfg_path} already exists; pass --force to regenerate its "
            "[issueflow] keys."
        )
        if as_json:
            _emit_json(
                console,
                {"written": False, "path": str(cfg_path), "error": msg, **values},
            )
        else:
            console.print(f"[yellow]exists[/yellow]  {msg}")
            _print_config_guide(console, cfg_path)
        return 1

    modes.write_default_config(cfg_path, overwrite=force, **values)

    payload = {
        "written": True,
        "path": str(cfg_path),
        "overwritten": existed,
        **values,
    }
    if as_json:
        _emit_json(console, payload)
        return 0

    verb = "regenerated" if existed else "wrote"
    console.print(f"[green]{verb}[/green]  {cfg_path}")
    _print_config_guide(console, cfg_path)
    return 0


# ---------------------------------------------------------------------------
# status (top-level, human-facing)
# ---------------------------------------------------------------------------


def run_status(project_root: Path, console: Console, local: bool, as_json: bool) -> int:
    """Read-only overview: focus stage, parked, solved, optional GitHub cross-ref."""
    settings = Settings()
    folders = _folders(project_root, settings)
    branch = gitutils.current_branch(project_root)

    focus = tracking.resolve_focus(folders["current"], branch)
    focus_section: dict[str, Any] | None = None
    if focus.number is not None:
        group = _focus_group(folders, focus.number)
        focus_section = {
            "number": focus.number,
            "title": group.title(),
            "stage": group.stage,
            "next_command": group.next_command,
            "resolved_via": focus.resolved_via,
        }

    parked_groups = tracking.group_issue_files(folders["partly"])
    parked = [
        {"number": n, "title": g.title()} for n, g in sorted(parked_groups.items())
    ]
    solved_numbers = sorted(tracking.group_issue_files(folders["solved"]))

    # An in-flight /iflow-cycle leaves a cycle_status.md in current-issues; a
    # finished one is archived to solved/, so its presence here means a batch
    # run is paused or active.
    cycle_active = (folders["current"] / "cycle_status.md").is_file()

    github: dict[str, Any] | None = None
    if not local:
        github = _github_section(project_root, folders)

    payload: dict[str, Any] = {
        "branch": branch,
        "focus": focus_section,
        "ambiguous_candidates": focus.candidates,
        "parked": parked,
        "solved_count": len(solved_numbers),
        "solved_recent": solved_numbers[-5:],
        "cycle_active": cycle_active,
        "github": github,
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    _render_status_text(console, settings, payload)
    return 0


def _github_section(project_root: Path, folders: dict[str, Path]) -> dict[str, Any]:
    """Cross-reference open GitHub issues against local tracking folders."""
    if not gitutils.gh_available():
        return {"available": False, "reason": "gh not on PATH"}

    issues = gitutils.gh_issue_list(project_root)
    if issues is None:
        return {"available": False, "reason": "gh failed or unauthenticated"}

    current = set(tracking.group_issue_files(folders["current"]))
    partly = set(tracking.group_issue_files(folders["partly"]))
    solved = set(tracking.group_issue_files(folders["solved"]))

    annotated: list[dict[str, Any]] = []
    untracked = 0
    for issue in issues:
        number = issue.get("number")
        if number in current:
            state = "focus"
        elif number in partly:
            state = "parked"
        elif number in solved:
            state = "solved-locally"
        else:
            state = "untracked"
            untracked += 1
        annotated.append(
            {"number": number, "title": issue.get("title"), "local_state": state}
        )

    return {
        "available": True,
        "open_count": len(annotated),
        "untracked_count": untracked,
        "issues": annotated,
    }


def _render_status_text(
    console: Console, settings: Settings, payload: dict[str, Any]
) -> None:
    branch = payload["branch"]
    console.print(f"[bold]Branch[/bold]: {escape(branch) if branch else '(detached)'}")

    focus = payload["focus"]
    if focus is not None:
        title = f" — {escape(focus['title'])}" if focus["title"] else ""
        console.print(
            f"[bold]Focus[/bold]: #{focus['number']}{title} "
            f"(stage {focus['stage']} -> {focus['next_command']})"
        )
    elif payload["ambiguous_candidates"]:
        cands = ", ".join(f"#{n}" for n in payload["ambiguous_candidates"])
        console.print(f"[bold]Focus[/bold]: ambiguous ({cands})")
    else:
        console.print("[bold]Focus[/bold]: none")

    parked = payload["parked"]
    if parked:
        console.print(f"[bold]Parked[/bold]: {len(parked)}")
        for item in parked:
            title = f" — {escape(item['title'])}" if item["title"] else ""
            console.print(f"  #{item['number']}{title}")
    else:
        console.print("[bold]Parked[/bold]: 0")

    console.print(f"[bold]Solved[/bold]: {payload['solved_count']}")

    if payload.get("cycle_active"):
        console.print(
            "[bold]Cycle[/bold]: [yellow]in-flight[/yellow] "
            "(cycle_status.md present — resume with `/iflow-cycle resume`)"
        )

    github = payload["github"]
    summary_github = ""
    if github is None:
        pass
    elif not github.get("available"):
        console.print(f"[bold]GitHub[/bold]: unavailable ({github.get('reason')})")
    else:
        console.print(
            f"[bold]GitHub[/bold]: {github['open_count']} open "
            f"({github['untracked_count']} untracked)"
        )
        summary_github = (
            f" Open on GitHub: {github['open_count']} "
            f"({github['untracked_count']} untracked)."
        )

    focus_str = f"#{focus['number']} ({focus['stage']})" if focus else "none"
    console.print(
        f"[dim]Summary: Focus: {focus_str}. Parked: {len(parked)}. "
        f"Solved: {payload['solved_count']}.{summary_github}[/dim]"
    )
