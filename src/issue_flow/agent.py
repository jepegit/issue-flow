"""Orchestrators behind the agent-facing CLI surface.

These functions back ``issue-flow status`` (human-facing, top-level) and the
``issue-flow agent ...`` sub-commands (``state`` / ``preflight`` / ``switchback`` /
``version-plan`` / ``resolve`` / ``sweep`` / ``archive`` / ``capture``) that
exist so AI agents can ask the tool for a deterministic answer instead of
re-deriving lifecycle state by hand on every run.

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
                }
            )
            if state != "closed":
                done = False
        stage_payloads.append(
            {
                "index": stage.index,
                "title": stage.title,
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
        "  [dim]- [bold]step_directives[/bold] / [bold]model_label_flows[/bold]: "
        "bake MODEL & EXECUTION DIRECTIVE sections into lifecycle skills; optional "
        "label hints during /iflow-pick; re-run 'issue-flow update' after changing.[/dim]"
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
