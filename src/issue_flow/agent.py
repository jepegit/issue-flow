"""Orchestrators behind the agent-facing CLI surface.

These functions back ``issue-flow status`` (human-facing, top-level) and the
``issue-flow agent ...`` sub-commands (``state`` / ``preflight`` / ``switchback`` /
``default-sync`` / ``sync-branch`` / ``branches`` / ``version-plan`` / ``resolve`` /
``open-workspace`` / ``worktree-add`` / ``worktree-list`` / ``worktree-remove`` /
``sweep`` / ``archive`` / ``capture`` / ``sub-issue-add``) that exist so AI agents
can ask the tool for a deterministic answer instead of re-deriving lifecycle
state by hand on every run.

Each ``run_*`` returns a process exit code and emits either a short human
report (via :class:`rich.console.Console`) or a stable JSON object on stdout
when ``as_json`` is set. They all degrade gracefully: a missing/unauthenticated
``gh`` never hard-fails a read-only command, it just trims the GitHub section
and notes the gap — mirroring the scaffolded ``/iflow-status`` contract.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from collections.abc import Callable
from typing import Any

from rich.console import Console
from rich.markup import escape

from issue_flow import (
    epic_session,
    gitutils,
    history,
    modes,
    project,
    readiness,
    tracking,
)
from issue_flow.config import Settings
from issue_flow.editors import DEFAULT_EDITOR, EDITORS
from issue_flow.templating import packaged_skill_output_names


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


_SKILL_VERSION_RE = re.compile(r"^issue-flow-version:\s*(\S+)\s*$", re.MULTILINE)
VERSION_DRIFT_NOTE = (
    "rendered skills are stamped issue-flow {skills} but the CLI is {cli} — "
    "run `issue-flow update` so the skills match the installed CLI."
)


def rendered_skills_version(project_root: Path, settings: Settings) -> str | None:
    """``issue-flow-version`` stamped on the rendered ``iflow`` dispatcher skill.

    ``None`` when the skill is not rendered (or carries no stamp). Only the
    dispatcher is read: every skill is re-stamped by the same ``update`` run,
    so one file is a faithful proxy for the whole set.
    """
    skill_md = project_root / settings.agent_dir / "skills" / "iflow" / "SKILL.md"
    if not skill_md.is_file():
        return None
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    match = _SKILL_VERSION_RE.search(text)
    return match.group(1) if match else None


def version_drift_fields(project_root: Path, settings: Settings) -> dict[str, Any]:
    """``cli_version`` / ``skills_version`` / ``version_drift`` for a payload.

    Issue #386: an installed CLI newer than the rendered skills is how drive
    mode ended up planning with stale skill text. Surfacing it in ``agent
    state`` / ``preflight`` lets every entry point warn instead of guessing.
    """
    from issue_flow import __version__

    skills_version = rendered_skills_version(project_root, settings)
    return {
        "cli_version": __version__,
        "skills_version": skills_version,
        "version_drift": skills_version is not None and skills_version != __version__,
    }


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
        "epic_hint": None,
        "epic_session": None,
        **version_drift_fields(project_root, settings),
    }

    session = epic_session.read_epic_session(folders["current"])
    if session is not None:
        payload["epic_session"] = session.as_dict()

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
    elif focus.resolved_via != "ambiguous":
        # No focus yet — surface active-epic next_candidates so /iflow can
        # recommend /iflow-pick instead of a blind /iflow-capture (issue #210).
        epic_hint = _collect_epic_hints(project_root, local=False)
        payload["epic_hint"] = epic_hint
        if not epic_hint["epics"]:
            payload["next_command"] = tracking.STAGE_NEXT_COMMAND[tracking.STAGE_INIT]

    if as_json:
        _emit_json(console, payload)
        return 0

    if payload["version_drift"]:
        console.print(
            "  [yellow]warn[/yellow]  "
            + VERSION_DRIFT_NOTE.format(
                skills=payload["skills_version"], cli=payload["cli_version"]
            )
        )
    if focus.resolved_via == "ambiguous":
        console.print(
            "[yellow]Ambiguous focus[/yellow]: multiple issue groups in "
            f"{settings.current_issues_folder} -> "
            f"{', '.join(f'#{n}' for n in focus.candidates)}. "
            "Specify which issue to act on."
        )
        return 0
    if focus.number is None:
        epic_hint = payload.get("epic_hint") or {"epics": []}
        session_info = payload.get("epic_session")
        if session_info:
            console.print(
                "[dim]Epic session[/dim] "
                f"#{session_info['epic']} ({escape(str(session_info['mode']))})"
            )
        if epic_hint["epics"]:
            console.print(
                "[dim]No focus issue found.[/dim] Active epic next candidates "
                "(do not auto-init — use /iflow-pick or pass an explicit N):"
            )
            for entry in epic_hint["epics"]:
                nums = ", ".join(f"#{n}" for n in entry["next_candidates"])
                console.print(
                    f"  Epic #{entry['epic']} stage {entry['stage']} "
                    f"({escape(entry['title'])}): {nums}"
                )
            return 0
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
    drift = version_drift_fields(project_root, settings)
    if drift["version_drift"]:
        notes.append(
            VERSION_DRIFT_NOTE.format(
                skills=drift["skills_version"], cli=drift["cli_version"]
            )
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
        **drift,
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
# agent setup-status (readiness picture for ``/iflow-setup``)
# ---------------------------------------------------------------------------


def run_setup_status(project_root: Path, console: Console, as_json: bool) -> int:
    """Report whether the project is ready to run the issue-flow workflow.

    Read-only and always exit 0: "not ready" is the answer, not an error, so
    ``/iflow-setup`` can parse the payload on a bare directory just as well as
    on a fully configured repo.
    """
    report = readiness.probe(project_root)

    if as_json:
        _emit_json(console, report.as_dict())
        return 0

    def _mark(ok: bool) -> str:
        return "[green]ok[/green]  " if ok else "[yellow]--[/yellow]  "

    console.print(f"\n[bold]Setup status for [cyan]{report.project_root}[/cyan][/bold]")
    console.print(
        f"[dim]Looks like a{'n' if report.project_kind == 'existing' else ''} "
        f"{report.project_kind} project.[/dim]\n"
    )

    for name, present in report.tools.items():
        console.print(f"  {_mark(present)}{name}")
    console.print(f"  {_mark(bool(report.git['is_repo']))}git repository")
    origin = report.git["origin"]
    console.print(
        f"  {_mark(bool(report.git['has_origin']))}origin remote"
        + (f" ([cyan]{escape(str(origin))}[/cyan])" if origin else "")
    )
    account = report.github["account"]
    console.print(
        f"  {_mark(bool(report.github['authenticated']))}gh authenticated"
        + (f" (as [cyan]{escape(str(account))}[/cyan])" if account else "")
    )
    console.print(f"  {_mark(bool(report.python['has_pyproject']))}pyproject.toml")
    mode = report.issueflow["mode"]
    console.print(
        f"  {_mark(bool(report.issueflow['scaffolded']))}issue-flow scaffold"
        + (f" (mode [cyan]{escape(str(mode))}[/cyan])" if mode else "")
    )

    if not report.blockers:
        console.print("\n[bold green]Ready.[/bold green] Next: /iflow-pick\n")
        return 0

    console.print(
        f"\n[bold yellow]{len(report.blockers)} thing(s) to sort out[/bold yellow] "
        "[dim](run /iflow-setup in your editor to be walked through them)[/dim]"
    )
    for blocker in report.blockers:
        console.print(f"\n  {escape(blocker.summary)}")
        console.print(f"    [green]{escape(blocker.fix)}[/green]")
        if not blocker.agent_may_run:
            console.print("    [dim]you need to run this one yourself[/dim]")
    console.print()
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

        base_ref = f"origin/{default}"
        target_ref = f"origin/{name}"
        unique = gitutils.cherry_unique_count(project_root, base_ref, target_ref)
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
                project_root, base_ref, target_ref, limit=commit_limit
            )
            shortstat = gitutils.unique_diff_shortstat(
                project_root, base_ref, target_ref
            )
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
            project_root, base_ref, target_ref, limit=commit_limit
        )
        shortstat = gitutils.unique_diff_shortstat(project_root, base_ref, target_ref)
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
# agent local-branches (local audit for ``/iflow-cleanup`` Phase A, issue #243)
# ---------------------------------------------------------------------------


def _commits_after_merge(
    newest_commit_date: str | None,
    merged_prs: list[dict[str, Any]],
) -> bool:
    """Whether unique commits are *newer* than the newest merged PR.

    A squash merge rewrites the branch's commits, so a landed branch keeps
    commits that ``git cherry`` calls unique even though nothing is at risk.
    Work pushed *after* the PR merged looks identical in the bucket counts but
    is genuinely unmerged, so it must never be offered for deletion. When
    either timestamp is unparseable, answer ``True`` — the cautious side.
    """
    newest = gitutils.parse_iso8601(newest_commit_date or "")
    if newest is None:
        return True
    merges = [
        gitutils.parse_iso8601(str(pr.get("mergedAt") or "")) for pr in merged_prs
    ]
    stamps = [stamp for stamp in merges if stamp is not None]
    if not stamps:
        return True
    return newest > max(stamps)


def run_local_branches(
    project_root: Path,
    console: Console,
    as_json: bool,
    *,
    fetch: bool = True,
    commit_limit: int = 20,
) -> int:
    """Classify local branches by how they relate to the default branch.

    ``git branch -d`` only accepts branches *reachable* from the default, so in
    a squash-merging repo it refuses every landed branch. This splits the
    locals into what ``-d`` can take (``reachable``), what is provably landed
    but needs ``-D`` (``squash_landed``), what a merged PR claims is landed
    while the tip still differs (``merged_pr_divergent``), and what must never
    be deleted (``unique_work``).

    Read-only: never deletes a branch. The confirm-gated deletes live in
    ``/iflow-cleanup``.
    """
    notes: list[str] = []
    remote = gitutils.remote_owner_repo(project_root)
    repo = f"{remote[0]}/{remote[1]}" if remote else None
    payload: dict[str, Any] = {
        "git_available": gitutils.git_available(),
        "gh_available": gitutils.gh_available(),
        "repo": repo,
        "default_branch": None,
        "base_ref": None,
        "fetched": False,
        "current_branch": None,
        "reachable": [],
        "squash_landed": [],
        "merged_pr_divergent": [],
        "unique_work": [],
        "skipped": [],
        "notes": notes,
    }

    def emit(exit_code: int) -> int:
        if as_json:
            _emit_json(console, payload)
            return exit_code
        return _render_local_branches_text(console, payload, exit_code)

    if not gitutils.git_available():
        notes.append("git is not on PATH")
        return emit(1)

    if fetch:
        payload["fetched"] = gitutils.fetch_prune(project_root)
        if not payload["fetched"]:
            notes.append("git fetch --prune failed or was skipped")

    default = gitutils.default_branch(project_root)
    payload["default_branch"] = default

    base_ref = f"origin/{default}"
    if gitutils.branch_tip(project_root, base_ref) is None:
        base_ref = default
        notes.append(
            f"origin/{default} not found; comparing against local {default} instead"
        )
    payload["base_ref"] = base_ref

    names = gitutils.list_local_branches(project_root)
    if names is None:
        notes.append("could not list local branches")
        return emit(1)

    current = gitutils.current_branch(project_root)
    payload["current_branch"] = current

    prs_by_head: dict[str, list[dict[str, Any]]] | None = None
    if gitutils.gh_available():
        prs_by_head = gitutils.gh_prs_by_head(project_root, repo)
        if prs_by_head is None:
            notes.append("gh pr list failed; PR evidence unavailable")

    def protection_skip(name: str) -> bool:
        """True when GitHub marks ``name`` protected (checked for candidates only)."""
        if prs_by_head is None and not gitutils.gh_available():
            return False
        return gitutils.branch_is_protected(project_root, name, repo) is True

    for name in sorted(names):
        if name == default:
            payload["skipped"].append({"name": name, "reason": "default branch"})
            continue
        if current and name == current:
            payload["skipped"].append(
                {"name": name, "reason": "current branch (checked out)"}
            )
            continue

        tip = gitutils.branch_tip(project_root, name)
        reachable = gitutils.is_ancestor(project_root, name, base_ref)
        if reachable is None:
            payload["skipped"].append(
                {
                    "name": name,
                    "tip": tip,
                    "reason": f"could not compare to {base_ref}",
                }
            )
            continue

        prs = (prs_by_head or {}).get(name)
        open_prs, merged_prs = _pr_bucket(prs)

        if reachable:
            if protection_skip(name):
                payload["skipped"].append(
                    {"name": name, "tip": tip, "reason": "GitHub protected branch"}
                )
                continue
            payload["reachable"].append(
                {
                    "name": name,
                    "tip": tip,
                    "reason": f"tip reachable from {base_ref} (plain -d works)",
                    "merged_prs": merged_prs,
                }
            )
            continue

        unique = gitutils.cherry_unique_count(project_root, base_ref, name)
        if unique is None:
            payload["skipped"].append(
                {
                    "name": name,
                    "tip": tip,
                    "reason": f"could not compare to {base_ref}",
                }
            )
            continue

        if unique == 0:
            if protection_skip(name):
                payload["skipped"].append(
                    {"name": name, "tip": tip, "reason": "GitHub protected branch"}
                )
                continue
            reason = f"every commit is patch-equivalent to {base_ref}"
            if merged_prs:
                reason += " (merged PR on GitHub)"
            payload["squash_landed"].append(
                {
                    "name": name,
                    "tip": tip,
                    "reason": reason,
                    "merged_prs": merged_prs,
                }
            )
            continue

        commits = gitutils.unique_commit_onelines(
            project_root, base_ref, name, limit=commit_limit, no_merges=True
        )
        shortstat = gitutils.unique_diff_shortstat(project_root, base_ref, name)
        entry: dict[str, Any] = {
            "name": name,
            "tip": tip,
            "unique_commits": unique,
            "commits": commits or [],
            "shortstat": shortstat or "",
            "open_prs": open_prs,
            "merged_prs": merged_prs,
        }

        if merged_prs and not open_prs:
            numbers = ", ".join(f"#{pr.get('number')}" for pr in merged_prs)
            newest = gitutils.latest_unique_commit_date(project_root, base_ref, name)
            after = _commits_after_merge(newest, merged_prs)
            if after:
                entry["committed_after_merge"] = True
                entry["reason"] = (
                    f"{unique} commit(s) added after PR {numbers} merged "
                    f"(not in {base_ref})"
                )
                payload["unique_work"].append(entry)
                continue
            entry["reason"] = (
                f"merged PR {numbers}; {unique} commit(s) rewritten by the "
                f"squash merge, none newer than it"
            )
            payload["merged_pr_divergent"].append(entry)
            continue

        if open_prs:
            entry["reason"] = "open pull request on this head"
        else:
            entry["reason"] = f"{unique} commit(s) not in {base_ref}"
        payload["unique_work"].append(entry)

    return emit(0)


def _render_local_branches_text(
    console: Console, payload: dict[str, Any], exit_code: int
) -> int:
    if exit_code != 0 and not payload.get("default_branch"):
        for note in payload.get("notes") or []:
            console.print(f"[yellow]{escape(str(note))}[/yellow]")
        return exit_code

    base_ref = payload.get("base_ref") or "?"
    console.print(f"Local branch audit vs [bold]{escape(str(base_ref))}[/bold]:")
    reachable = payload.get("reachable") or []
    squashed = payload.get("squash_landed") or []
    divergent = payload.get("merged_pr_divergent") or []
    unique = payload.get("unique_work") or []
    skipped = payload.get("skipped") or []
    console.print(
        f"  [green]reachable[/green] {len(reachable)}  ·  "
        f"[yellow]squash-landed[/yellow] {len(squashed)}  ·  "
        f"[magenta]merged-PR divergent[/magenta] {len(divergent)}  ·  "
        f"[cyan]unique work[/cyan] {len(unique)}  ·  "
        f"[dim]skipped[/dim] {len(skipped)}"
    )
    for item in reachable:
        console.print(
            f"  [green]reachable[/green]  {escape(str(item.get('name')))} "
            f"{escape(str(item.get('tip') or '?'))} — -d is enough"
        )
    for item in squashed:
        console.print(
            f"  [yellow]squash-landed[/yellow]  {escape(str(item.get('name')))} "
            f"{escape(str(item.get('tip') or '?'))} — {escape(str(item.get('reason')))}"
        )
    for item in divergent:
        console.print(
            f"  [magenta]merged-PR divergent[/magenta]  "
            f"{escape(str(item.get('name')))} "
            f"{escape(str(item.get('tip') or '?'))} — {escape(str(item.get('reason')))}"
        )
        for line in (item.get("commits") or [])[:5]:
            console.print(f"      {escape(str(line))}")
    for item in unique:
        console.print(
            f"  [cyan]unique[/cyan]  {escape(str(item.get('name')))} "
            f"{escape(str(item.get('tip') or '?'))} — {escape(str(item.get('reason')))}"
        )
        for line in (item.get("commits") or [])[:5]:
            console.print(f"      {escape(str(line))}")
    for item in skipped:
        console.print(
            f"  [dim]skipped[/dim]  {escape(str(item.get('name')))} — "
            f"{escape(str(item.get('reason')))}"
        )
    if squashed or divergent:
        console.print(
            "  [dim]squash-landed / divergent branches need "
            "`git branch -D`; restore with `git branch <name> <tip>`.[/dim]"
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
        "in_worktree": False,
        "dirty_paths": [],
        "default_sync": None,
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
    payload["in_worktree"] = gitutils.is_linked_worktree(project_root)

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

    payload["in_worktree"] = gitutils.is_linked_worktree(project_root)
    if payload["in_worktree"]:
        home = gitutils.worktree_home_path(project_root)
        notes.append(
            "linked worktree — skip switch to default (home already holds it). "
            "Pull default from home"
            + (f" (`issue-flow agent switchback -C {home}`)" if home else "")
            + "."
        )
        return emit(0)

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
    sync = gitutils.classify_default_sync(
        project_root,
        issueflows_dir=Settings().issueflows_dir,
        default=default,
        fetch=False,
    )
    payload["default_sync"] = sync
    if not ok:
        notes.append(
            f"git pull --ff-only refused: {error} — do not rebase, force-push, "
            "or push default to skip CI."
        )
        notes.extend(_default_sync_note_lines(sync))
        return emit(1)

    if sync.get("ahead"):
        notes.extend(_default_sync_note_lines(sync))

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
# agent default-sync (issue #303)
# ---------------------------------------------------------------------------


def run_default_sync(project_root: Path, console: Console, as_json: bool) -> int:
    """Classify unique commits on home default vs origin — no mutate."""
    notes: list[str] = []
    if not gitutils.git_available():
        payload = {
            "default_branch": None,
            "ahead": None,
            "behind": None,
            "ff_possible": False,
            "class": "unknown",
            "action": "unknown",
            "commits": [],
            "tree_paths": [],
            "never": list(gitutils.DEFAULT_SYNC_NEVER),
            "notes": ["git is not on PATH"],
        }
        if as_json:
            _emit_json(console, payload)
        else:
            console.print("[red]error[/red]  git is not on PATH")
        return 1

    payload = gitutils.classify_default_sync(
        project_root,
        issueflows_dir=Settings().issueflows_dir,
    )
    notes.extend(payload.get("notes") or [])
    payload["notes"] = notes
    if as_json:
        _emit_json(console, payload)
        return 0
    _render_default_sync_text(console, payload)
    return 0


def _default_sync_note_lines(sync: dict[str, Any]) -> list[str]:
    """Short notes skills can print after an ff-only refusal or ahead-only home."""
    lines = [
        f"default-sync: action={sync.get('action')} class={sync.get('class')} "
        f"ahead={sync.get('ahead')} behind={sync.get('behind')}"
    ]
    for commit in sync.get("commits") or []:
        mark = " (merge)" if commit.get("is_merge") else ""
        paths = ", ".join(commit.get("paths") or []) or "(no paths)"
        lines.append(f"  {commit.get('sha')} {commit.get('subject')}{mark} — {paths}")
    tree = sync.get("tree_paths") or []
    if tree:
        lines.append("  tree: " + ", ".join(tree))
    action = sync.get("action")
    if action == "tracking_pr":
        lines.append(
            "offer: merge origin/<default> or cherry-pick onto a chore branch, "
            "then open a tiny PR — never push default directly."
        )
    elif action == "replay_tracking":
        lines.append(
            "offer: replay the tracking commit onto origin/<default> "
            "(chore branch + PR). Do not stack another merge."
        )
    elif action == "stop_product":
        lines.append(
            "stop: unique commits touch product / lock / HISTORY. "
            "User decides. Do not merge onto default."
        )
    elif action == "report_ahead":
        lines.append(
            "home default is ahead of origin; report unique commits. "
            "Do not silent-push default."
        )
    elif action == "ff_only":
        lines.append("ff-only is safe (behind only).")
    never = sync.get("never") or list(gitutils.DEFAULT_SYNC_NEVER)
    lines.append("never: " + "; ".join(never))
    return lines


def _render_default_sync_text(console: Console, payload: dict[str, Any]) -> None:
    console.print(
        f"[bold]action[/bold] {escape(str(payload.get('action')))}  "
        f"class={escape(str(payload.get('class')))}  "
        f"ahead={payload.get('ahead')} behind={payload.get('behind')}  "
        f"ff_possible={payload.get('ff_possible')}"
    )
    for line in _default_sync_note_lines(payload)[1:]:
        console.print(f"  {escape(line)}")
    for note in payload.get("notes") or []:
        console.print(f"  [dim]{escape(note)}[/dim]")


# ---------------------------------------------------------------------------
# agent sync-branch
# ---------------------------------------------------------------------------

#: How many consecutive conflicted commits the changelog resolver will handle
#: during one rebase before giving up. A well-formed issue branch touches the
#: changelog in a single commit; more than a handful means something else is
#: going on and a human should look.
_SYNC_RESOLVE_LIMIT = 10

SYNC_STRATEGIES = ("rebase", "merge")


RESOLVER_CHANGELOG = "changelog"
RESOLVER_ADDITIVE = "additive"

_STATUS_FILE_RE = re.compile(r"^issue\d+_status\.md$")


def _resolver_for_path(
    rel_path: str,
    *,
    changelog: str,
    settings: Settings,
) -> str | None:
    """Which keep-both resolver may rewrite ``rel_path`` (repo-relative).

    * the changelog → strict ``[Unreleased]``-only resolver (issue #240);
    * anything under ``<issueflows>/<designs>/`` or an ``issue<N>_status.md``
      under ``<issueflows>/`` → the additive resolver (bullets + table rows,
      issue #386);
    * everything else → ``None``: product code is a human decision.
    """
    normalized = rel_path.replace("\\", "/")
    if normalized == changelog.replace("\\", "/"):
        return RESOLVER_CHANGELOG
    issueflows = settings.issueflows_dir.strip("/")
    designs_prefix = f"{issueflows}/{settings.designs_folder.strip('/')}/"
    if normalized.startswith(designs_prefix) and normalized.endswith(".md"):
        return RESOLVER_ADDITIVE
    if normalized.startswith(f"{issueflows}/") and _STATUS_FILE_RE.match(
        normalized.rsplit("/", 1)[-1]
    ):
        return RESOLVER_ADDITIVE
    return None


def _detect_stacked_base(
    project_root: Path,
    default: str,
    notes: list[str],
) -> str | None:
    """Find a squash-landed parent branch this branch was stacked on.

    A child PR built on a sibling issue branch (``Depends on: #N``) still
    carries the parent's commits after the parent squash-merges. Replaying
    those onto ``origin/<default>`` conflicts on every file they touched, so
    the sync must start *after* the parent's tip (issue #386).

    Candidate = a local branch or ``origin/*`` ref that is an ancestor of
    ``HEAD``, is **not** already reachable from ``origin/<default>``, and is
    provably landed — a ``MERGED`` PR on that head, zero ``git cherry`` unique
    commits, or its touched files byte-identical on the default branch
    (:func:`gitutils.content_landed`). The nearest one (fewest commits between
    it and ``HEAD``) wins. Returns ``None`` when nothing qualifies.
    """
    base_ref = f"origin/{default}"
    current = gitutils.current_branch(project_root)
    candidates: list[str] = []
    for name in gitutils.list_local_branches(project_root) or []:
        if name in {default, current}:
            continue
        candidates.append(name)
    for name in gitutils.list_origin_branches(project_root) or []:
        if name in {default, current}:
            continue
        candidates.append(f"origin/{name}")

    prs_by_head: dict[str, list[dict[str, Any]]] | None = None
    if gitutils.gh_available():
        remote = gitutils.remote_owner_repo(project_root)
        repo = f"{remote[0]}/{remote[1]}" if remote else None
        prs_by_head = gitutils.gh_prs_by_head(project_root, repo)

    best: tuple[int, str] | None = None
    for ref in candidates:
        if gitutils.is_ancestor(project_root, ref, "HEAD") is not True:
            continue
        if gitutils.is_ancestor(project_root, ref, base_ref) is True:
            continue
        head_name = ref.removeprefix("origin/")
        _open, merged = _pr_bucket((prs_by_head or {}).get(head_name))
        landed = bool(merged)
        if not landed:
            unique = gitutils.cherry_unique_count(project_root, base_ref, ref)
            landed = unique == 0
        if not landed:
            # Multi-commit squash: patch-ids differ, but the parent's files
            # are exactly what sits on the default branch now.
            landed = gitutils.content_landed(project_root, ref, base_ref) is True
        if not landed:
            continue
        distance = gitutils.rev_list_count(project_root, ref, "HEAD")
        if distance is None or distance <= 0:
            continue
        if best is None or distance < best[0]:
            best = (distance, ref)

    if best is None:
        return None
    notes.append(
        f"stacked on squash-landed {best[1]}; replaying only the "
        f"{best[0]} commit(s) after it"
    )
    return best[1]


def run_sync_branch(
    project_root: Path,
    console: Console,
    strategy: str,
    as_json: bool,
    *,
    base: str | None = None,
) -> int:
    """Bring the current issue branch up to date with ``origin/<default>``.

    ``/iflow-close`` used to sync with a plain ``git pull --ff-only`` on the
    issue branch, which cannot pick up commits that landed on the *default*
    branch while the issue was in flight — so the PR only failed later, at
    merge time, with ``mergeable: CONFLICTING`` (issue #240).

    This replays the branch onto ``origin/<default>`` (``--strategy merge``
    merges instead) and auto-resolves the conflict shapes that are pure
    bookkeeping: both sides appending bullets to the changelog's
    ``[Unreleased]`` section, and both sides appending bullets / table rows to
    a design guide or an ``issue<N>_status.md`` (issue #386). Anything else
    aborts the operation, leaves the branch exactly as it was, and exits 1 for
    the caller to stop on.

    ``base`` (``--base <ref>``) rebases ``--onto origin/<default>`` from that
    ref so a squash-merged parent's commits are dropped; without it a landed
    parent is auto-detected (:func:`_detect_stacked_base`).

    Pushing is deliberately out of scope: a rebase rewrites the branch, so the
    force-with-lease push stays in ``/iflow-close`` where the user's tokens and
    confirmations apply.
    """
    settings = Settings()
    changelog = settings.history_file
    notes: list[str] = []
    payload: dict[str, Any] = {
        "git_available": gitutils.git_available(),
        "branch": None,
        "default_branch": None,
        "strategy": strategy,
        "ahead": None,
        "behind": None,
        "action": "none",
        "changelog": changelog,
        "changelog_resolved": False,
        "resolved_paths": [],
        "resolvers": {},
        "conflicts": [],
        "dirty_paths": [],
        "base": base,
        "base_detected": False,
        "dropped_commits": 0,
        "needs_force_push": False,
        "notes": notes,
    }

    def emit(exit_code: int) -> int:
        if as_json:
            _emit_json(console, payload)
        else:
            _render_sync_branch_text(console, payload, exit_code)
        return exit_code

    if strategy not in SYNC_STRATEGIES:
        notes.append(
            f"unknown strategy {strategy!r}; expected one of "
            f"{', '.join(SYNC_STRATEGIES)}"
        )
        return emit(1)
    if not payload["git_available"]:
        notes.append("git is not on PATH")
        return emit(1)

    branch = gitutils.current_branch(project_root)
    default = gitutils.default_branch(project_root)
    payload["branch"] = branch
    payload["default_branch"] = default

    if branch is None:
        notes.append("HEAD is detached; switch to the issue branch first")
        return emit(1)
    if branch == default:
        notes.append(
            f"already on the default branch ({default}); sync-branch is for an "
            "issue branch"
        )
        return emit(1)

    dirty = gitutils.dirty_paths(project_root)
    if dirty is None:
        notes.append("could not read the working tree state (not a git repo?)")
        return emit(1)
    if dirty:
        payload["dirty_paths"] = dirty
        notes.append(
            "working tree is dirty; commit or stash before syncing so a "
            "conflict can never strand uncommitted work."
        )
        return emit(1)

    if not gitutils.fetch_prune(project_root):
        notes.append("git fetch --prune failed; comparing against stale refs")

    counts = gitutils.ahead_behind(project_root, default)
    if counts is None:
        notes.append(
            f"could not compare with origin/{default} (missing remote-tracking "
            "ref?); sync manually"
        )
        return emit(1)
    ahead, behind = counts
    payload["ahead"] = ahead
    payload["behind"] = behind

    if behind == 0:
        notes.append(f"already up to date with origin/{default}")
        return emit(0)

    ref = f"origin/{default}"

    if base is not None:
        if gitutils.rev_parse_verify(project_root, base) is None:
            notes.append(f"--base {base!r} does not resolve to a commit")
            return emit(1)
        if gitutils.is_ancestor(project_root, base, "HEAD") is not True:
            notes.append(
                f"--base {base!r} is not an ancestor of {branch}; refusing to "
                "guess which commits to drop"
            )
            return emit(1)
    elif strategy == "rebase":
        detected = _detect_stacked_base(project_root, default, notes)
        if detected is not None:
            base = detected
            payload["base"] = detected
            payload["base_detected"] = True

    if base is not None:
        if strategy != "rebase":
            notes.append("--base only applies to the rebase strategy")
            return emit(1)
        dropped = gitutils.rev_list_count(project_root, ref, base)
        payload["dropped_commits"] = dropped or 0

    if strategy == "rebase":
        ok, error = gitutils.rebase_onto(project_root, ref, base=base)
    else:
        ok, error = gitutils.merge_ref(project_root, ref)

    if not ok:
        resolved = _resolve_sync_conflicts(
            project_root, strategy, changelog, payload, notes, error, settings
        )
        if not resolved:
            return emit(1)

    payload["action"] = (
        "fast-forward"
        if ahead == 0 and strategy == "rebase"
        else ("rebased" if strategy == "rebase" else "merged")
    )
    payload["needs_force_push"] = strategy == "rebase" and ahead > 0
    return emit(0)


def _abort_sync(
    project_root: Path,
    strategy: str,
    payload: dict[str, Any],
    notes: list[str],
) -> None:
    """Undo an in-progress rebase/merge so the branch is untouched.

    An abort rewinds any changelog resolve made earlier in the same run (a
    rebase can conflict once per replayed commit), so the payload must stop
    claiming it — nothing was kept.
    """
    if strategy == "rebase":
        gitutils.rebase_abort(project_root)
    else:
        gitutils.merge_abort(project_root)
    if payload["changelog_resolved"] or payload["resolved_paths"]:
        notes.append(
            "rolled back the keep-both resolve(s) — the abort restored the "
            "branch as it was"
        )
        payload["changelog_resolved"] = False
        payload["resolved_paths"] = []
        payload["resolvers"] = {}


def _resolve_sync_conflicts(
    project_root: Path,
    strategy: str,
    changelog: str,
    payload: dict[str, Any],
    notes: list[str],
    error: str | None,
    settings: Settings | None = None,
) -> bool:
    """Auto-resolve bookkeeping-only conflicts; abort on anything else.

    Every conflicted path must map to a resolver (:func:`_resolver_for_path`)
    **and** that resolver must accept the file's conflict shape. One product
    file, one heading conflict, one prose edit → abort, branch untouched.

    Returns True when the rebase/merge completed. On False the operation has
    been aborted and ``notes`` explains why the caller must stop.
    """
    settings = settings or Settings()
    # During a rebase HEAD is the upstream being replayed onto, so the issue's
    # own commit is the "theirs" side; a merge is the other way around.
    in_flight_side = "theirs" if strategy == "rebase" else "ours"
    root = gitutils.repo_root(project_root) or project_root
    changelog_abs = (project_root / changelog).resolve()

    def rel_to_project(path: str) -> str:
        absolute = (root / path).resolve()
        try:
            return absolute.relative_to(project_root.resolve()).as_posix()
        except ValueError:
            return path.replace("\\", "/")

    for _ in range(_SYNC_RESOLVE_LIMIT):
        unmerged = gitutils.unmerged_paths(project_root)
        if unmerged is None:
            _abort_sync(project_root, strategy, payload, notes)
            notes.append("could not list conflicted paths; aborted and stopped")
            return False
        if not unmerged:
            _abort_sync(project_root, strategy, payload, notes)
            notes.append(
                f"git {strategy} failed without conflicts: {error or 'unknown error'}"
            )
            return False

        payload["conflicts"] = unmerged
        plan: list[tuple[str, str]] = []
        offending: list[str] = []
        for path in unmerged:
            if (root / path).resolve() == changelog_abs:
                plan.append((path, RESOLVER_CHANGELOG))
                continue
            resolver = _resolver_for_path(
                rel_to_project(path), changelog=changelog, settings=settings
            )
            if resolver is None:
                offending.append(path)
            else:
                plan.append((path, resolver))
        if offending:
            _abort_sync(project_root, strategy, payload, notes)
            notes.append(
                "conflicts outside the bookkeeping set "
                f"({', '.join(offending)}); aborted and stopped — "
                "this needs a human decision."
            )
            return False

        for path, resolver in plan:
            conflicted = root / path
            text = conflicted.read_text(encoding="utf-8")
            if resolver == RESOLVER_CHANGELOG:
                result = history.resolve_changelog_conflict(
                    text, in_flight_side=in_flight_side
                )
                refusal = (
                    f"{changelog} conflict is not two additive [Unreleased] "
                    f"bullet lists ({result.reason}); aborted and stopped."
                )
            else:
                result = history.resolve_additive_conflict(
                    text, in_flight_side=in_flight_side
                )
                refusal = (
                    f"{path} conflict is not two additive bullet / table-row "
                    f"sets ({result.reason}); aborted and stopped — this needs "
                    "a human decision."
                )
            if not result.ok or result.text is None:
                _abort_sync(project_root, strategy, payload, notes)
                notes.append(refusal)
                return False
            conflicted.write_text(result.text, encoding="utf-8", newline="")

        ok, stage_error = gitutils.stage_paths(project_root, unmerged)
        if not ok:
            _abort_sync(project_root, strategy, payload, notes)
            notes.append(f"could not stage the resolved paths: {stage_error}")
            return False

        for path, resolver in plan:
            if resolver == RESOLVER_CHANGELOG:
                payload["changelog_resolved"] = True
                notes.append(
                    f"kept both {changelog} bullet sets (in-flight bullet last)"
                )
            else:
                notes.append(f"kept both {path} additions (in-flight last)")
            if path not in payload["resolved_paths"]:
                payload["resolved_paths"].append(path)
            payload["resolvers"][path] = resolver

        if strategy == "rebase":
            ok, error = gitutils.rebase_continue(project_root)
        else:
            ok, error = gitutils.merge_continue(project_root)
        if ok:
            payload["conflicts"] = []
            return True

    _abort_sync(project_root, strategy, payload, notes)
    notes.append(
        f"more than {_SYNC_RESOLVE_LIMIT} conflicted commits; aborted and stopped"
    )
    return False


def _render_sync_branch_text(
    console: Console, payload: dict[str, Any], exit_code: int
) -> None:
    if exit_code == 0:
        branch = escape(payload["branch"] or "(detached)")
        default = escape(payload["default_branch"] or "?")
        action = payload["action"]
        if action == "none":
            console.print(f"[green]ok[/green]  [bold]{branch}[/bold] is in sync.")
        else:
            console.print(
                f"[green]ok[/green]  [bold]{branch}[/bold] {action} onto "
                f"origin/{default}."
            )
        if payload["needs_force_push"]:
            console.print(
                "  [yellow]note[/yellow]  history was rewritten — push with "
                "--force-with-lease"
            )
        if payload.get("base"):
            how = "detected" if payload.get("base_detected") else "given"
            console.print(
                f"  [dim]base {escape(str(payload['base']))} ({how}); dropped "
                f"{payload.get('dropped_commits', 0)} landed commit(s)[/dim]"
            )
        for path, resolver in (payload.get("resolvers") or {}).items():
            console.print(f"  [dim]resolved[/dim]  {escape(path)} ({resolver})")
    for path in payload["dirty_paths"]:
        console.print(f"  [yellow]dirty[/yellow]  {escape(path)}")
    for path in payload["conflicts"]:
        console.print(f"  [red]conflict[/red]  {escape(path)}")
    for note in payload["notes"]:
        style = "red" if exit_code != 0 else "dim"
        console.print(f"  [{style}]{escape(note)}[/{style}]")


# ---------------------------------------------------------------------------
# agent pr-sync (multi-PR HISTORY refresh, issue #260)
# ---------------------------------------------------------------------------

_NEEDS_SYNC_STATES = frozenset({"DIRTY", "BEHIND", "BLOCKED", "UNKNOWN"})


def _pr_needs_sync(pr: dict[str, Any]) -> bool:
    """True when GitHub says the PR is behind or conflicted."""
    mergeable = str(pr.get("mergeable") or "").upper()
    state = str(pr.get("mergeStateStatus") or "").upper()
    if mergeable == "CONFLICTING":
        return True
    if state in _NEEDS_SYNC_STATES:
        return True
    return False


_FAILURE_CONCLUSIONS = frozenset(
    {
        "FAILURE",
        "CANCELLED",
        "TIMED_OUT",
        "ACTION_REQUIRED",
        "STARTUP_FAILURE",
        "ERROR",
    }
)
_PENDING_STATUSES = frozenset(
    {"QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED"}
)
_OK_CONCLUSIONS = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
_PR_READY_POLL_SECONDS = 15.0


def _rollup_checks(
    pr: dict[str, Any],
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return pending, failing, required_pending, required_failing check names."""
    pending: list[str] = []
    failing: list[str] = []
    required_pending: list[str] = []
    required_failing: list[str] = []
    rollup = pr.get("statusCheckRollup")
    if not isinstance(rollup, list):
        return pending, failing, required_pending, required_failing
    for item in rollup:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("context") or "?")
        required = item.get("isRequired")
        conclusion = str(item.get("conclusion") or item.get("state") or "").upper()
        status = str(item.get("status") or "").upper()
        failed = conclusion in _FAILURE_CONCLUSIONS
        in_flight = status in _PENDING_STATUSES or conclusion in {"PENDING", ""}
        if failed:
            failing.append(name)
            if required is True:
                required_failing.append(name)
        elif in_flight and conclusion not in _OK_CONCLUSIONS:
            pending.append(name)
            if required is True:
                required_pending.append(name)
    return pending, failing, required_pending, required_failing


def _blocking_checks(pr: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Failing and pending names that are not explicitly optional."""
    failing: list[str] = []
    pending: list[str] = []
    rollup = pr.get("statusCheckRollup")
    if not isinstance(rollup, list):
        return failing, pending
    for item in rollup:
        if not isinstance(item, dict) or item.get("isRequired") is False:
            continue
        name = str(item.get("name") or item.get("context") or "?")
        conclusion = str(item.get("conclusion") or item.get("state") or "").upper()
        status = str(item.get("status") or "").upper()
        failed = conclusion in _FAILURE_CONCLUSIONS
        in_flight = status in _PENDING_STATUSES or conclusion in {"PENDING", ""}
        if failed:
            failing.append(name)
        elif in_flight and conclusion not in _OK_CONCLUSIONS:
            pending.append(name)
    return failing, pending


def classify_pr_ready(
    pr: dict[str, Any] | None, *, gh_available: bool
) -> dict[str, Any]:
    """Classify whether an open PR is allowed to merge. Never merges."""
    notes: list[str] = []
    pending_checks: list[str] = []
    failing_checks: list[str] = []
    payload: dict[str, Any] = {
        "state": "unknown",
        "pr": None,
        "url": None,
        "title": None,
        "isDraft": None,
        "mergeable": None,
        "mergeStateStatus": None,
        "reviewDecision": None,
        "pending_checks": pending_checks,
        "failing_checks": failing_checks,
        "notes": notes,
    }
    if not gh_available:
        notes.append("gh is not on PATH")
        return payload
    if pr is None:
        notes.append("could not load PR")
        return payload

    payload["pr"] = pr.get("number")
    payload["url"] = pr.get("url")
    payload["title"] = pr.get("title")
    is_draft = bool(pr.get("isDraft"))
    payload["isDraft"] = is_draft
    mergeable = str(pr.get("mergeable") or "").upper()
    merge_state = str(pr.get("mergeStateStatus") or "").upper()
    review = str(pr.get("reviewDecision") or "").upper()
    pr_state = str(pr.get("state") or "").upper()
    payload["mergeable"] = mergeable or None
    payload["mergeStateStatus"] = merge_state or None
    payload["reviewDecision"] = review or None

    pending_all, failing_all, _required_pending, _required_failing = _rollup_checks(pr)
    pending_checks.extend(pending_all)
    failing_checks.extend(failing_all)
    block_failing, block_pending = _blocking_checks(pr)

    if pr_state in {"CLOSED", "MERGED"}:
        payload["state"] = "blocked"
        notes.append(f"PR is {pr_state.lower()}")
        return payload
    if is_draft or merge_state == "DRAFT":
        payload["state"] = "blocked"
        notes.append("PR is a draft")
        return payload
    if mergeable == "CONFLICTING" or merge_state in {"DIRTY"}:
        payload["state"] = "blocked"
        notes.append("PR has merge conflicts")
        return payload
    if review == "CHANGES_REQUESTED":
        payload["state"] = "blocked"
        notes.append("review requested changes")
        return payload
    if block_failing:
        payload["state"] = "blocked"
        notes.append("required checks failed: " + ", ".join(block_failing))
        return payload
    if mergeable in {"", "UNKNOWN"} or merge_state in {
        "UNKNOWN",
        "BLOCKED",
        "BEHIND",
    }:
        payload["state"] = "pending"
        notes.append("mergeability or required gate still in flight")
        return payload
    if block_pending:
        payload["state"] = "pending"
        notes.append("required checks pending: " + ", ".join(block_pending))
        return payload
    if review == "REVIEW_REQUIRED":
        payload["state"] = "pending"
        notes.append("required review still missing")
        return payload
    if (
        mergeable == "MERGEABLE"
        and merge_state in {"CLEAN", "UNSTABLE"}
        and not is_draft
        and pr_state in {"", "OPEN"}
    ):
        payload["state"] = "ready"
        if merge_state == "UNSTABLE" and (pending_all or failing_all):
            notes.append("UNSTABLE with optional-only noise; treating as ready")
        return payload

    payload["state"] = "unknown"
    notes.append("could not classify merge-ready state")
    return payload


def run_pr_ready(
    project_root: Path,
    console: Console,
    number: int | None,
    *,
    watch: bool,
    as_json: bool,
    repo: str | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    monotonic_fn: Callable[[], float] = time.monotonic,
    poll_seconds: float = _PR_READY_POLL_SECONDS,
) -> int:
    """Classify whether PR ``number`` (or the current branch PR) can merge.

    Read-only: never merges. Exit 0 only when ``state`` is ``ready``.
    """
    settings = Settings()
    budget_min = settings.resolve_checks_watch_minutes(project_root)
    notes: list[str] = []
    payload: dict[str, Any] = {
        "gh_available": gitutils.gh_available(),
        "repo": repo,
        "watch": watch,
        "budget_minutes": budget_min,
        "state": "unknown",
        "pr": number,
        "url": None,
        "title": None,
        "isDraft": None,
        "mergeable": None,
        "mergeStateStatus": None,
        "reviewDecision": None,
        "pending_checks": [],
        "failing_checks": [],
        "notes": notes,
    }

    def emit(exit_code: int) -> int:
        if as_json:
            _emit_json(console, payload)
        else:
            _render_pr_ready_text(console, payload, exit_code)
        return exit_code

    if not payload["gh_available"]:
        notes.append("gh is not on PATH")
        return emit(1)

    home = gitutils.worktree_home_path(project_root) or project_root.resolve()
    if repo is None:
        remote = gitutils.remote_owner_repo(home)
        repo = f"{remote[0]}/{remote[1]}" if remote else None
    payload["repo"] = repo
    if repo is None:
        notes.append("could not resolve owner/repo from origin")
        return emit(1)

    deadline = monotonic_fn() + (budget_min * 60 if watch else 0)
    classified: dict[str, Any] | None = None
    while True:
        pr = gitutils.gh_pr_view(home, number, repo=repo)
        if pr is None and number is None:
            notes.clear()
            notes.append("no PR for this branch")
            payload["state"] = "unknown"
            return emit(1)
        classified = classify_pr_ready(pr, gh_available=True)
        for key in (
            "state",
            "pr",
            "url",
            "title",
            "isDraft",
            "mergeable",
            "mergeStateStatus",
            "reviewDecision",
            "pending_checks",
            "failing_checks",
        ):
            payload[key] = classified[key]
        payload["notes"] = classified["notes"]
        notes = classified["notes"]
        state = classified["state"]
        if state in {"ready", "blocked"} or not watch:
            return emit(0 if state == "ready" else 1)
        if monotonic_fn() >= deadline:
            notes.append(f"watch budget ({budget_min} min) elapsed still {state}")
            payload["notes"] = notes
            return emit(1)
        if not as_json:
            _render_pr_ready_text(console, payload, 1)
        sleep_fn(poll_seconds)


def _render_pr_ready_text(
    console: Console, payload: dict[str, Any], exit_code: int
) -> None:
    state = str(payload.get("state") or "unknown")
    style = "green" if exit_code == 0 else "yellow" if state == "pending" else "red"
    pr = payload.get("pr")
    label = f"#{pr}" if pr is not None else "current branch"
    console.print(f"[{style}]{state}[/{style}]  PR {label}")
    if payload.get("url"):
        console.print(f"  {escape(str(payload['url']))}")
    for field in (
        "title",
        "isDraft",
        "mergeable",
        "mergeStateStatus",
        "reviewDecision",
    ):
        value = payload.get(field)
        if value is not None and value != "":
            console.print(f"  {field}: {escape(str(value))}")
    pending = payload.get("pending_checks") or []
    failing = payload.get("failing_checks") or []
    if pending:
        console.print(f"  pending: {escape(', '.join(str(n) for n in pending))}")
    if failing:
        console.print(f"  failing: {escape(', '.join(str(n) for n in failing))}")
    for note in payload.get("notes") or []:
        console.print(f"  [dim]{escape(str(note))}[/dim]")


def run_pr_sync(
    project_root: Path,
    console: Console,
    *,
    numbers: list[int] | None,
    all_open: bool,
    dirty_only: bool,
    dry_run: bool,
    push: bool,
    fail_fast: bool,
    strategy: str,
    cleanup_worktrees: bool,
    as_json: bool,
) -> int:
    """Refresh open PR heads onto ``origin/<default>`` (changelog keep-both).

    Loops ``sync-branch`` over each candidate head in an isolated worktree, then
    optionally ``git push --force-with-lease``. Never uses bare ``--force``.
    """
    notes: list[str] = []
    results: list[dict[str, Any]] = []
    payload: dict[str, Any] = {
        "git_available": gitutils.git_available(),
        "gh_available": gitutils.gh_available(),
        "default_branch": None,
        "repo": None,
        "dry_run": dry_run,
        "push": push and not dry_run,
        "strategy": strategy,
        "candidates": [],
        "results": results,
        "notes": notes,
    }

    def emit(exit_code: int) -> int:
        if as_json:
            _emit_json(console, payload)
        else:
            _render_pr_sync_text(console, payload, exit_code)
        return exit_code

    if strategy not in SYNC_STRATEGIES:
        notes.append(
            f"unknown strategy {strategy!r}; expected one of "
            f"{', '.join(SYNC_STRATEGIES)}"
        )
        return emit(1)
    if not payload["git_available"]:
        notes.append("git is not on PATH")
        return emit(1)
    if not payload["gh_available"]:
        notes.append("gh is not on PATH")
        return emit(1)

    home = gitutils.worktree_home_path(project_root) or project_root.resolve()
    default = gitutils.default_branch(home)
    payload["default_branch"] = default
    remote = gitutils.remote_owner_repo(home)
    repo = f"{remote[0]}/{remote[1]}" if remote else None
    payload["repo"] = repo

    if not gitutils.fetch_prune(home):
        notes.append("git fetch --prune failed; continuing with stale refs")

    candidates: list[dict[str, Any]] = []
    if numbers:
        for number in numbers:
            pr = gitutils.gh_pr_view(home, number, repo=repo)
            if pr is None:
                notes.append(f"could not load PR #{number}")
                if fail_fast:
                    return emit(1)
                continue
            if str(pr.get("state") or "").upper() != "OPEN":
                notes.append(f"PR #{number} is not open; skipped")
                continue
            candidates.append(pr)
    else:
        listed = gitutils.gh_open_prs(home, repo=repo)
        if listed is None:
            notes.append("gh pr list failed")
            return emit(1)
        for pr in listed:
            if dirty_only or not all_open:
                if not _pr_needs_sync(pr):
                    continue
            candidates.append(pr)

    filtered: list[dict[str, Any]] = []
    for pr in candidates:
        base = pr.get("baseRefName") or default
        if base != default:
            notes.append(
                f"PR #{pr.get('number')} bases on {base!r}, not {default!r}; skipped"
            )
            continue
        head = pr.get("headRefName")
        if not head or head == default:
            notes.append(f"PR #{pr.get('number')} has unusable head; skipped")
            continue
        filtered.append(pr)
    candidates = filtered
    payload["candidates"] = [
        {
            "number": p.get("number"),
            "title": p.get("title"),
            "url": p.get("url"),
            "head": p.get("headRefName"),
            "mergeable": p.get("mergeable"),
            "mergeStateStatus": p.get("mergeStateStatus"),
        }
        for p in candidates
    ]

    if not candidates:
        notes.append("no open PRs need sync")
        return emit(0)

    if dry_run:
        notes.append("dry-run: no sync or push performed")
        return emit(0)

    overall_ok = True
    for pr in candidates:
        number = int(pr["number"])
        head = str(pr["headRefName"])
        entry: dict[str, Any] = {
            "number": number,
            "head": head,
            "url": pr.get("url"),
            "ok": False,
            "synced": False,
            "pushed": False,
            "changelog_resolved": False,
            "worktree": None,
            "ephemeral_worktree": False,
            "notes": [],
        }
        path, _created, ephemeral, error = gitutils.ensure_branch_worktree(home, head)
        if path is None:
            entry["notes"].append(error or "could not create worktree")
            results.append(entry)
            overall_ok = False
            if fail_fast:
                notes.append(f"stopped on PR #{number}")
                return emit(1)
            continue
        entry["worktree"] = str(path)
        entry["ephemeral_worktree"] = ephemeral

        from io import StringIO

        buf = StringIO()
        quiet = Console(file=buf, force_terminal=False, soft_wrap=True, no_color=True)
        code = run_sync_branch(path, quiet, strategy, as_json=True)
        raw = buf.getvalue().strip()
        # Rich print_json may leave a trailing newline; take the last JSON object.
        sync_payload: dict[str, Any] = {}
        if raw:
            try:
                # Prefer the last line that looks like JSON.
                for line in reversed(raw.splitlines()):
                    line = line.strip()
                    if line.startswith("{"):
                        sync_payload = json.loads(line)
                        break
                else:
                    sync_payload = json.loads(raw)
            except json.JSONDecodeError:
                entry["notes"].append("could not parse sync-branch JSON")
        entry["synced"] = code == 0
        entry["changelog_resolved"] = bool(sync_payload.get("changelog_resolved"))
        entry["needs_force_push"] = bool(sync_payload.get("needs_force_push"))
        entry["notes"].extend(sync_payload.get("notes") or [])
        if code != 0:
            entry["ok"] = False
            results.append(entry)
            overall_ok = False
            if cleanup_worktrees and ephemeral:
                gitutils.remove_worktree(home, path, force=True)
            if fail_fast:
                notes.append(f"stopped on PR #{number} (sync failed)")
                return emit(1)
            continue

        if push:
            # After a successful sync, push with --force-with-lease whenever the
            # branch tip may have moved (rebase) or still be ahead.
            ok, push_err = gitutils.push_force_with_lease(path, branch=head)
            entry["pushed"] = ok
            if not ok:
                entry["notes"].append(push_err or "push failed")
                entry["ok"] = False
                overall_ok = False
                results.append(entry)
                if cleanup_worktrees and ephemeral:
                    gitutils.remove_worktree(home, path, force=True)
                if fail_fast:
                    notes.append(f"stopped on PR #{number} (push failed)")
                    return emit(1)
                continue

        entry["ok"] = True
        results.append(entry)
        if cleanup_worktrees and ephemeral:
            gitutils.remove_worktree(home, path, force=True)

    return emit(0 if overall_ok else 1)


def _render_pr_sync_text(
    console: Console, payload: dict[str, Any], exit_code: int
) -> None:
    cands = payload.get("candidates") or []
    console.print(
        f"[bold]pr-sync[/bold]  {len(cands)} candidate(s)"
        + (" [dim](dry-run)[/dim]" if payload.get("dry_run") else "")
    )
    for item in cands:
        console.print(
            f"  #{item.get('number')}  {escape(str(item.get('head')))}  "
            f"{item.get('mergeable')}/{item.get('mergeStateStatus')}"
        )
    for entry in payload.get("results") or []:
        mark = "green" if entry.get("ok") else "red"
        console.print(
            f"  [{mark}]{'ok' if entry.get('ok') else 'fail'}[/{mark}]  "
            f"#{entry.get('number')} {escape(str(entry.get('head')))}"
            f"{' synced' if entry.get('synced') else ''}"
            f"{' pushed' if entry.get('pushed') else ''}"
        )
        for note in entry.get("notes") or []:
            console.print(f"    [dim]{escape(str(note))}[/dim]")
    for note in payload.get("notes") or []:
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
# agent open-workspace (issue #253)
# ---------------------------------------------------------------------------


def _editor_binary_candidates(editor_id: str) -> list[str]:
    """Ordered binary names to try for launching an editor workspace."""
    primary = {
        "cursor": "cursor",
        "claude": "claude",
        "opencode": "opencode",
        "codex": "codex",
    }.get(editor_id, editor_id)
    out: list[str] = []
    for name in (primary, "cursor", "code"):
        if name and name not in out:
            out.append(name)
    return out


def _resolve_open_workspace_target(
    project_dir: Path,
    target: str | None,
    *,
    issueflows_dir: str,
) -> tuple[Path | None, str | None, str]:
    """Resolve a folder path for ``open-workspace``.

    Returns ``(path, error, resolved_via)``. ``resolved_via`` is one of
    ``project_dir``, ``path``, ``workspace_member``.
    """
    start = project_dir.resolve()
    if target is None or not target.strip():
        root = project.find_project_root(start, issueflows_dir=issueflows_dir) or start
        return root, None, "project_dir"

    raw = target.strip()
    as_path = Path(raw)
    if as_path.is_absolute():
        if as_path.is_dir():
            return as_path.resolve(), None, "path"
        return None, f"target path does not exist or is not a directory: {raw}", "path"

    for base in (Path.cwd(), start):
        candidate = (base / raw).resolve()
        if candidate.is_dir():
            return candidate, None, "path"

    workspace = project.discover_workspace(start, issueflows_dir=issueflows_dir)
    if workspace is not None and raw in workspace.members:
        member_path = (workspace.root / raw).resolve()
        if member_path.is_dir():
            return member_path, None, "workspace_member"
        return (
            None,
            f"workspace member '{raw}' path missing: {member_path}",
            "workspace_member",
        )

    return None, f"target not found as path or workspace member: {raw}", "none"


def run_open_workspace(
    project_dir: Path,
    console: Console,
    target: str | None,
    do_open: bool,
    as_json: bool,
    *,
    editor_id: str | None = None,
) -> int:
    """Print (and optionally launch) a path as its own editor workspace.

    Default is print-only. ``--open`` spawns the editor binary when found;
    skills must confirm before passing ``--open``. Never creates worktrees or
    ``.code-workspace`` files.
    """
    settings = Settings()
    resolved_editor = (editor_id or settings.editor or DEFAULT_EDITOR).strip().lower()
    path, error, via = _resolve_open_workspace_target(
        project_dir,
        target,
        issueflows_dir=settings.issueflows_dir,
    )

    candidates = _editor_binary_candidates(resolved_editor)
    binary: str | None = None
    for name in candidates:
        found = shutil.which(name)
        if found:
            binary = found
            break

    suggested_argv = [binary or candidates[0], str(path)] if path is not None else []

    payload: dict[str, Any] = {
        "path": str(path) if path is not None else None,
        "resolved_via": via,
        "editor": resolved_editor,
        "binary": binary,
        "binary_found": binary is not None,
        "suggested_argv": suggested_argv,
        "opened": False,
        "error": error,
    }

    if path is None:
        if as_json:
            _emit_json(console, payload)
        else:
            console.print(f"[red]error[/red]  {escape(error or 'target not found')}")
        return 1

    if do_open:
        if binary is None:
            msg = (
                "no editor binary found on PATH "
                f"(tried: {', '.join(candidates)}); print-only still works"
            )
            payload["error"] = msg
            if as_json:
                _emit_json(console, payload)
            else:
                console.print(f"[red]error[/red]  {escape(msg)}")
                console.print(f"[bold]Path[/bold]: {path}")
            return 1
        try:
            subprocess.Popen(  # noqa: S603 — argv is our resolved binary + path
                [binary, str(path)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            msg = f"failed to launch editor: {exc}"
            payload["error"] = msg
            if as_json:
                _emit_json(console, payload)
            else:
                console.print(f"[red]error[/red]  {escape(msg)}")
            return 1
        payload["opened"] = True

    if as_json:
        _emit_json(console, payload)
        return 0

    console.print(f"[bold]Path[/bold]: {path}")
    console.print(f"[bold]Resolved via[/bold]: {via}")
    console.print(f"[bold]Editor[/bold]: {resolved_editor}")
    if binary:
        console.print(f"[bold]Binary[/bold]: {binary}")
    else:
        console.print(
            "[bold]Binary[/bold]: [yellow]not found[/yellow] "
            f"(tried: {', '.join(candidates)})"
        )
    if suggested_argv:
        console.print(f"[bold]Suggested[/bold]: {' '.join(suggested_argv)}")
    if do_open and payload["opened"]:
        console.print("[green]Opened[/green] (non-blocking).")
    elif not do_open:
        console.print(
            "[dim]Print-only. Pass --open after confirm to launch "
            "(skills must never auto-open).[/dim]"
        )
    return 0


# ---------------------------------------------------------------------------
# agent worktree-add / list / remove (issue #255)
# ---------------------------------------------------------------------------


def _worktree_location(home: Path, number: int) -> gitutils.WorktreeLocation:
    """Resolve where issue ``number``'s worktree goes, honouring #328 settings."""
    settings = Settings()
    return gitutils.resolve_worktree_location(
        home,
        number,
        worktrees_dir=settings.resolve_worktrees_dir(home),
        in_workspace=settings.resolve_worktrees_in_workspace(home),
    )


def run_worktree_add(
    project_dir: Path,
    console: Console,
    number: int,
    slug: str,
    as_json: bool,
) -> int:
    """Create the issue worktree on ``<N>-<slug>`` without switching home.

    The folder is ``../<repo>-<N>`` unless ``worktrees_dir`` /
    ``worktrees_in_workspace`` say otherwise; ``location`` in the payload
    reports which rule applied (#328).
    """
    home = project_dir.resolve()
    cleaned = slug.strip().lstrip("/")
    if cleaned.startswith(f"{number}-"):
        cleaned = cleaned[len(f"{number}-") :]
    if not cleaned or "/" in cleaned or "\\" in cleaned:
        error = f"invalid slug: {slug!r}"
        payload = {
            "path": None,
            "branch": None,
            "home_path": str(home),
            "home_branch": gitutils.current_branch(home),
            "created": False,
            "error": error,
        }
        if as_json:
            _emit_json(console, payload)
        else:
            console.print(f"[red]error[/red]  {escape(error)}")
        return 1

    location = _worktree_location(home, number)
    path, created, error = gitutils.add_worktree(
        home, number=number, slug=cleaned, target=location.path
    )
    payload = {
        "path": str(path) if path is not None else None,
        "branch": f"{number}-{cleaned}",
        "home_path": str(home),
        "home_branch": gitutils.current_branch(home),
        "created": created,
        "location": location.reason,
        "location_note": location.note,
        "error": error,
    }
    if error or path is None:
        if as_json:
            _emit_json(console, payload)
        else:
            console.print(f"[red]error[/red]  {escape(error or 'worktree add failed')}")
        return 1
    if as_json:
        _emit_json(console, payload)
        return 0
    verb = "Created" if created else "Reused"
    console.print(f"[bold]{verb}[/bold]: {path}  [dim]({location.reason})[/dim]")
    if location.note:
        console.print(f"[yellow]note[/yellow]  {escape(location.note)}")
    console.print(f"[bold]Branch[/bold]: {payload['branch']}")
    console.print(f"[bold]Home[/bold]: {home} ({payload['home_branch']})")
    return 0


def run_worktree_list(
    project_dir: Path,
    console: Console,
    as_json: bool,
) -> int:
    """List git worktrees for the repo that contains ``project_dir``."""
    home = gitutils.worktree_home_path(project_dir) or project_dir.resolve()
    entries = gitutils.list_worktrees(project_dir)
    payload = {
        "home_path": str(home),
        "worktrees": [
            {
                "path": str(info.path),
                "branch": info.branch,
                "head": info.head,
                "is_main": info.is_main,
            }
            for info in entries
        ],
    }
    if as_json:
        _emit_json(console, payload)
        return 0
    if not entries:
        console.print("[dim]No worktrees found.[/dim]")
        return 0
    for info in entries:
        kind = "home" if info.is_main else "linked"
        branch = info.branch or "(detached)"
        console.print(f"  {info.path}  {branch}  [dim]{kind}[/dim]")
    return 0


def run_worktree_remove(
    project_dir: Path,
    console: Console,
    target: str,
    as_json: bool,
    *,
    force: bool = False,
) -> int:
    """Remove a linked worktree by path or issue number."""
    home = gitutils.worktree_home_path(project_dir) or project_dir.resolve()
    path: Path | None = None
    raw = target.strip()
    if raw.isdigit():
        number = int(raw)
        expected = _worktree_location(home, number).path
        prefix = f"{number}-"
        for info in gitutils.list_worktrees(home):
            if info.is_main:
                continue
            if info.path == expected.resolve() or (
                info.branch is not None and info.branch.startswith(prefix)
            ):
                path = info.path
                break
        if path is None:
            path = expected if expected.is_dir() else None
    else:
        candidate = Path(raw)
        path = candidate.resolve() if candidate.exists() else None

    error = None
    removed = False
    if path is None:
        error = f"worktree not found: {raw}"
    else:
        removed, error = gitutils.remove_worktree(home, path, force=force)

    payload = {
        "path": str(path) if path is not None else None,
        "removed": removed,
        "error": error,
        "home_path": str(home),
    }
    if as_json:
        _emit_json(console, payload)
        return 0 if removed else 1
    if removed:
        console.print(f"[green]Removed[/green] {path}")
        return 0
    console.print(f"[red]error[/red]  {escape(error or 'remove failed')}")
    return 1


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


def run_publish_intent(
    project_root: Path,
    console: Console,
    *,
    issue: int | None,
    labels: list[str],
    as_json: bool,
) -> int:
    """Resolve publish-on-success intent from labels (read-only; issue #308).

    When ``issue`` is set, fetch that issue's labels via ``gh``. Otherwise use
    the explicit ``labels`` list. Never bumps or creates releases.
    """
    from issue_flow import publishintent, versionplan

    settings = Settings()
    publish_label = settings.resolve_publish_label(project_root)
    notes: list[str] = []

    resolved_labels = list(labels)
    if issue is not None:
        repo_slug: str | None = None
        owner_repo = gitutils.remote_owner_repo(project_root)
        if owner_repo is not None:
            repo_slug = f"{owner_repo[0]}/{owner_repo[1]}"
        meta = gitutils.gh_issue_meta(issue, project_root, repo_slug)
        if meta is None:
            msg = f"could not fetch issue #{issue} (gh missing or unauthenticated)."
            if as_json:
                _emit_json(console, {"error": msg, "issue": issue})
            else:
                console.print(f"[red]error[/red]  {msg}")
            return 1
        resolved_labels = _label_names(meta.get("labels"))
        notes.append(
            f"labels from issue #{issue}: " + (", ".join(resolved_labels) or "(none)")
        )

    strategy, _reason, static_version = versionplan.detect_strategy(project_root)
    current_text: str | None = None
    if strategy == "uv":
        current_text = static_version
    elif strategy == "tag":
        tag = gitutils.latest_tag(project_root)
        current_text = tag
        if tag is None:
            notes.append("no git tags found; explicit-version logic may be unverified.")
    else:
        notes.append(
            "release strategy unknown; explicit-version logic may be unverified."
        )

    current = versionplan.parse_version(current_text) if current_text else None
    current_version = (
        current.formatted().lstrip("v") if current else (current_text or None)
    )

    intent = publishintent.resolve_publish_intent(
        resolved_labels,
        publish_label,
        current_version=current_version,
    )
    payload = publishintent.intent_to_dict(intent)
    payload["current_version"] = current_version
    payload["labels"] = resolved_labels
    payload["issue"] = issue
    payload["label_flows"] = settings.resolve_label_flows(project_root)
    merged_notes = list(payload.get("notes") or [])
    merged_notes.extend(notes)
    payload["notes"] = merged_notes

    if as_json:
        _emit_json(console, payload)
    else:
        if not intent.matched:
            console.print(
                f"no publish label matched "
                f"(looking for '{publish_label}' / '{publish_label}:…')"
            )
        else:
            console.print(
                f"publish intent: kind={intent.kind} level={intent.level} "
                f"target={intent.target_version} logical={intent.logical} "
                f"conflict={intent.conflict} label={intent.label!r}"
            )
            if intent.suggestion:
                console.print(f"suggestion: {intent.suggestion}")
        for note in payload["notes"]:
            console.print(f"[dim]- {note}[/dim]")
    if intent.conflict or intent.logical is False:
        return 2
    return 0


# ---------------------------------------------------------------------------
# agent epic-status
# ---------------------------------------------------------------------------

_EPIC_PLAN_NAME = re.compile(r"^epic(\d+)_plan\.md$")


def _build_epic_status_payload(
    project_root: Path,
    number: int,
    *,
    local: bool,
) -> dict[str, Any] | None:
    """Return the epic-status JSON payload, or ``None`` if the plan is missing."""
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
        return None

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

    return {
        "epic": plan.number if plan.number is not None else number,
        "title": plan.title,
        "plan_status": plan.status,
        "local": local,
        "stages": stage_payloads,
        "current_stage": current_stage,
        "next_candidates": next_candidates,
    }


def _collect_epic_hints(
    project_root: Path,
    *,
    local: bool,
) -> dict[str, Any]:
    """Scan ``05-epics/`` for plans with non-empty ``next_candidates``.

    Used by ``agent state`` when there is no focus issue so ``/iflow`` can
    recommend ``/iflow-pick`` (issue #210). Never auto-picks.
    """
    settings = Settings()
    epics_dir = project_root / settings.issueflows_dir / settings.epics_folder
    entries: list[dict[str, Any]] = []
    if epics_dir.is_dir():
        for path in sorted(epics_dir.iterdir()):
            match = _EPIC_PLAN_NAME.match(path.name)
            if match is None:
                continue
            number = int(match.group(1))
            payload = _build_epic_status_payload(project_root, number, local=local)
            if payload is None:
                continue
            candidates = payload.get("next_candidates") or []
            if not candidates:
                continue
            stage_title = ""
            current = payload.get("current_stage")
            for stage in payload.get("stages") or []:
                if stage.get("index") == current:
                    stage_title = stage.get("title") or ""
                    break
            entries.append(
                {
                    "epic": payload["epic"],
                    "title": payload.get("title") or "",
                    "stage": current,
                    "stage_title": stage_title,
                    "next_candidates": list(candidates),
                }
            )
    return {"epics": entries}


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
    settings = Settings()
    plan_path = (
        project_root
        / settings.issueflows_dir
        / settings.epics_folder
        / f"epic{number}_plan.md"
    )
    payload = _build_epic_status_payload(project_root, number, local=local)
    if payload is None:
        msg = f"no epic plan found at {plan_path}; draft one with /iflow-epic {number}."
        if as_json:
            _emit_json(console, {"epic": number, "error": msg})
        else:
            console.print(f"[red]error[/red]  {escape(msg)}")
        return 1

    if as_json:
        _emit_json(console, payload)
        return 0

    stage_payloads = payload["stages"]
    current_stage = payload["current_stage"]
    next_candidates = payload["next_candidates"]

    console.print(
        f"[bold]Epic #{payload['epic']}[/bold] — {escape(payload['title'])} "
        f"[dim](plan: {payload['plan_status']})[/dim]"
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

    # Dependencies outside the queue (e.g. a previous epic stage): look up
    # their state so closed ones satisfy dependencies instead of blocking.
    in_queue = {item.number for item in items}
    outside = sorted({dep for item in items for dep in item.depends_on} - in_queue)
    closed_external = {
        dep
        for dep in outside
        if gitutils.gh_issue_state(dep, project_root, repo_slug) == "closed"
    }
    plan = queueplan.build_queue(items, closed_external=closed_external)

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
        # #386: the hands-off drivers (/iflow-cycle, /iflow-auto, /iflow-drive)
        # surface these in their confirm so the operator knows which issues
        # will take the non-yolo lane (policy: cycle_nonyolo) instead of
        # stopping the run.
        "nonyolo": [item.number for item in plan.ordered if not item.yolo],
        "nonyolo_count": sum(1 for item in plan.ordered if not item.yolo),
        "notes": notes,
    }

    if as_json:
        _emit_json(console, payload)
        return 0

    if not plan.ordered:
        console.print("[dim]Nothing to queue.[/dim]")
    for entry in payload["queue"]:
        flags = " [yolo]" if entry["yolo"] else " [non-yolo]"
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
    if payload["nonyolo"]:
        console.print(
            f"  [yellow]non-yolo lane[/yellow] ({payload['nonyolo_count']}): "
            + ", ".join(f"#{n}" for n in payload["nonyolo"])
            + " — merge policy: cycle_nonyolo"
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
    *,
    sync_code_workspace: bool = False,
    code_workspace_path: str | None = None,
    drop_unknown_folders: bool = False,
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

    cw_path: Path | None = None
    if sync_code_workspace:
        try:
            cw_path = project.resolve_code_workspace_path(root, code_workspace_path)
            if cw_path.is_file():
                project.load_code_workspace(cw_path)
        except project.CodeWorkspaceError as exc:
            return _fail(str(exc))

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
        "code_workspace": None,
    }
    if cw_path is not None:
        payload["code_workspace"] = project.sync_code_workspace(
            cw_path, members, drop_unknown=drop_unknown_folders
        )
    if as_json:
        _emit_json(console, payload)
        return 0

    console.print(f"[green]wrote[/green]  {target}")
    console.print(
        f"  members: {', '.join(members)} — default: "
        f"{escape(default) if default else '(none; edit the file to set one)'}"
    )
    cw = payload.get("code_workspace")
    if isinstance(cw, dict) and cw.get("path"):
        console.print(f"[green]wrote[/green]  {escape(str(cw['path']))}")
    return 0


def run_workspace_bootstrap(
    workspace_dir: Path,
    console: Console,
    default: str | None,
    apply: bool,
    force: bool,
    skip_dep_check: bool,
    editors: list[str] | None,
    as_json: bool,
    *,
    sync_code_workspace: bool = False,
    code_workspace_path: str | None = None,
) -> int:
    """Classify (and optionally init) git siblings, then write the workspace file.

    Classify-only when ``apply`` is false. ``--yes`` inits unscaffolded own-git
    children via :func:`issue_flow.init.run_init` and then
    :func:`run_workspace_init`. Never writes ``.issueflows/`` on the parent
    and never ``git init`` s children.
    """
    import typer

    import issue_flow.console_io as console_module
    from issue_flow.init import run_init

    settings = Settings()
    root = workspace_dir.resolve()
    children = project.classify_immediate_children(
        root, issueflows_dir=settings.issueflows_dir
    )
    members = [
        child
        for child in children
        if child.status in (project.CHILD_SCAFFOLDED, project.CHILD_UNSCAFFOLDED)
    ]
    member_names = [child.name for child in members]
    proposed_default = next(
        (child.name for child in members if child.status == project.CHILD_SCAFFOLDED),
        members[0].name if members else None,
    )
    next_command = (
        f"issue-flow workspace bootstrap {root} --yes --default {proposed_default}"
        if proposed_default
        else None
    )
    toml_path = root / project.WORKSPACE_FILENAME
    workspace_exists = toml_path.is_file()
    existing_workspace = (
        project.load_workspace(toml_path, issueflows_dir=settings.issueflows_dir)
        if workspace_exists
        else None
    )
    existing_names = existing_workspace.members if existing_workspace else []
    existing_default = existing_workspace.default if existing_workspace else None
    missing_from_toml = [name for name in member_names if name not in existing_names]

    def _child_payload(child: project.WorkspaceChild) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": child.name,
            "path": str(child.path),
            "status": child.status,
        }
        if child.reason:
            payload["reason"] = child.reason
        return payload

    def _fail(msg: str) -> int:
        payload: dict[str, Any] = {
            "applied": apply,
            "ok": False,
            "error": msg,
            "workspace_root": str(root),
            "workspace_exists": workspace_exists,
            "workspace_written": False,
            "default": default,
            "proposed_default": proposed_default,
            "next_command": next_command,
            "children": [_child_payload(c) for c in children],
            "members": [],
            "ok_count": 0,
            "fail_count": 0,
            "missing_from_toml": missing_from_toml,
        }
        if as_json:
            _emit_json(console, payload)
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 1

    if not members:
        return _fail(
            f"no git member repos found under {root} — init each repo "
            "with `issue-flow init` or `/iflow-setup`, then "
            "`issue-flow workspace init`. Bootstrap skips non-git folders."
        )

    if default is not None and default not in member_names:
        return _fail(
            f"--default '{default}' is not a git member; "
            f"available members: {', '.join(member_names)}."
        )

    if apply and default is None and len(members) > 1:
        hint = f" {next_command}" if next_command else ""
        return _fail(
            "pass --default <member-folder> when more than one git member "
            f"is present; available members: {', '.join(member_names)}."
            f"{hint}"
        )

    member_results: list[dict[str, Any]] = []
    ok_count = 0
    fail_count = 0
    workspace_written = False

    if apply:
        if not skip_dep_check:
            from issue_flow.init import _dependency_gate

            if not _dependency_gate(skip_dep_check=False):
                return 1

        def _run_member_init(member_root: Path) -> None:
            if as_json:
                quiet = Console(quiet=True)
                saved = console_module.console
                console_module.console = quiet
                try:
                    run_init(
                        member_root,
                        skip_dep_check=True,
                        editors=editors,
                    )
                finally:
                    console_module.console = saved
            else:
                run_init(
                    member_root,
                    skip_dep_check=True,
                    editors=editors,
                )

        for child in members:
            entry: dict[str, Any] = {
                "name": child.name,
                "path": str(child.path),
                "status": child.status,
            }
            if child.status == project.CHILD_SCAFFOLDED:
                entry["ok"] = True
                entry["action"] = "already_scaffolded"
                ok_count += 1
                member_results.append(entry)
                continue
            try:
                _run_member_init(child.path)
                entry["ok"] = True
                entry["action"] = "inited"
                entry["status"] = project.CHILD_SCAFFOLDED
                ok_count += 1
            except typer.Exit as exc:
                entry["ok"] = False
                entry["action"] = "init"
                entry["error"] = f"init failed (exit {exc.exit_code})"
                fail_count += 1
            except Exception as exc:
                entry["ok"] = False
                entry["action"] = "init"
                entry["error"] = str(exc)
                fail_count += 1
            member_results.append(entry)

        if fail_count < len(members):
            init_console = Console(quiet=True) if as_json else console
            init_default = default if default is not None else existing_default
            code = run_workspace_init(
                root,
                init_console,
                init_default,
                force=True,
                as_json=False,
                sync_code_workspace=sync_code_workspace,
                code_workspace_path=code_workspace_path,
                drop_unknown_folders=force,
            )
            workspace_written = code == 0
            if code != 0 and not as_json:
                # run_workspace_init already printed the error.
                pass
            if code != 0 and as_json:
                extra = " (code-workspace sync refused)" if sync_code_workspace else ""
                return _fail(
                    f"member init finished but {project.WORKSPACE_FILENAME} "
                    f"was not written{extra}"
                )
    else:
        for child in members:
            member_results.append(
                {
                    "name": child.name,
                    "path": str(child.path),
                    "status": child.status,
                    "ok": True,
                    "action": "planned",
                }
            )
            ok_count += 1

    resolved_default = default
    if resolved_default is None and len(members) == 1:
        resolved_default = members[0].name

    payload = {
        "applied": apply,
        "ok": fail_count == 0,
        "workspace_root": str(root),
        "workspace_exists": toml_path.is_file(),
        "workspace_written": workspace_written,
        "default": resolved_default,
        "proposed_default": proposed_default,
        "next_command": next_command,
        "children": [_child_payload(c) for c in children],
        "members": member_results,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "missing_from_toml": missing_from_toml,
    }

    if as_json:
        _emit_json(console, payload)
        return 0 if fail_count == 0 else 1

    console.print(f"workspace  {root}")
    for child in children:
        extra = f" ({child.reason})" if child.reason else ""
        console.print(f"  {child.status:14} {child.name}{extra}")
    if not apply:
        console.print(
            "[dim]classify only — pass --yes to init unscaffolded members "
            "and write issueflow-workspace.toml[/dim]"
        )
        if len(members) > 1 and default is None:
            console.print(
                f"[dim]will need --default <member-folder>; "
                f"members: {', '.join(member_names)}[/dim]"
            )
            if next_command:
                console.print(f"[dim]next: {escape(next_command)}[/dim]")
        if missing_from_toml:
            console.print(
                "[yellow]missing from toml[/yellow]  "
                + escape(", ".join(missing_from_toml))
            )
        return 0

    if fail_count == 0:
        console.print(
            f"[bold green]Bootstrapped {ok_count}/{len(members)} member(s).[/bold green]"
        )
    else:
        console.print(
            f"[bold yellow]Bootstrapped {ok_count}/{len(members)} member(s); "
            f"{fail_count} failed.[/bold yellow]"
        )
        for entry in member_results:
            if not entry.get("ok"):
                console.print(
                    f"  [red]fail[/red]  {escape(entry['name'])}: "
                    f"{escape(str(entry.get('error', 'unknown error')))}"
                )
    return 0 if fail_count == 0 else 1


def _prepare_workspace_members(
    start: Path,
    console: Console,
    as_json: bool,
) -> tuple[project.Workspace, list[tuple[str, Path]]] | None:
    """Resolve unique scaffolded members, or emit the shared workspace error."""
    found = project.iter_workspace_members(start)
    if found is None:
        msg = (
            f"no {project.WORKSPACE_FILENAME} found above {start} — run "
            f"`issue-flow workspace init` from the workspace root first."
        )
        _emit_workspace_error(console, as_json, msg)
        return None
    workspace, pairs = found
    if not pairs:
        msg = (
            f"no scaffolded member repos found under {workspace.root} — run "
            "`issue-flow init` inside the member repos first."
        )
        _emit_workspace_error(console, as_json, msg)
        return None
    return workspace, pairs


def _emit_workspace_error(console: Console, as_json: bool, msg: str) -> None:
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
    prepared = _prepare_workspace_members(start, console, as_json)
    if prepared is None:
        return 1
    workspace, member_pairs = prepared
    member_roots = [root for _, root in member_pairs]

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

    for name, root in member_pairs:
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


def _dirty_class(paths: list[str] | None, issueflows_dir: str) -> str:
    """``clean`` / ``issueflows_only`` / ``mixed`` / ``unknown``."""
    if paths is None:
        return "unknown"
    if not paths:
        return "clean"
    if gitutils.issueflows_only_dirty(paths, issueflows_dir):
        return "issueflows_only"
    return "mixed"


def run_workspace_status(
    workspace_dir: Path,
    console: Console,
    local: bool,
    as_json: bool,
) -> int:
    """Aggregate ``run_status`` across workspace members."""
    start = workspace_dir.resolve()
    prepared = _prepare_workspace_members(start, console, as_json)
    if prepared is None:
        return 1
    workspace, member_pairs = prepared
    settings = Settings()
    results: list[dict[str, Any]] = []
    ok_count = 0
    skip_count = 0
    fail_count = 0

    if not as_json:
        console.print(f"\n[bold]Workspace status[/bold]  [cyan]{workspace.root}[/cyan]")
        console.print(f"[dim]{len(member_pairs)} member(s)[/dim]\n")

    for name, root in member_pairs:
        entry: dict[str, Any] = {"name": name, "path": str(root)}
        if settings.resolve_locked(root):
            entry["ok"] = True
            entry["skipped"] = True
            entry["reason"] = "locked"
            skip_count += 1
            results.append(entry)
            if not as_json:
                console.print(f"[yellow]skip[/yellow]  {escape(name)}  (locked)")
            continue
        try:
            payload = _status_payload(root, local)
            entry["ok"] = True
            entry["status"] = payload
            ok_count += 1
            if not as_json:
                console.print(f"[bold]{escape(name)}[/bold]  {root}")
                _render_status_text(console, settings, payload)
                console.print()
        except Exception as exc:  # noqa: BLE001 — continue-on-fail fan-out
            entry["ok"] = False
            entry["error"] = str(exc)
            fail_count += 1
            if not as_json:
                console.print(f"[red]fail[/red]  {escape(name)}: {escape(str(exc))}")
        results.append(entry)

    payload = {
        "ok": fail_count == 0,
        "workspace_root": str(workspace.root),
        "members": results,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
    }
    if as_json:
        _emit_json(console, payload)
    elif fail_count:
        console.print(
            f"[bold yellow]Status {ok_count}/{len(member_pairs)} member(s); "
            f"{fail_count} failed.[/bold yellow]"
        )
    return 0 if fail_count == 0 else 1


def run_workspace_doctor(
    workspace_dir: Path,
    console: Console,
    as_json: bool,
) -> int:
    """Aggregate ``run_audit`` across workspace members. No ``--fix``."""
    start = workspace_dir.resolve()
    prepared = _prepare_workspace_members(start, console, as_json)
    if prepared is None:
        return 1
    workspace, member_pairs = prepared
    settings = Settings()
    results: list[dict[str, Any]] = []
    ok_count = 0
    skip_count = 0
    fail_count = 0

    if not as_json:
        console.print(f"\n[bold]Workspace doctor[/bold]  [cyan]{workspace.root}[/cyan]")
        console.print(f"[dim]{len(member_pairs)} member(s)[/dim]\n")

    for name, root in member_pairs:
        entry: dict[str, Any] = {"name": name, "path": str(root)}
        if settings.resolve_locked(root):
            entry["ok"] = True
            entry["skipped"] = True
            entry["reason"] = "locked"
            skip_count += 1
            results.append(entry)
            if not as_json:
                console.print(f"[yellow]skip[/yellow]  {escape(name)}  (locked)")
            continue
        try:
            audit = _audit_payload(root)
            entry["ok"] = True
            entry["audit"] = audit
            if audit.get("has_error"):
                fail_count += 1
            else:
                ok_count += 1
            if not as_json:
                console.print(f"[bold]{escape(name)}[/bold]  {root}")
                _render_audit_text(console, audit)
                console.print()
        except Exception as exc:  # noqa: BLE001 — continue-on-fail fan-out
            entry["ok"] = False
            entry["error"] = str(exc)
            fail_count += 1
            if not as_json:
                console.print(f"[red]fail[/red]  {escape(name)}: {escape(str(exc))}")
        results.append(entry)

    payload = {
        "ok": fail_count == 0,
        "workspace_root": str(workspace.root),
        "members": results,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
    }
    if as_json:
        _emit_json(console, payload)
    return 0 if fail_count == 0 else 1


def run_workspace_dirty(
    workspace_dir: Path,
    console: Console,
    as_json: bool,
) -> int:
    """Classify each member's working tree (no writes)."""
    start = workspace_dir.resolve()
    prepared = _prepare_workspace_members(start, console, as_json)
    if prepared is None:
        return 1
    workspace, member_pairs = prepared
    settings = Settings()
    results: list[dict[str, Any]] = []
    ok_count = 0
    skip_count = 0
    fail_count = 0

    if not as_json:
        console.print(f"\n[bold]Workspace dirty[/bold]  [cyan]{workspace.root}[/cyan]")
        console.print(f"[dim]{len(member_pairs)} member(s)[/dim]\n")

    for name, root in member_pairs:
        entry: dict[str, Any] = {"name": name, "path": str(root)}
        if settings.resolve_locked(root):
            entry["ok"] = True
            entry["skipped"] = True
            entry["reason"] = "locked"
            skip_count += 1
            results.append(entry)
            if not as_json:
                console.print(f"[yellow]skip[/yellow]  {escape(name)}  (locked)")
            continue
        paths = gitutils.dirty_paths(root)
        klass = _dirty_class(paths, settings.issueflows_dir)
        entry["ok"] = True
        entry["class"] = klass
        entry["dirty_paths"] = paths if paths is not None else []
        entry["issueflows_only"] = klass == "issueflows_only"
        ok_count += 1
        results.append(entry)
        if not as_json:
            console.print(f"  {escape(name)}  {klass}")
            if paths:
                for path in paths:
                    console.print(f"    {escape(path)}")

    payload = {
        "ok": fail_count == 0,
        "workspace_root": str(workspace.root),
        "members": results,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
    }
    if as_json:
        _emit_json(console, payload)
    return 0 if fail_count == 0 else 1


def _git_member_snapshot(root: Path, settings: Settings) -> dict[str, Any]:
    """Local git hygiene fields for one member (no fetch)."""
    dirty = gitutils.dirty_paths(root)
    clean = gitutils.working_tree_clean(root)
    default = gitutils.default_branch(root)
    counts = gitutils.ahead_behind(root, default)
    return {
        "branch": gitutils.current_branch(root),
        "default_branch": default,
        "clean": clean,
        "dirty_paths": dirty if dirty is not None else [],
        "issueflows_only": gitutils.issueflows_only_dirty(
            dirty, settings.issueflows_dir
        ),
        "ahead": counts[0] if counts else None,
        "behind": counts[1] if counts else None,
    }


def _format_ahead_behind(ahead: int | None, behind: int | None) -> str:
    if ahead is None or behind is None:
        return "? ahead / ? behind"
    return f"{ahead} ahead / {behind} behind"


def run_workspace_git_status(
    workspace_dir: Path,
    console: Console,
    as_json: bool,
) -> int:
    """Read-only git snapshot across workspace members (no fetch)."""
    start = workspace_dir.resolve()
    prepared = _prepare_workspace_members(start, console, as_json)
    if prepared is None:
        return 1
    workspace, member_pairs = prepared
    settings = Settings()
    results: list[dict[str, Any]] = []
    ok_count = 0
    skip_count = 0
    fail_count = 0

    if not as_json:
        console.print(f"\n[bold]Workspace git[/bold]  [cyan]{workspace.root}[/cyan]")
        console.print(f"[dim]{len(member_pairs)} member(s)[/dim]\n")

    for name, root in member_pairs:
        entry: dict[str, Any] = {"name": name, "path": str(root)}
        if settings.resolve_locked(root):
            entry["ok"] = True
            entry["skipped"] = True
            entry["reason"] = "locked"
            skip_count += 1
            results.append(entry)
            if not as_json:
                console.print(f"[yellow]skip[/yellow]  {escape(name)}  (locked)")
            continue
        try:
            git_info = _git_member_snapshot(root, settings)
            entry["ok"] = True
            entry.update(git_info)
            ok_count += 1
            if not as_json:
                tree = (
                    "clean"
                    if git_info["clean"]
                    else "dirty"
                    if git_info["clean"] is not None
                    else "unknown"
                )
                branch = git_info["branch"] or "(detached)"
                counts_str = _format_ahead_behind(git_info["ahead"], git_info["behind"])
                console.print(
                    f"  {escape(name)}  {escape(branch)}  {counts_str}  {tree}"
                )
                for path in git_info["dirty_paths"]:
                    console.print(f"    {escape(path)}")
        except Exception as exc:  # noqa: BLE001 — continue-on-fail fan-out
            entry["ok"] = False
            entry["error"] = str(exc)
            fail_count += 1
            if not as_json:
                console.print(f"[red]fail[/red]  {escape(name)}: {escape(str(exc))}")
        results.append(entry)

    payload = {
        "ok": fail_count == 0,
        "workspace_root": str(workspace.root),
        "members": results,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
    }
    if as_json:
        _emit_json(console, payload)
    return 0 if fail_count == 0 else 1


def run_workspace_git_fetch(
    workspace_dir: Path,
    console: Console,
    as_json: bool,
) -> int:
    """``git fetch --prune`` across workspace members. Continue-on-fail."""
    start = workspace_dir.resolve()
    prepared = _prepare_workspace_members(start, console, as_json)
    if prepared is None:
        return 1
    workspace, member_pairs = prepared
    settings = Settings()
    results: list[dict[str, Any]] = []
    ok_count = 0
    skip_count = 0
    fail_count = 0

    if not as_json:
        console.print(
            f"\n[bold]Workspace git fetch[/bold]  [cyan]{workspace.root}[/cyan]"
        )
        console.print(f"[dim]{len(member_pairs)} member(s)[/dim]\n")

    for name, root in member_pairs:
        entry: dict[str, Any] = {"name": name, "path": str(root)}
        if settings.resolve_locked(root):
            entry["ok"] = True
            entry["skipped"] = True
            entry["reason"] = "locked"
            skip_count += 1
            results.append(entry)
            if not as_json:
                console.print(f"[yellow]skip[/yellow]  {escape(name)}  (locked)")
            continue
        fetched = gitutils.fetch_prune(root)
        entry["ok"] = fetched
        entry["fetched"] = fetched
        if fetched:
            ok_count += 1
            if not as_json:
                console.print(f"[green]ok[/green]  {escape(name)}")
        else:
            fail_count += 1
            entry["error"] = "git fetch --prune failed"
            if not as_json:
                console.print(
                    f"[red]fail[/red]  {escape(name)}: git fetch --prune failed"
                )
        results.append(entry)

    payload = {
        "ok": fail_count == 0,
        "workspace_root": str(workspace.root),
        "members": results,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
    }
    if as_json:
        _emit_json(console, payload)
    return 0 if fail_count == 0 else 1


# ---------------------------------------------------------------------------
# agent self-update
# ---------------------------------------------------------------------------


def run_self_update(
    project_root: Path,
    console: Console,
    as_json: bool,
) -> int:
    """Upgrade the uv-tool install, then refresh this project's scaffold."""
    from issue_flow.self_update import run_self_update as _run

    return _run(project_root, console, as_json)


# ---------------------------------------------------------------------------
# agent apply-changelog
# ---------------------------------------------------------------------------


def _status_path_for_issue(
    project_root: Path, settings: Settings, number: int
) -> Path | None:
    """``issue<N>_status.md`` in current-issues, then solved (issue #288)."""
    name = f"issue{number}_status.md"
    base = project_root / settings.issueflows_dir
    for folder in (settings.current_issues_folder, settings.solved_folder):
        path = base / folder / name
        if path.is_file():
            return path
    return None


def run_apply_changelog(
    project_root: Path,
    console: Console,
    issue_number: int,
    as_json: bool,
) -> int:
    """Apply a deferred changelog bullet on the default branch (issue #288).

    Reads ``### Deferred changelog`` from ``issue<N>_status.md`` (current, then
    solved) and writes ``Settings.history_file``. Refuses on an issue branch.
    No-op when the file is missing, the close step chose ``nohistory``, or the
    bullet is already present.
    """
    from datetime import date

    settings = Settings()
    changelog_name = settings.history_file
    notes: list[str] = []
    payload: dict[str, Any] = {
        "ok": False,
        "action": "none",
        "reason": None,
        "issue": issue_number,
        "history_file": changelog_name,
        "status_file": None,
        "bullet": None,
        "planned_version": None,
        "branch": None,
        "default_branch": None,
        "notes": notes,
    }

    def emit(exit_code: int) -> int:
        payload["ok"] = exit_code == 0
        if as_json:
            _emit_json(console, payload)
        else:
            _render_apply_changelog_text(console, payload, exit_code)
        return exit_code

    if not gitutils.git_available():
        notes.append("git is not available.")
        payload["reason"] = "git_unavailable"
        payload["action"] = "refused"
        return emit(1)

    current = gitutils.current_branch(project_root)
    default = gitutils.default_branch(project_root)
    payload["branch"] = current
    payload["default_branch"] = default
    if current is None or current != default:
        notes.append(
            f"apply-changelog runs on the default branch only "
            f"(now on {current or 'detached'}, default {default})."
        )
        payload["reason"] = "not_default_branch"
        payload["action"] = "refused"
        return emit(1)

    status_path = _status_path_for_issue(project_root, settings, issue_number)
    if status_path is None:
        notes.append(
            f"no issue{issue_number}_status.md under "
            f"{settings.current_issues_folder} or {settings.solved_folder}."
        )
        payload["reason"] = "no_status_file"
        payload["action"] = "noop"
        return emit(0)

    payload["status_file"] = str(
        status_path.relative_to(project_root)
        if status_path.is_relative_to(project_root)
        else status_path
    )
    try:
        status_text = status_path.read_text(encoding="utf-8")
    except OSError as exc:
        notes.append(f"could not read status file: {exc}")
        payload["reason"] = "status_unreadable"
        payload["action"] = "refused"
        return emit(1)

    deferred = history.parse_deferred_changelog(status_text)
    if deferred is None:
        notes.append("no ### Deferred changelog section.")
        payload["reason"] = "no_deferred_section"
        payload["action"] = "noop"
        return emit(0)
    if deferred.skipped:
        notes.append("deferred section is nohistory — skip.")
        payload["reason"] = "nohistory"
        payload["action"] = "noop"
        return emit(0)
    if not deferred.bullet:
        notes.append("deferred section has no bullet.")
        payload["reason"] = "no_bullet"
        payload["action"] = "noop"
        return emit(0)

    payload["bullet"] = deferred.bullet
    payload["planned_version"] = deferred.planned_version

    history_path = project_root / changelog_name
    if not history_path.is_file():
        notes.append(f"no {changelog_name} at the project root — skip.")
        payload["reason"] = "missing_history_file"
        payload["action"] = "noop"
        return emit(0)

    try:
        text = history_path.read_text(encoding="utf-8")
    except OSError as exc:
        notes.append(f"could not read {changelog_name}: {exc}")
        payload["reason"] = "history_unreadable"
        payload["action"] = "refused"
        return emit(1)

    if history.changelog_has_bullet(text, deferred.bullet):
        notes.append("bullet already present.")
        payload["reason"] = "already_present"
        payload["action"] = "noop"
        return emit(0)

    try:
        updated = history.append_unreleased_bullet(text, deferred.bullet)
        action = "appended"
        if deferred.planned_version:
            updated = history.promote_unreleased(
                updated, deferred.planned_version, date.today().isoformat()
            )
            action = "promoted"
    except history.MissingUnreleased:
        notes.append(f"{changelog_name} has no ## [Unreleased] heading.")
        payload["reason"] = "no_unreleased_section"
        payload["action"] = "refused"
        return emit(1)

    if updated == text:
        notes.append("no change after apply.")
        payload["reason"] = "unchanged"
        payload["action"] = "noop"
        return emit(0)

    try:
        history_path.write_text(updated, encoding="utf-8")
    except OSError as exc:
        notes.append(f"could not write {changelog_name}: {exc}")
        payload["reason"] = "history_unwritable"
        payload["action"] = "refused"
        return emit(1)

    payload["reason"] = action
    payload["action"] = action
    notes.append(f"wrote {changelog_name} ({action}).")
    return emit(0)


def _render_apply_changelog_text(
    console: Console, payload: dict[str, Any], exit_code: int
) -> None:
    action = payload.get("action") or "none"
    reason = payload.get("reason") or ""
    issue = payload.get("issue")
    if exit_code == 0:
        console.print(
            f"[green]ok[/green]  apply-changelog #{issue} "
            f"[bold]{escape(str(action))}[/bold]"
            + (f" ({escape(str(reason))})" if reason and reason != action else "")
        )
    else:
        console.print(
            f"[red]refused[/red]  apply-changelog #{issue}: "
            f"{escape(str(reason) or action)}"
        )
    for note in payload.get("notes") or []:
        console.print(f"  [dim]{escape(str(note))}[/dim]")


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


# Every editor scaffold materializes this skill, so its presence under an agent
# directory is a reliable "issue-flow is scaffolded here" marker.
_SCAFFOLD_MARKER_SKILL = Path("skills") / "iflow-init" / "SKILL.md"


def audit_editor_scaffolds(
    project_root: Path, settings: Settings
) -> list[tracking.DirtyFinding]:
    """Flag editor config dirs present on disk that lack an issue-flow scaffold.

    Catches the "opened in editor X but only editor Y was scaffolded" gap: e.g.
    a ``.claude/`` directory (Claude Code in use) with no ``.claude/skills/`` or
    ``.claude/commands/`` issue-flow surfaces, so none of the ``/iflow-*``
    commands appear. Each hit is an INFO nudge to run
    ``issue-flow update --editor <id>``.

    Only editors whose agent directory already exists are considered — an absent
    ``.codex/`` is not a problem, just an editor this project does not use. The
    check is skipped entirely when the agent directory is overridden
    (``ISSUEFLOW_AGENT_DIR``), since the per-editor default paths no longer
    describe the on-disk layout.
    """
    if settings.agent_dir_override:
        return []

    findings: list[tracking.DirtyFinding] = []
    for editor_id, profile in EDITORS.items():
        agent_root = project_root / profile.agent_dir
        if not agent_root.is_dir():
            continue  # editor not in use here — nothing to nudge about
        if (agent_root / _SCAFFOLD_MARKER_SKILL).is_file():
            continue  # skills scaffold already materialized
        if (
            profile.commands_dir
            and (agent_root / profile.commands_dir / "iflow-init.md").is_file()
        ):
            continue  # command scaffold present (skills-less layout)
        findings.append(
            tracking.DirtyFinding(
                code="missing_editor_scaffold",
                severity=tracking.SEVERITY_INFO,
                message=(
                    f"{profile.name} config dir {profile.agent_dir!r} is present "
                    "but has no issue-flow scaffold, so its /iflow-* commands "
                    "will not appear."
                ),
                repairable=False,
                suggested_command=f"issue-flow update --editor {editor_id}",
            )
        )
    return findings


def audit_unmanaged_editor_skills(
    project_root: Path, settings: Settings
) -> list[tracking.DirtyFinding]:
    """Report skill directories that issue-flow did not scaffold.

    ``update`` already leaves unknown names alone; this only makes them
    visible. Compare directory names against every packaged ``SKILL_DIRS``
    output name (including optional pstack stems). Report-only: never
    delete, prune, or import.

    Skipped when ``ISSUEFLOW_AGENT_DIR`` overrides the layout — the
    per-editor default skills paths no longer describe the on-disk tree.
    """
    if settings.agent_dir_override:
        return []

    packaged = packaged_skill_output_names()
    findings: list[tracking.DirtyFinding] = []
    for profile in EDITORS.values():
        skills_dir = project_root / profile.agent_dir / "skills"
        if not skills_dir.is_dir():
            continue
        for entry in sorted(skills_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            if entry.name in packaged:
                continue
            rel = entry.relative_to(project_root).as_posix()
            findings.append(
                tracking.DirtyFinding(
                    code="unmanaged_editor_skill",
                    severity=tracking.SEVERITY_INFO,
                    message=(
                        f"Unmanaged skill directory {rel!r} is not an "
                        "issue-flow packaged skill (left alone by update)."
                    ),
                    repairable=False,
                )
            )
    return findings


def _audit_payload(project_root: Path) -> dict[str, Any]:
    """JSON-shaped doctor audit for one project root."""
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
    findings.extend(audit_editor_scaffolds(project_root, settings))
    findings.extend(audit_unmanaged_editor_skills(project_root, settings))
    has_error = any(f.severity == tracking.SEVERITY_ERROR for f in findings)
    return {
        "findings": [_finding_payload(f) for f in findings],
        "has_error": has_error,
        "count": len(findings),
    }


def _render_audit_text(console: Console, payload: dict[str, Any]) -> None:
    findings = payload.get("findings") or []
    if not findings:
        console.print("[green]OK[/green]  No dirty conditions detected.")
        return
    for finding in findings:
        color = {
            tracking.SEVERITY_ERROR: "red",
            tracking.SEVERITY_WARN: "yellow",
            tracking.SEVERITY_INFO: "dim",
        }.get(finding.get("severity", ""), "white")
        console.print(
            f"  [{color}]{finding.get('severity')}[/{color}]  "
            f"{escape(str(finding.get('code', '')))}: "
            f"{escape(str(finding.get('message', '')))}"
        )
        suggested = finding.get("suggested_command")
        if suggested:
            console.print(f"         -> {escape(str(suggested))}")


def run_audit(project_root: Path, console: Console, as_json: bool) -> int:
    """Audit ``.issueflows/`` for dirty conditions."""
    payload = _audit_payload(project_root)
    if as_json:
        _emit_json(console, payload)
        return 1 if payload["has_error"] else 0
    _render_audit_text(console, payload)
    return 1 if payload["has_error"] else 0


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
# agent sub-issue-add
# ---------------------------------------------------------------------------


def run_sub_issue_add(
    project_root: Path,
    console: Console,
    parent: int,
    child: int,
    repo: str | None,
    dry_run: bool,
    as_json: bool,
) -> int:
    """Link ``child`` as a native GitHub sub-issue of ``parent`` (idempotent)."""
    if parent < 1 or child < 1:
        msg = "parent and child must be positive issue numbers."
        if as_json:
            _emit_json(console, {"linked": False, "error": msg})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 2
    if parent == child:
        msg = "parent and child must be different issues."
        if as_json:
            _emit_json(console, {"linked": False, "error": msg})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 2

    if not gitutils.gh_available():
        msg = "gh is not on PATH; cannot link sub-issues. Try `gh auth login`."
        if as_json:
            _emit_json(console, {"linked": False, "error": msg})
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 1

    resolved_repo = repo
    if resolved_repo is None:
        owner_repo = gitutils.remote_owner_repo(project_root)
        if owner_repo is not None:
            resolved_repo = f"{owner_repo[0]}/{owner_repo[1]}"

    existing = gitutils.gh_list_sub_issue_numbers(parent, project_root, resolved_repo)
    if existing is not None and child in existing:
        payload = {
            "parent": parent,
            "child": child,
            "child_id": None,
            "repo": resolved_repo,
            "linked": False,
            "skipped": True,
            "dry_run": dry_run,
            "error": None,
        }
        if as_json:
            _emit_json(console, payload)
        else:
            console.print(
                f"[yellow]skip[/yellow]  #{child} already a sub-issue of #{parent}"
            )
        return 0

    child_id = gitutils.gh_issue_database_id(child, project_root, resolved_repo)
    if child_id is None:
        msg = (
            f"could not resolve database id for #{child}"
            + (f" in {resolved_repo}" if resolved_repo else "")
            + "."
        )
        if as_json:
            _emit_json(
                console,
                {
                    "parent": parent,
                    "child": child,
                    "child_id": None,
                    "repo": resolved_repo,
                    "linked": False,
                    "skipped": False,
                    "error": msg,
                },
            )
        else:
            console.print(f"[red]error[/red]  {msg}")
        return 1

    if dry_run:
        payload = {
            "parent": parent,
            "child": child,
            "child_id": child_id,
            "repo": resolved_repo,
            "linked": False,
            "skipped": False,
            "dry_run": True,
            "error": None,
        }
        if as_json:
            _emit_json(console, payload)
        else:
            console.print(
                f"[dim]dry-run[/dim]  would link #{child} (id {child_id}) "
                f"under #{parent}"
            )
        return 0

    ok, err = gitutils.gh_add_sub_issue(parent, child_id, project_root, resolved_repo)
    payload = {
        "parent": parent,
        "child": child,
        "child_id": child_id,
        "repo": resolved_repo,
        "linked": ok,
        "skipped": False,
        "dry_run": False,
        "error": err,
    }
    if as_json:
        _emit_json(console, payload)
        return 0 if ok else 1
    if ok:
        console.print(f"[green]linked[/green]  #{child} → #{parent}")
        return 0
    console.print(f"[red]error[/red]  {err or 'link failed'}")
    return 1


# ---------------------------------------------------------------------------
# config add / show / set / edit
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
        "  [dim]- [bold]label_flows[/bold] / [bold]yolo_label[/bold] / "
        "[bold]ops_label[/bold] / [bold]publish_label[/bold]: let issue labels "
        "pick the flow (e.g. a 'yolo' label runs /iflow-yolo; 'ops' runs "
        "/iflow-ops no-PR close; 'publish' bumps + releases after merge); "
        "re-run 'issue-flow update' so the commands re-render.[/dim]"
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
        "  [dim]- [bold]remind_cleanup[/bold] / [bold]noob[/bold] / "
        "[bold]cleanup_include_github[/bold] / [bold]cleanup_yes_a1[/bold] / "
        "[bold]cleanup_yes_a2[/bold] / [bold]on_bleeding_edge[/bold] / "
        "[bold]suggest_graphify[/bold] / "
        "[bold]auto_graphify_on_plan[/bold]; "
        "[bold]auto_switchback[/bold] / [bold]auto_remove_worktree[/bold] / "
        "[bold]worktree_first[/bold] / "
        "[bold]auto_close[/bold] / [bold]auto_cleanup[/bold] / "
        "[bold]auto_plan[/bold] / [bold]auto_build[/bold] / "
        "[bold]early_pr[/bold] / [bold]fix_auto_name[/bold]; "
        "[bold]confirm_version_bump[/bold] / [bold]confirm_changelog_update[/bold] / "
        "[bold]defer_changelog[/bold]; "
        "[bold]ruff_autofix[/bold]; [bold]essential_tests[/bold] / "
        "[bold]test_runner[/bold] / [bold]essential_marker[/bold] / "
        "[bold]essential_review[/bold]: skill-behaviour toggles; re-run "
        "'issue-flow update' so skills re-render.[/dim]"
    )
    console.print(
        "  [dim]- [bold]pr_merge_method[/bold]: squash|merge|rebase for yolo "
        "close (default squash); [bold]cycle_max_issues[/bold]: /iflow-cycle "
        "queue cap (default 10); [bold]auto_adversarial_loops[/bold]: "
        "/iflow-auto inter-epoch budget (default 2; trailing loops:<n>).[/dim]"
    )
    console.print(
        "  [dim]- [bold]pstack_skills[/bold]: vendored pstack skills to scaffold "
        "(list of upstream names, e.g. ['unslop', 'tdd'], or \"all\"; default []); "
        "re-run 'issue-flow update' after changing.[/dim]"
    )
    console.print(
        "  [dim]Or use [bold]issue-flow config show|set|edit[/bold]. Other "
        "ISSUEFLOW_* settings are environment-only (set them in .env), not in "
        "config.toml.[/dim]"
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


def run_config_show(
    project_root: Path,
    console: Console,
    key: str | None,
    *,
    persisted_only: bool,
    as_json: bool,
    global_layer: bool = False,
) -> int:
    """Print effective (or persisted-only) ``[issueflow]`` config values."""
    from issue_flow import config_ops
    from issue_flow.user_global import user_global_config_path

    settings = Settings()
    cfg_path = (
        user_global_config_path()
        if global_layer
        else settings.config_path(project_root)
    )
    effective = settings.effective_config(project_root)
    persisted = config_ops.read_persisted_section(cfg_path) or {}

    if key is not None:
        if key not in config_ops.CONFIG_KEYS:
            msg = (
                f"unknown key {key!r}; known keys: "
                f"{', '.join(config_ops.known_config_keys())}"
            )
            if as_json:
                _emit_json(console, {"ok": False, "error": msg, "path": str(cfg_path)})
            else:
                console.print(f"[red]error[/red]  {msg}")
            return 1
        if persisted_only and key not in persisted:
            if as_json:
                _emit_json(
                    console,
                    {
                        "ok": True,
                        "path": str(cfg_path),
                        "key": key,
                        "value": None,
                        "set": False,
                        "persisted": True,
                        "layer": "user-global" if global_layer else "project",
                    },
                )
            else:
                console.print(f"[dim]{key}[/dim]  (not set in {escape(str(cfg_path))})")
            return 0
        if persisted_only:
            value = persisted[key]
        elif global_layer:
            seeded = settings.seed_config_values()
            value = persisted[key] if key in persisted else seeded[key]
        else:
            value = effective[key]
        payload = {
            "ok": True,
            "path": str(cfg_path),
            "key": key,
            "value": value,
            "set": key in persisted,
            "persisted": persisted_only,
            "layer": "user-global" if global_layer else "project",
        }
        if as_json:
            _emit_json(console, payload)
            return 0
        console.print(f"[bold]{key}[/bold] = {value!r}")
        if not persisted_only and key not in persisted:
            layer = "user-global" if global_layer else "config.toml"
            console.print(f"  [dim](default / env; not set in {layer})[/dim]")
        return 0

    if persisted_only:
        values = persisted
    elif global_layer:
        seeded = settings.seed_config_values()
        values = {
            name: persisted[name] if name in persisted else seeded[name]
            for name in seeded
        }
    else:
        values = effective
    payload = {
        "ok": True,
        "path": str(cfg_path),
        "exists": cfg_path.is_file(),
        "persisted": persisted_only,
        "layer": "user-global" if global_layer else "project",
        "values": values,
        "persisted_keys": sorted(persisted),
    }
    if as_json:
        _emit_json(console, payload)
        return 0

    if not cfg_path.is_file():
        console.print(
            f"[yellow]missing[/yellow]  {escape(str(cfg_path))} "
            + (
                "(showing defaults; run 'issue-flow config set --global' to create)"
                if global_layer
                else "(showing defaults; run 'issue-flow config add' to create)"
            )
        )
    else:
        console.print(f"[dim]{escape(str(cfg_path))}[/dim]")
    label = "persisted" if persisted_only else "effective"
    console.print(f"[bold]{label} [issueflow][/bold]")
    if persisted_only and not values:
        console.print("  [dim](empty)[/dim]")
        return 0
    for name in config_ops.known_config_keys():
        if persisted_only and name not in values:
            continue
        val = values.get(name, effective.get(name))
        marker = ""
        if not persisted_only and name not in persisted:
            marker = "  [dim](default)[/dim]"
        console.print(f"  {name} = {val!r}{marker}")
    return 0


def run_config_set(
    project_root: Path,
    console: Console,
    key: str,
    raw_value: str,
    *,
    as_json: bool,
    global_layer: bool = False,
) -> int:
    """Upsert one ``[issueflow]`` key in project or user-global ``config.toml``."""
    from issue_flow import config_ops
    from issue_flow.user_global import upsert_user_global_value, user_global_config_path

    settings = Settings()
    cfg_path = (
        user_global_config_path()
        if global_layer
        else settings.config_path(project_root)
    )
    try:
        value = config_ops.parse_config_value(key, raw_value)
        if global_layer:
            upsert_user_global_value(key, value)
        else:
            config_ops.upsert_config_value(cfg_path, key, value)
    except ValueError as exc:
        if as_json:
            _emit_json(
                console,
                {"ok": False, "error": str(exc), "path": str(cfg_path), "key": key},
            )
        else:
            console.print(f"[red]error[/red]  {exc}")
        return 1

    needs_update = config_ops.CONFIG_KEYS[key].needs_update
    payload = {
        "ok": True,
        "path": str(cfg_path),
        "key": key,
        "value": value,
        "needs_update": needs_update,
        "layer": "user-global" if global_layer else "project",
    }
    if as_json:
        _emit_json(console, payload)
        return 0

    console.print(f"[green]set[/green]  {key} = {value!r}")
    console.print(f"  [dim]{escape(str(cfg_path))}[/dim]")
    if needs_update:
        console.print(
            "  [dim]Re-run [bold]issue-flow update[/bold] so scaffolded "
            "skills/rules pick this up.[/dim]"
        )
    return 0


def run_config_edit(
    project_root: Path,
    console: Console,
    *,
    editor: str | None,
    create: bool,
    as_json: bool,
) -> int:
    """Open ``config.toml`` in ``$VISUAL`` / ``$EDITOR`` (or ``--editor``)."""
    from issue_flow import config_ops

    settings = Settings()
    cfg_path = settings.config_path(project_root)
    created = False
    if not cfg_path.is_file():
        if not create:
            msg = (
                f"{cfg_path} does not exist; pass --create to seed defaults, "
                "or run 'issue-flow config add' first."
            )
            if as_json:
                _emit_json(
                    console,
                    {"ok": False, "error": msg, "path": str(cfg_path), "opened": False},
                )
            else:
                console.print(f"[red]error[/red]  {msg}")
            return 1
        values = settings.seed_config_values()
        modes.write_default_config(cfg_path, overwrite=False, **values)
        created = True

    try:
        editor_argv = config_ops.resolve_text_editor(editor)
    except RuntimeError as exc:
        if as_json:
            _emit_json(
                console,
                {
                    "ok": False,
                    "error": str(exc),
                    "path": str(cfg_path),
                    "opened": False,
                    "created": created,
                },
            )
        else:
            console.print(f"[red]error[/red]  {exc}")
        return 1

    if as_json:
        # JSON mode is for agents/scripts — do not block on an interactive editor.
        _emit_json(
            console,
            {
                "ok": True,
                "path": str(cfg_path),
                "created": created,
                "editor": editor_argv,
                "opened": False,
                "hint": "re-invoke without --json to open the editor",
            },
        )
        return 0

    if created:
        console.print(f"[green]created[/green]  {escape(str(cfg_path))}")
    console.print(
        f"[dim]opening[/dim]  {escape(str(cfg_path))}  "
        f"([bold]{' '.join(editor_argv)}[/bold])"
    )
    code = config_ops.open_in_editor(cfg_path, editor=editor)
    if code != 0:
        console.print(f"[yellow]editor exited {code}[/yellow]")
        return code if code > 0 else 1
    console.print(
        "  [dim]If you changed bake-into-template knobs, re-run "
        "[bold]issue-flow update[/bold].[/dim]"
    )
    return 0


# ---------------------------------------------------------------------------
# status (top-level, human-facing)
# ---------------------------------------------------------------------------


def _status_payload(project_root: Path, local: bool) -> dict[str, Any]:
    """JSON-shaped status overview for one project root."""
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

    return {
        "branch": branch,
        "focus": focus_section,
        "ambiguous_candidates": focus.candidates,
        "parked": parked,
        "solved_count": len(solved_numbers),
        "solved_recent": solved_numbers[-5:],
        "cycle_active": cycle_active,
        "github": github,
    }


def run_status(project_root: Path, console: Console, local: bool, as_json: bool) -> int:
    """Read-only overview: focus stage, parked, solved, optional GitHub cross-ref."""
    payload = _status_payload(project_root, local)
    if as_json:
        _emit_json(console, payload)
        return 0
    _render_status_text(console, Settings(), payload)
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
