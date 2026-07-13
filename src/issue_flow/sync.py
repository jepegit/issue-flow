"""Sync ``.issueflows/`` folder placement to GitHub issue labels (and optionally milestones).

Reads tracked issue groups from the three lifecycle folders via
:mod:`issue_flow.tracking` and pushes one-way updates to GitHub through ``gh``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from rich.console import Console
from rich.table import Table

from issue_flow import gitutils, tracking
from issue_flow.config import Settings, _env_flag
from issue_flow.modes import (
    DEFAULT_SYNC_CLOSE_ON_SOLVED,
    DEFAULT_SYNC_ENABLED,
    DEFAULT_SYNC_LABEL_PREFIX,
    DEFAULT_SYNC_LABELS,
    DEFAULT_SYNC_MILESTONE_MAP,
    DEFAULT_SYNC_MILESTONES,
    read_sync_settings,
)

SyncState = Literal["current", "parked", "solved"]

SYNC_STATES: tuple[SyncState, ...] = ("current", "parked", "solved")

_FOLDER_PRECEDENCE: dict[str, int] = {
    "01-current-issues": 0,
    "02-partly-solved-issues": 1,
    "03-solved-issues": 2,
}


@dataclass(frozen=True)
class SyncSettings:
    """Resolved sync configuration for one project."""

    enabled: bool = True
    label_prefix: str = "status:"
    labels: bool = True
    milestones: bool = False
    milestone_map: dict[str, str] = field(
        default_factory=lambda: {"current": "", "parked": "", "solved": ""}
    )
    close_on_solved: bool = False


@dataclass
class IssueSyncPlan:
    """Planned GitHub mutations for one tracked issue."""

    number: int
    state: SyncState
    folder: str
    desired_label: str | None = None
    labels_to_add: list[str] = field(default_factory=list)
    labels_to_remove: list[str] = field(default_factory=list)
    milestone: str | None = None
    close: bool = False
    skipped: bool = False
    skip_reason: str | None = None


@dataclass
class IssueSyncResult:
    """Outcome of applying (or dry-running) one issue sync."""

    number: int
    state: SyncState
    labels_added: list[str] = field(default_factory=list)
    labels_removed: list[str] = field(default_factory=list)
    milestone: str | None = None
    closed: bool = False
    skipped: bool = False
    error: str | None = None


def load_sync_settings(settings: Settings, project_root: Path) -> SyncSettings:
    """Resolve sync config: ``[issueflow.sync]`` > ``ISSUEFLOW_SYNC_*`` env > defaults."""
    import os

    persisted = read_sync_settings(settings.config_path(project_root)) or {}
    milestone_raw = persisted.get("milestone_map")
    milestone_map = dict(DEFAULT_SYNC_MILESTONE_MAP)
    if isinstance(milestone_raw, dict):
        for key in SYNC_STATES:
            if key in milestone_raw and milestone_raw[key] is not None:
                milestone_map[key] = str(milestone_raw[key])

    def _bool(key: str, env: str, default: bool) -> bool:
        if key in persisted:
            return bool(persisted[key])
        return _env_flag(env, default=default)

    def _str(key: str, env: str, default: str) -> str:
        if key in persisted and persisted[key] is not None:
            return str(persisted[key])
        value = os.getenv(env)
        if value and value.strip():
            return value.strip()
        return default

    return SyncSettings(
        enabled=_bool("enabled", "ISSUEFLOW_SYNC_ENABLED", DEFAULT_SYNC_ENABLED),
        label_prefix=_str(
            "label_prefix", "ISSUEFLOW_SYNC_LABEL_PREFIX", DEFAULT_SYNC_LABEL_PREFIX
        ),
        labels=_bool("labels", "ISSUEFLOW_SYNC_LABELS", DEFAULT_SYNC_LABELS),
        milestones=_bool(
            "milestones", "ISSUEFLOW_SYNC_MILESTONES", DEFAULT_SYNC_MILESTONES
        ),
        milestone_map=milestone_map,
        close_on_solved=_bool(
            "close_on_solved",
            "ISSUEFLOW_SYNC_CLOSE_ON_SOLVED",
            DEFAULT_SYNC_CLOSE_ON_SOLVED,
        ),
    )


def managed_labels(prefix: str) -> set[str]:
    """All managed label names for the given prefix."""
    return {f"{prefix}{state}" for state in SYNC_STATES}


def label_for_state(prefix: str, state: SyncState) -> str:
    return f"{prefix}{state}"


def _folder_state_map(settings: Settings) -> dict[str, SyncState]:
    return {
        settings.current_issues_folder: "current",
        settings.partly_solved_folder: "parked",
        settings.solved_folder: "solved",
    }


def collect_tracked_issues(
    project_root,
    settings: Settings,
) -> tuple[dict[int, SyncState], dict[int, str], list[str]]:
    """Scan lifecycle folders and return issue → state (+ folder), with warnings."""
    folder_states = _folder_state_map(settings)
    found: dict[int, tuple[SyncState, str]] = {}
    warnings: list[str] = []

    for folder_name, state in folder_states.items():
        folder = project_root / settings.issueflows_dir / folder_name
        for number in tracking.group_issue_files(folder):
            if number in found:
                prev_state, prev_folder = found[number]
                if _FOLDER_PRECEDENCE[folder_name] >= _FOLDER_PRECEDENCE[prev_folder]:
                    warnings.append(
                        f"Issue #{number} appears in both {prev_folder} and "
                        f"{folder_name}; keeping {prev_folder} ({prev_state})."
                    )
                    continue
                warnings.append(
                    f"Issue #{number} appears in both {prev_folder} and "
                    f"{folder_name}; preferring {folder_name} ({state})."
                )
            found[number] = (state, folder_name)

    states = {number: state for number, (state, _) in found.items()}
    folders = {number: folder for number, (_, folder) in found.items()}
    return states, folders, warnings


def plan_issue_sync(
    number: int,
    state: SyncState,
    folder: str,
    *,
    config: SyncSettings,
    current_labels: list[str],
    current_milestone: str | None,
    issue_open: bool,
) -> IssueSyncPlan:
    """Build the label/milestone/close plan for one issue."""
    plan = IssueSyncPlan(number=number, state=state, folder=folder)
    managed = managed_labels(config.label_prefix)

    if config.labels:
        desired = label_for_state(config.label_prefix, state)
        plan.desired_label = desired
        plan.labels_to_add = [desired] if desired not in current_labels else []
        plan.labels_to_remove = sorted(
            label for label in current_labels if label in managed and label != desired
        )

    if config.milestones:
        title = (config.milestone_map.get(state) or "").strip()
        if title and title != (current_milestone or ""):
            plan.milestone = title

    if config.close_on_solved and state == "solved" and issue_open:
        plan.close = True

    if (
        not plan.labels_to_add
        and not plan.labels_to_remove
        and not plan.milestone
        and not plan.close
    ):
        plan.skipped = True
        plan.skip_reason = "already in sync"

    return plan


def plan_sync(
    project_root,
    settings: Settings,
    config: SyncSettings,
    *,
    repo: str | None,
) -> tuple[list[IssueSyncPlan], list[str]]:
    """Plan sync for every tracked issue under ``.issueflows/``."""
    states, folders, warnings = collect_tracked_issues(project_root, settings)
    plans: list[IssueSyncPlan] = []

    for number in sorted(states):
        meta = gitutils.gh_issue_meta(number, project_root, repo=repo)
        if meta is None:
            plans.append(
                IssueSyncPlan(
                    number=number,
                    state=states[number],
                    folder=folders[number],
                    skipped=True,
                    skip_reason="could not fetch issue from GitHub",
                )
            )
            continue

        raw_labels = meta.get("labels") or []
        current_labels = [
            str(item.get("name"))
            for item in raw_labels
            if isinstance(item, dict) and item.get("name")
        ]
        issue_state = str(meta.get("state", "")).lower()
        issue_open = issue_state == "open"
        current_milestone: str | None = None
        milestone_obj = meta.get("milestone")
        if isinstance(milestone_obj, dict):
            title = milestone_obj.get("title")
            if title:
                current_milestone = str(title)

        plans.append(
            plan_issue_sync(
                number,
                states[number],
                folders[number],
                config=config,
                current_labels=current_labels,
                current_milestone=current_milestone,
                issue_open=issue_open,
            )
        )

    return plans, warnings


def _milestone_exists(title: str, project_root, repo: str | None) -> bool:
    titles = gitutils.gh_milestone_titles(project_root, repo=repo)
    if titles is None:
        return False
    return title in titles


def apply_plan(
    plan: IssueSyncPlan,
    project_root,
    *,
    repo: str | None,
    config: SyncSettings,
    dry_run: bool,
) -> IssueSyncResult:
    """Apply one planned sync (or record a dry-run result)."""
    result = IssueSyncResult(number=plan.number, state=plan.state)

    if plan.skipped:
        result.skipped = True
        result.error = plan.skip_reason
        return result

    if dry_run:
        result.labels_added = list(plan.labels_to_add)
        result.labels_removed = list(plan.labels_to_remove)
        result.milestone = plan.milestone
        result.closed = plan.close
        return result

    if plan.labels_to_add or plan.labels_to_remove or plan.milestone:
        milestone = plan.milestone
        if milestone and not _milestone_exists(milestone, project_root, repo):
            result.error = f"milestone {milestone!r} does not exist on GitHub"
            return result

        ok, err = gitutils.gh_issue_edit(
            plan.number,
            project_root,
            repo=repo,
            add_labels=plan.labels_to_add or None,
            remove_labels=plan.labels_to_remove or None,
            milestone=milestone,
        )
        if not ok:
            result.error = err or "gh issue edit failed"
            return result
        result.labels_added = list(plan.labels_to_add)
        result.labels_removed = list(plan.labels_to_remove)
        result.milestone = milestone

    if plan.close:
        ok, err = gitutils.gh_issue_close(plan.number, project_root, repo=repo)
        if not ok:
            result.error = err or "gh issue close failed"
            return result
        result.closed = True

    return result


def bootstrap_hint(prefix: str) -> str:
    return "Create managed labels once, then re-run sync:\n" + "\n".join(
        f"  gh label create '{label_for_state(prefix, state)}' --color "
        f"{'0E8A16' if state == 'current' else 'FBCA04' if state == 'parked' else '6E7781'}"
        for state in SYNC_STATES
    )


def run_sync(
    project_root,
    console: Console,
    *,
    apply: bool,
    repo: str | None,
    as_json: bool,
) -> int:
    """Entry point for ``issue-flow sync``."""
    settings = Settings()
    config = load_sync_settings(settings, project_root)

    if not config.enabled:
        payload = {"enabled": False, "results": [], "warnings": []}
        if as_json:
            console.print_json(data=payload)
        else:
            console.print("[dim]Sync disabled in config; nothing to do.[/dim]")
        return 0

    if apply and not gitutils.gh_available():
        console.print("[red]gh is not available[/red]; cannot apply sync.")
        return 1

    owner_repo = repo
    if owner_repo is None:
        remote = gitutils.remote_owner_repo(project_root)
        if remote:
            owner_repo = f"{remote[0]}/{remote[1]}"

    plans, warnings = plan_sync(project_root, settings, config, repo=owner_repo)
    dry_run = not apply
    results: list[IssueSyncResult] = [
        apply_plan(plan, project_root, repo=owner_repo, config=config, dry_run=dry_run)
        for plan in plans
    ]

    label_errors = [
        r for r in results if r.error and "label" in (r.error or "").lower()
    ]
    payload: dict[str, Any] = {
        "dry_run": dry_run,
        "repo": owner_repo,
        "config": {
            "enabled": config.enabled,
            "label_prefix": config.label_prefix,
            "labels": config.labels,
            "milestones": config.milestones,
            "close_on_solved": config.close_on_solved,
        },
        "warnings": warnings,
        "results": [
            {
                "number": r.number,
                "state": r.state,
                "labels_added": r.labels_added,
                "labels_removed": r.labels_removed,
                "milestone": r.milestone,
                "closed": r.closed,
                "skipped": r.skipped,
                "error": r.error,
            }
            for r in results
        ],
    }

    if as_json:
        console.print_json(data=payload)
        return 1 if any(r.error and not r.skipped for r in results) else 0

    if warnings:
        for warning in warnings:
            console.print(f"[yellow]warning[/yellow]  {warning}")

    mode = "dry-run" if dry_run else "applied"
    console.print(
        f"[bold]issue-flow sync[/bold] ({mode}) — {len(results)} tracked issue(s)"
    )

    if not results:
        console.print("[dim]No tracked issues found under .issueflows/.[/dim]")
        return 0

    table = Table(
        "Issue", "State", "Labels +", "Labels −", "Milestone", "Close", "Status"
    )
    for plan, result in zip(plans, results, strict=True):
        status = "ok"
        if result.skipped:
            status = result.error or "skipped"
        elif result.error:
            status = f"[red]{result.error}[/red]"
        table.add_row(
            f"#{result.number}",
            result.state,
            ", ".join(result.labels_added) or "—",
            ", ".join(result.labels_removed) or "—",
            result.milestone or "—",
            "yes" if result.closed else "—",
            status,
        )
    console.print(table)

    if label_errors and apply:
        console.print(
            "\n[yellow]Some labels may be missing on GitHub.[/yellow] "
            + bootstrap_hint(config.label_prefix)
        )

    return 1 if any(r.error and not r.skipped for r in results) else 0
