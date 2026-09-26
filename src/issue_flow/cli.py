"""Command-line interface for issue-flow."""

from __future__ import annotations

from importlib.metadata import version as _package_version
from pathlib import Path

import typer
from rich.console import Console

from issue_flow.editors import EDITORS

app = typer.Typer(
    name="issue-flow",
    add_completion=True,
)

agent_app = typer.Typer(
    name="agent",
    add_completion=False,
    help=(
        "Agent-facing helpers that read the .issueflows/ tree and git/gh so "
        "AI agents get deterministic answers instead of re-deriving lifecycle "
        "state by hand. All are read-only except `sweep`, `archive`, `capture`, "
        "`switchback`, `sync-branch`, `pr-sync`, `apply-changelog`, `self-update`, `repair`, `label-apply`, "
        "`open-workspace --open`, `worktree-add`, and `worktree-remove`. "
        "`branches` (remote), `local-branches` (local), and `default-sync` only classify: "
        "every delete stays in `/iflow-cleanup`; `default-sync` never mutates."
    ),
)

config_app = typer.Typer(
    name="config",
    add_completion=False,
    help="Manage the project's .issueflows/config.toml.",
)

workspace_app = typer.Typer(
    name="workspace",
    add_completion=False,
    help=(
        "Manage the multi-repo workspace registry (issueflow-workspace.toml): "
        "a workspace-root file naming the member repos and the default "
        "('parent') repo that lifecycle commands fall back to."
    ),
)
workspace_git_app = typer.Typer(
    name="git",
    add_completion=False,
    help=(
        "Git hygiene across every scaffolded workspace member: "
        "status (read-only snapshot) or fetch --prune. No pull/push."
    ),
    invoke_without_command=True,
)

_console = Console()

_PROJECT_DIR_ARGUMENT = typer.Argument(
    default=Path("."),
    help="Project root directory (defaults to current directory).",
    exists=True,
    file_okay=False,
    resolve_path=True,
)

# Agent subcommands take -C/--project-dir (same shape as capture/archive/resolve)
# so multi-root skill recipes can pass -C uniformly. Top-level init/update/
# status/doctor keep the positional Argument form above.
_PROJECT_DIR_OPTION = typer.Option(
    Path("."),
    "--project-dir",
    "-C",
    help="Project root directory (defaults to current directory).",
    exists=True,
    file_okay=False,
    resolve_path=True,
)

_EDITOR_HELP = (
    "AI coding tool(s) to scaffold for. Repeatable; accepts "
    f"{', '.join(sorted(EDITORS))}, or 'all'. Defaults to 'cursor'."
)

_MODE_HELP = (
    "Scaffolding mode (which workflow surfaces to install). Built-ins: "
    "'standard' (full workflow), 'novice' (guided setup + linear lifecycle, "
    "and seeds settings that ask before each step), and 'simple' "
    "(markdown-only lifecycle). Projects may define custom modes in "
    ".issueflows/config.toml. The choice is persisted; change it by re-running "
    "init. Defaults to the persisted mode (or 'standard')."
)

_SKILL_LEVEL_HELP = (
    "Scaffolding skill level (controls quality-tooling recommendations). "
    "Options: 'basic' (minimal), 'standard' (default), 'advanced' (opinionated "
    "type checking / linting / pre-commit guidance). The choice is persisted; "
    "change it by re-running init. Defaults to the persisted level (or 'standard')."
)


def _version_callback(value: bool) -> None:
    if value:
        _console.print(f"issue-flow {_package_version('issue-flow')}")
        raise typer.Exit()


@app.callback()
def _callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the issue-flow version and exit.",
    ),
) -> None:
    """Agents should behave. Let them follow the issue flow."""


@app.command()
def init(
    project_dir: Path = typer.Argument(
        default=Path("."),
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files without asking.",
    ),
    skip_dep_check: bool = typer.Option(
        False,
        "--skip-dep-check",
        help=(
            "Skip the external-CLI dependency check (git, gh) and the "
            "confirmation prompt that follows if anything is missing."
        ),
    ),
    editor: list[str] = typer.Option(
        ["cursor"],
        "--editor",
        "-e",
        help=_EDITOR_HELP,
    ),
    mode: str | None = typer.Option(
        None,
        "--mode",
        "-m",
        help=_MODE_HELP,
    ),
    skill_level: str | None = typer.Option(
        None,
        "--skill-level",
        help=_SKILL_LEVEL_HELP,
    ),
    canonical: bool = typer.Option(
        False,
        "--canonical",
        help=(
            "Scaffold the team-committed canonical store under .issueflows/agent/ "
            "instead of per-editor trees. Adds a managed .gitignore block for "
            "local editor directories."
        ),
    ),
) -> None:
    """Scaffold issue-flow directories and editor config files in a project."""
    from issue_flow.init import run_init

    run_init(
        project_root=project_dir,
        force=force,
        skip_dep_check=skip_dep_check,
        editors=editor,
        mode=mode,
        skill_level=skill_level,
        canonical=canonical,
    )


@app.command()
def convert(
    project_dir: Path = typer.Argument(
        default=Path("."),
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    to: str | None = typer.Option(
        None,
        "--to",
        help=(
            "Target layout: an editor id (cursor, claude, opencode, codex) or "
            "'canonical' for the team store under .issueflows/agent/. Defaults "
            "to ISSUEFLOW_EDITOR / config.toml / cursor."
        ),
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing manifest outputs.",
    ),
    prune_other: bool = typer.Option(
        False,
        "--prune-other",
        help="Remove scaffold trees for non-target editors after converting.",
    ),
    gitignore: bool = typer.Option(
        False,
        "--gitignore",
        help="Append a managed .gitignore block for local editor directories.",
    ),
) -> None:
    """Convert between canonical and per-editor issue-flow scaffold layouts."""
    from issue_flow.convert import run_convert

    run_convert(
        project_root=project_dir,
        to=to,
        force=force,
        prune_other=prune_other,
        gitignore=gitignore,
    )


@app.command()
def update(
    project_dir: Path = typer.Argument(
        default=Path("."),
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    skip_dep_check: bool = typer.Option(
        False,
        "--skip-dep-check",
        help=(
            "Skip the external-CLI dependency check (git, gh) and the "
            "confirmation prompt that follows if anything is missing."
        ),
    ),
    editor: list[str] = typer.Option(
        ["cursor"],
        "--editor",
        "-e",
        help=_EDITOR_HELP,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help=(
            "Overwrite a packaged skill directory even when it looks foreign "
            "(symlink, extra files, or hash ≠ last render stamp)."
        ),
    ),
    all_roots: bool = typer.Option(
        False,
        "--all",
        help=(
            "Refresh every unlocked root in the user-global registry "
            "(skips missing and locked repos). No workspace file required."
        ),
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object (with --all)."
    ),
    include_workspace: bool = typer.Option(
        False,
        "--workspace",
        help=(
            "With --all, also union members of the nearest "
            "issueflow-workspace.toml (unique by resolved path). "
            "Without --all this flag is an error."
        ),
    ),
) -> None:
    """Refresh packaged editor commands, rules, and workflow doc from this package."""
    from issue_flow.init import run_update, run_update_all

    if include_workspace and not all_roots:
        _console.print(
            "[red]error[/red]  --workspace requires --all "
            "(union registry + nearest workspace members)."
        )
        raise typer.Exit(code=2)

    if all_roots:
        raise typer.Exit(
            code=run_update_all(
                skip_dep_check=skip_dep_check,
                editors=editor,
                force=force,
                as_json=json_output,
                include_workspace=include_workspace,
                workspace_start=project_dir,
            )
        )

    run_update(
        project_root=project_dir,
        skip_dep_check=skip_dep_check,
        editors=editor,
        force=force,
    )


@app.command()
def sync(
    project_dir: Path = typer.Argument(
        default=Path("."),
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Apply label/milestone changes to GitHub (default is dry-run).",
    ),
    repo: str | None = typer.Option(
        None,
        "--repo",
        help="owner/repo override (else derived from the origin remote).",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Sync ``.issueflows/`` folder state to GitHub labels (and optionally milestones)."""
    from issue_flow.sync import run_sync

    raise typer.Exit(
        code=run_sync(
            project_dir, _console, apply=apply, repo=repo, as_json=json_output
        )
    )


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def graphify(
    ctx: typer.Context,
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help=(
            "Project root directory to scan with graphify. "
            "Defaults to the current directory."
        ),
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
) -> None:
    """Rebuild the graphify knowledge graph for the project.

    With no extra arguments runs ``graphify update <project_dir>``
    (AST-only build, no LLM API key required) so first-time builds
    just work. Pick a different action by passing the subcommand as
    the first argument: ``issue-flow graphify extract`` adds the slower
    semantic LLM pass for richer cross-file relationships (needs an
    API key — ``GEMINI_API_KEY``, ``ANTHROPIC_API_KEY``,
    ``OPENAI_API_KEY``, or ``--backend ollama`` for a local LLM);
    ``issue-flow graphify watch`` runs a live rebuild;
    ``issue-flow graphify cluster-only --no-viz`` re-clusters an existing
    graph. Trailing flags pass through verbatim. Use ``-C <dir>`` to
    scan a project other than the current directory. Requires
    ``graphify`` to be on ``PATH`` (install with
    ``uv tool install graphifyy``).
    """
    from issue_flow.graphify import run_build

    exit_code = run_build(project_dir, ctx.args, _console)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


@app.command()
def status(
    project_dir: Path = _PROJECT_DIR_ARGUMENT,
    local: bool = typer.Option(
        False,
        "--local",
        help="Skip the GitHub query; report only local .issueflows/ state.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit a machine-readable JSON object instead of a text report.",
    ),
) -> None:
    """Read-only overview of every issue: focus stage, parked, solved, GitHub."""
    from issue_flow.agent import run_status

    raise typer.Exit(code=run_status(project_dir, _console, local, json_output))


@app.command()
def doctor(
    project_dir: Path = _PROJECT_DIR_ARGUMENT,
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Apply safe repairs (mkdir missing folders, sweep non-focus groups).",
    ),
    except_number: int | None = typer.Option(
        None,
        "--except",
        "-x",
        help="Issue number to keep in current-issues when repairing.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="With --fix, show planned repairs without touching files.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit a machine-readable JSON object.",
    ),
) -> None:
    """Audit .issueflows/ for dirty conditions; optionally repair safely."""
    from issue_flow.agent import run_audit, run_repair

    if fix:
        raise typer.Exit(
            code=run_repair(project_dir, _console, except_number, dry_run, json_output)
        )
    raise typer.Exit(code=run_audit(project_dir, _console, json_output))


@agent_app.command("audit")
def agent_audit(
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Audit .issueflows/ for dirty conditions (alias for ``issue-flow doctor``)."""
    from issue_flow.agent import run_audit

    raise typer.Exit(code=run_audit(project_dir, _console, json_output))


@agent_app.command("repair")
def agent_repair(
    project_dir: Path = _PROJECT_DIR_OPTION,
    except_number: int | None = typer.Option(
        None,
        "--except",
        "-x",
        help="Issue number to keep in current-issues when repairing.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show planned repairs without touching files."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Apply safe .issueflows/ repairs (alias for ``issue-flow doctor --fix``)."""
    from issue_flow.agent import run_repair

    raise typer.Exit(
        code=run_repair(project_dir, _console, except_number, dry_run, json_output)
    )


@agent_app.command("state")
def agent_state(
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Resolve the focus issue, its lifecycle stage, and the next command."""
    from issue_flow.agent import run_state

    raise typer.Exit(code=run_state(project_dir, _console, json_output))


@agent_app.command("preflight")
def agent_preflight(
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Branch hygiene report: default branch, clean/dirty, ahead/behind, stale."""
    from issue_flow.agent import run_preflight

    raise typer.Exit(code=run_preflight(project_dir, _console, json_output))


@agent_app.command("setup-status")
def agent_setup_status(
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Report whether a project is ready to run the issue-flow workflow.

    The read-only half of ``/iflow-setup``: which of ``uv`` / ``git`` / ``gh``
    are installed, whether this is a git repo with commits and an ``origin``
    remote, whether ``gh`` is signed in, whether a Python project and an
    issue-flow scaffold exist — plus an ordered ``blockers`` list where each
    entry carries the exact fix command and whether an agent may run it.

    Never prompts, never mutates, and exits 0 even when the project is not
    ready: "needs_setup" is the answer, not an error.
    """
    from issue_flow.agent import run_setup_status

    raise typer.Exit(code=run_setup_status(project_dir, _console, json_output))


@agent_app.command("switchback")
def agent_switchback(
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Switch back to the default branch and fast-forward it, when safe.

    The mechanical half of ``/iflow-close``'s post-PR step: refuses (exit 1)
    while the working tree is dirty so no work is ever stranded, otherwise
    runs ``git switch <default>`` and ``git pull --ff-only``. Never deletes
    branches — that stays in ``/iflow-cleanup``.
    """
    from issue_flow.agent import run_switchback

    raise typer.Exit(code=run_switchback(project_dir, _console, json_output))


@agent_app.command("default-sync")
def agent_default_sync(
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Classify unique commits on home default vs origin (no mutate).

    The mechanical half of pick / cleanup / switchback recovery when
    ``git pull --ff-only`` cannot reconcile unpushed home commits with a
    squash on origin. Prints ahead/behind, commit onelines + paths, and a
    recommended ``action``. Never rebases, force-pushes, or pushes default.
    """
    from issue_flow.agent import run_default_sync

    raise typer.Exit(code=run_default_sync(project_dir, _console, json_output))


@agent_app.command("sync-branch")
def agent_sync_branch(
    project_dir: Path = _PROJECT_DIR_OPTION,
    strategy: str = typer.Option(
        "rebase",
        "--strategy",
        help=(
            "How to take on the default branch's new commits: `rebase` "
            "(default, keeps history linear but rewrites the branch) or "
            "`merge` (no force-push needed)."
        ),
    ),
    base: str | None = typer.Option(
        None,
        "--base",
        help=(
            "Stacked-PR parent tip (branch or SHA): rebase `--onto "
            "origin/<default>` from here so a squash-merged parent's commits "
            "are dropped. Without it a landed parent is auto-detected."
        ),
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Sync the current issue branch with `origin/<default>` before merging.

    Replays the branch onto the default branch and auto-resolves the conflict
    shapes that are pure bookkeeping — both sides appending bullets to the
    changelog's `[Unreleased]` section, or bullets / table rows to a design
    guide under `04-designs-and-guides/` or an `issue<N>_status.md` — kept in
    full with the in-flight side last. Any other conflict aborts the
    operation, leaves the branch untouched, and exits 1. A squash-merged
    parent branch this branch was stacked on is detected (or named with
    `--base`) and its commits are not replayed. Never pushes: a rebase
    rewrites the branch, so the `--force-with-lease` push stays in
    `/iflow-close`.
    """
    from issue_flow.agent import run_sync_branch

    raise typer.Exit(
        code=run_sync_branch(project_dir, _console, strategy, json_output, base=base)
    )


@agent_app.command("apply-changelog")
def agent_apply_changelog(
    issue: int = typer.Option(
        ...,
        "--issue",
        "-n",
        help="GitHub issue number whose deferred changelog bullet to apply.",
    ),
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Apply a deferred changelog bullet on the default branch.

    Reads ``### Deferred changelog`` from ``issue<N>_status.md`` (current, then
    solved) and writes the project's HISTORY/CHANGELOG file. Refuses unless
    the checkout is on the default branch. No-op when the file is missing,
    the close step chose ``nohistory``, or the bullet is already present.
    Used by ``/iflow-cleanup`` and yolo post-pull when ``defer_changelog`` is
    on (issue #288).
    """
    from issue_flow.agent import run_apply_changelog

    raise typer.Exit(
        code=run_apply_changelog(project_dir, _console, issue, json_output)
    )


@agent_app.command("self-update")
def agent_self_update(
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Upgrade the uv-tool install to issue-flow@latest, then refresh the scaffold.

    Runs ``uv tool install issue-flow@latest`` then ``issue-flow update`` on
    ``project_dir`` (``--skip-dep-check``). Skips when the current tool
    install is editable or a local path. Used by ``/iflow-cleanup`` when
    ``on_bleeding_edge`` is on (issue #382).
    """
    from issue_flow.agent import run_self_update

    raise typer.Exit(code=run_self_update(project_dir, _console, json_output))


@agent_app.command("pr-sync")
def agent_pr_sync(
    numbers: list[int] = typer.Argument(
        default=None,
        help="Optional PR numbers to refresh (default: open PRs that need sync).",
    ),
    project_dir: Path = _PROJECT_DIR_OPTION,
    all_open: bool = typer.Option(
        False,
        "--all-open",
        help="Include every open PR (not only DIRTY/BEHIND/CONFLICTING).",
    ),
    dirty_only: bool = typer.Option(
        True,
        "--dirty-only/--all-needing",
        help="When no numbers given, only PRs GitHub marks as needing update.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="List candidates only; do not sync or push.",
    ),
    push: bool = typer.Option(
        True,
        "--push/--no-push",
        help="After a successful sync, `git push --force-with-lease` the head.",
    ),
    fail_fast: bool = typer.Option(
        True,
        "--fail-fast/--continue",
        help="Stop on the first sync/push failure (default).",
    ),
    strategy: str = typer.Option(
        "rebase",
        "--strategy",
        help="Passed through to sync-branch: `rebase` (default) or `merge`.",
    ),
    cleanup_worktrees: bool = typer.Option(
        True,
        "--cleanup-worktrees/--keep-worktrees",
        help="Remove ephemeral *-prsync-* worktrees after each PR.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Refresh open PR heads onto origin/<default> (changelog keep-both).

    For each candidate head: worktree → sync-branch → optional
    ``git push --force-with-lease``. Never bare ``--force``. Used by
    ``/iflow-pr-sync`` when a merge left sibling PRs DIRTY (issue #260).
    """
    from issue_flow.agent import run_pr_sync

    raise typer.Exit(
        code=run_pr_sync(
            project_dir,
            _console,
            numbers=list(numbers) if numbers else None,
            all_open=all_open,
            dirty_only=dirty_only,
            dry_run=dry_run,
            push=push,
            fail_fast=fail_fast,
            strategy=strategy,
            cleanup_worktrees=cleanup_worktrees,
            as_json=json_output,
        )
    )


@agent_app.command("pr-ready")
def agent_pr_ready(
    number: int | None = typer.Argument(
        None,
        help="PR number (same namespace as issues). Omit for the current branch.",
    ),
    project_dir: Path = _PROJECT_DIR_OPTION,
    watch: bool = typer.Option(
        False,
        "--watch",
        help="Poll until ready, blocked, or the checks_watch_minutes budget elapses.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
    repo: str | None = typer.Option(
        None,
        "--repo",
        help="owner/repo (default: origin remote).",
    ),
) -> None:
    """Classify whether a PR is allowed to merge. Never merges.

    Exit 0 only when ``state`` is ``ready``. ``--watch`` polls (``~15s``)
    until ready, blocked, or ``checks_watch_minutes`` elapses. Used after
    ``/iflow-close`` when the question is merge-ready; yolo still owns
    ``gh pr merge`` / ``gh pr checks --watch``.
    """
    from issue_flow.agent import run_pr_ready

    raise typer.Exit(
        code=run_pr_ready(
            project_dir,
            _console,
            number,
            watch=watch,
            as_json=json_output,
            repo=repo,
        )
    )


@agent_app.command("branches")
def agent_branches(
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
    no_fetch: bool = typer.Option(
        False,
        "--no-fetch",
        help="Skip `git fetch --prune` before classifying remotes.",
    ),
    commit_limit: int = typer.Option(
        20,
        "--commit-limit",
        help="Max `git log --oneline` lines per unique-work branch.",
    ),
) -> None:
    """Classify origin/* remotes: deletable vs unique work vs skipped.

    Read-only helper for ``/iflow-cleanup include GitHub``. Never deletes
    remote branches — the skill owns confirm + ``git push origin --delete``.
    """
    from issue_flow.agent import run_branches

    raise typer.Exit(
        code=run_branches(
            project_dir,
            _console,
            json_output,
            fetch=not no_fetch,
            commit_limit=commit_limit,
        )
    )


@agent_app.command("local-branches")
def agent_local_branches(
    project_dir: Path = _PROJECT_DIR_OPTION,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
    no_fetch: bool = typer.Option(
        False,
        "--no-fetch",
        help="Skip `git fetch --prune` before classifying local branches.",
    ),
    commit_limit: int = typer.Option(
        20,
        "--commit-limit",
        help="Max `git log --oneline` lines per branch with unique commits.",
    ),
) -> None:
    """Classify local branches: reachable / squash-landed / unique work.

    Read-only helper for ``/iflow-cleanup`` Phase A. ``git branch -d`` only
    accepts branches reachable from the default branch, so in a squash-merging
    repo it refuses every landed branch; this says which ones are provably
    landed (``-D`` is safe behind the skill's own confirm), which have a merged
    PR but a divergent tip, and which still hold unique work. Never deletes a
    branch — the skill owns confirm + ``git branch -d/-D``.
    """
    from issue_flow.agent import run_local_branches

    raise typer.Exit(
        code=run_local_branches(
            project_dir,
            _console,
            json_output,
            fetch=not no_fetch,
            commit_limit=commit_limit,
        )
    )


@agent_app.command("version-plan")
def agent_version_plan(
    project_dir: Path = _PROJECT_DIR_OPTION,
    bump: list[str] = typer.Option(
        [],
        "--bump",
        "-b",
        help=(
            "Bump level(s): major, minor, patch, stable, alpha, beta, rc, "
            "post, dev. Repeatable; combined levels apply in canonical order "
            "(minor + alpha -> 0.5.0a1). Omitted -> the pre-release-aware "
            "default based on the current version."
        ),
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Plan the next version deterministically (read-only).

    Detects the release strategy from ``pyproject.toml`` (static
    ``[project] version`` -> uv; ``dynamic = ["version"]`` with a tag-driven
    backend -> git tag), reads the current version (static field or latest
    tag), applies the PEP 440 bump arithmetic, and prints the exact commands.
    Never edits files, never creates tags — the doing stays with the agent
    and the user, per the iflow-version-bump skill.
    """
    from issue_flow.agent import run_version_plan

    raise typer.Exit(
        code=run_version_plan(project_dir, _console, list(bump), json_output)
    )


@agent_app.command("publish-intent")
def agent_publish_intent(
    project_dir: Path = _PROJECT_DIR_OPTION,
    issue: int | None = typer.Option(
        None,
        "--issue",
        "-i",
        help="GitHub issue number whose labels to inspect.",
    ),
    label: list[str] = typer.Option(
        [],
        "--label",
        "-l",
        help="Explicit label name (repeatable). Ignored when --issue is set.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Resolve publish-on-success intent from labels (read-only).

    Bare ``publish`` (or the configured ``publish_label``) means patch.
    ``publish:minor`` / ``publish:0.6.0`` override. Exit 2 when the intent
    conflicts or an explicit version is not a sensible next release — the
    agent must stop and ask. Never bumps or creates releases.
    """
    from issue_flow.agent import run_publish_intent

    raise typer.Exit(
        code=run_publish_intent(
            project_dir,
            _console,
            issue=issue,
            labels=list(label),
            as_json=json_output,
        )
    )


@agent_app.command("epic-status")
def agent_epic_status(
    number: int = typer.Argument(..., help="Epic anchor issue number."),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    local: bool = typer.Option(
        False,
        "--local",
        help="Skip the GitHub state lookups; report only the local plan file.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Deterministic epic progress (read-only).

    Parses ``.issueflows/05-epics/epic<N>_plan.md`` (the structure written by
    the /iflow-epic skill) and cross-references published issue states via
    ``gh``: stages with per-issue state and blockers, the current stage, and
    the next open, unblocked candidates. Exit 1 when no plan file exists.
    """
    from issue_flow.agent import run_epic_status

    raise typer.Exit(
        code=run_epic_status(project_dir, _console, number, local, json_output)
    )


@agent_app.command("queue")
def agent_queue(
    numbers: list[int] = typer.Argument(
        None,
        help="Explicit issue numbers to queue (alternative to --label/--epic).",
    ),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    label: str | None = typer.Option(
        None, "--label", help="Queue every open issue carrying this label."
    ),
    epic: int | None = typer.Option(
        None,
        "--epic",
        help="Queue the current stage of this epic's plan file.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Plan a hands-off execution queue (read-only).

    Exactly one source — explicit numbers, ``--label``, or ``--epic`` — is
    resolved, ``Depends on #N`` / ``Blocked by #N`` lines are parsed, and the
    result is a deterministic topological order plus ``blocked`` (open
    dependencies outside the queue), ``skipped_closed``, and ``independent``
    (parallel-safe) sets. A dependency cycle aborts with exit 1, naming the
    members; nothing is ever executed by this command.
    """
    from issue_flow.agent import run_queue

    raise typer.Exit(
        code=run_queue(
            project_dir, _console, list(numbers or []), label, epic, json_output
        )
    )


@agent_app.command("label-candidates")
def agent_label_candidates(
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    kind: str = typer.Option(
        "yolo",
        "--kind",
        help="Review kind (v1: yolo). Selects which configured label to check.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """List open issues for a review kind (read-only; no fitness judgment).

    For ``--kind yolo``, uses the project's resolved ``yolo_label``. Every open
    issue is returned with ``has_label`` true/false. Agents still decide
    yolo-fitness in ``/iflow-review``; this command only lists candidates.
    """
    from issue_flow.agent import run_label_candidates

    raise typer.Exit(
        code=run_label_candidates(project_dir, _console, kind, json_output)
    )


@agent_app.command("label-apply")
def agent_label_apply(
    numbers: list[int] = typer.Argument(
        ...,
        help="Issue numbers to label.",
    ),
    label: str = typer.Option(
        ...,
        "--label",
        help="Label name to add (idempotent).",
    ),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be applied without calling gh."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Apply one label to many issues (no judgment; writes via gh unless dry-run)."""
    from issue_flow.agent import run_label_apply

    raise typer.Exit(
        code=run_label_apply(
            project_dir, _console, list(numbers), label, dry_run, json_output
        )
    )


@agent_app.command("resolve")
def agent_resolve(
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Directory to start the scaffold walk from (defaults to cwd).",
        exists=True,
        file_okay=True,
        resolve_path=True,
    ),
    from_file: Path | None = typer.Option(
        None,
        "--from-file",
        help="Start the walk from this file's directory (e.g. the active editor file).",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Resolve project root, owner/repo, branch, and sibling scaffolds."""
    from issue_flow.agent import run_resolve

    raise typer.Exit(code=run_resolve(project_dir, _console, from_file, json_output))


@agent_app.command("open-workspace")
def agent_open_workspace(
    target: str | None = typer.Argument(
        None,
        help=(
            "Directory path or workspace member name to address as its own "
            "editor window. Defaults to the project root from -C."
        ),
    ),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Start directory for workspace-member lookup (defaults to cwd).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    do_open: bool = typer.Option(
        False,
        "--open",
        help=(
            "Launch the editor binary on the resolved path (non-blocking). "
            "Default is print-only; skills must confirm before passing --open."
        ),
    ),
    editor: str | None = typer.Option(
        None,
        "--editor",
        help="Editor id for binary lookup (default: ISSUEFLOW_EDITOR / cursor).",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Print (optionally open) a path as a separate editor workspace."""
    from issue_flow.agent import run_open_workspace

    raise typer.Exit(
        code=run_open_workspace(
            project_dir, _console, target, do_open, json_output, editor_id=editor
        )
    )


@agent_app.command("worktree-add")
def agent_worktree_add(
    number: int = typer.Argument(..., help="Issue number (branch prefix)."),
    slug: str = typer.Option(
        ...,
        "--slug",
        help="Kebab-case slug; branch becomes <N>-<slug>.",
    ),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Home checkout (must stay on default). Defaults to cwd.",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Add ../<repo>-<N> on <N>-<slug> without switching the home checkout."""
    from issue_flow.agent import run_worktree_add

    raise typer.Exit(
        code=run_worktree_add(project_dir, _console, number, slug, json_output)
    )


@agent_app.command("worktree-list")
def agent_worktree_list(
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Any worktree of the repo. Defaults to cwd.",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """List git worktrees (home + linked)."""
    from issue_flow.agent import run_worktree_list

    raise typer.Exit(code=run_worktree_list(project_dir, _console, json_output))


@agent_app.command("worktree-remove")
def agent_worktree_remove(
    target: str = typer.Argument(
        ...,
        help="Worktree path or issue number.",
    ),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Home checkout used to run git worktree remove.",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Pass --force to git worktree remove (still refuse unique work in skills).",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Remove a linked worktree. Refuses a dirty tree unless --force."""
    from issue_flow.agent import run_worktree_remove

    raise typer.Exit(
        code=run_worktree_remove(
            project_dir, _console, target, json_output, force=force
        )
    )


@agent_app.command("sweep")
def agent_sweep(
    project_dir: Path = _PROJECT_DIR_OPTION,
    except_number: int | None = typer.Option(
        None,
        "--except",
        "-x",
        help="Issue number to keep in current-issues (the focus issue).",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show planned moves without touching files."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Archive non-focus issue groups to partly-/solved- folders by Done status."""
    from issue_flow.agent import run_sweep

    raise typer.Exit(
        code=run_sweep(project_dir, _console, except_number, dry_run, json_output)
    )


@agent_app.command("archive")
def agent_archive(
    issues: list[int] = typer.Argument(
        ...,
        help="Solved issue number(s) whose files should be removed.",
    ),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show planned removals without touching files."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Remove solved issue<N>_* files (the mechanical half of /iflow-archive).

    Reports the pre-archive HEAD sha so the agent-written summary file can
    record a recovery point (``git show <sha>:<path>``). Summarising the
    issues into the dated archive file is left to the agent. Refuses when a
    requested issue has no files in the solved folder.
    """
    from issue_flow.agent import run_archive

    raise typer.Exit(
        code=run_archive(project_dir, _console, issues, dry_run, json_output)
    )


@agent_app.command("sub-issue-add")
def agent_sub_issue_add(
    parent: int = typer.Argument(..., help="Parent issue number."),
    child: int = typer.Argument(..., help="Child issue number to link."),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    repo: str | None = typer.Option(
        None,
        "--repo",
        help="owner/repo override (else derived from the origin remote).",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Resolve ids and skip the POST."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Link a child issue as a native GitHub sub-issue (idempotent)."""
    from issue_flow.agent import run_sub_issue_add

    raise typer.Exit(
        code=run_sub_issue_add(
            project_dir, _console, parent, child, repo, dry_run, json_output
        )
    )


@agent_app.command("capture")
def agent_capture(
    number: int = typer.Argument(..., help="GitHub issue number to capture."),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    repo: str | None = typer.Option(
        None,
        "--repo",
        help="owner/repo override (else derived from the origin remote).",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite an existing issue<N>_original.md."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Fetch a GitHub issue and write issue<N>_original.md (body only)."""
    from issue_flow.agent import run_capture

    raise typer.Exit(
        code=run_capture(project_dir, _console, number, repo, force, json_output)
    )


@config_app.command("add")
def config_add(
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Regenerate the [issueflow] keys even if config.toml already exists.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Create .issueflows/config.toml, seeded from .env (or issue-flow defaults).

    Writes the ``[issueflow]`` keys issue-flow reads from ``config.toml`` —
    ``mode``, ``skill_level``, ``caveman_default``, ``grill_me_default``,
    ``label_flows``, ``yolo_label``, ``ops_label``, ``publish_label``,
    ``checks_watch_minutes``,
    ``step_directives``, ``model_label_flows``, ``deep_model_label``,
    ``fast_model_label``, ``linguist_attributes``, ``remind_cleanup``,
    ``noob``,
    ``cleanup_include_github``, ``on_bleeding_edge``, ``suggest_graphify``,
    ``auto_graphify_on_plan``, ``auto_switchback``, ``auto_remove_worktree``,
    ``worktree_first``,
    ``pr_merge_method``, ``cycle_max_issues``, ``cycle_onfail``,
    ``cycle_nonyolo``, ``auto_adversarial_loops``,
    ``confirm_version_bump``,
    ``ruff_autofix``, ``auto_close``, ``auto_plan``, ``auto_build``,
    ``early_pr``, ``fix_auto_name``, ``confirm_changelog_update``,
    ``defer_changelog``,
    ``essential_tests``, ``test_runner``, ``essential_marker``,
    ``essential_review``, ``pstack_skills``
    — taking each from its ``ISSUEFLOW_*`` env var when set, else the default.
    Other ``ISSUEFLOW_*`` settings are environment-only and are not written
    here. Existing files are left untouched unless ``--force`` is passed.
    """
    from issue_flow.agent import run_config_add

    raise typer.Exit(code=run_config_add(project_dir, _console, force, json_output))


@config_app.command("show")
def config_show(
    key: str | None = typer.Argument(
        None,
        help="Optional single key to print (default: all effective keys).",
    ),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    persisted: bool = typer.Option(
        False,
        "--persisted",
        help="Show only keys written in config.toml (no defaults).",
    ),
    global_layer: bool = typer.Option(
        False,
        "--global",
        help="Read the user-global config.toml (XDG / %APPDATA%).",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Show effective (or persisted) [issueflow] config values."""
    from issue_flow.agent import run_config_show

    raise typer.Exit(
        code=run_config_show(
            project_dir,
            _console,
            key,
            persisted_only=persisted,
            as_json=json_output,
            global_layer=global_layer,
        )
    )


@config_app.command("set")
def config_set(
    key: str = typer.Argument(help="Config key under [issueflow]."),
    value: str = typer.Argument(help="New value (bool/int/str/list as text)."),
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    global_layer: bool = typer.Option(
        False,
        "--global",
        help="Write the user-global config.toml (XDG / %APPDATA%).",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Set one [issueflow] key in config.toml (creates the file if missing)."""
    from issue_flow.agent import run_config_set

    raise typer.Exit(
        code=run_config_set(
            project_dir,
            _console,
            key,
            value,
            as_json=json_output,
            global_layer=global_layer,
        )
    )


@config_app.command("edit")
def config_edit(
    project_dir: Path = typer.Option(
        Path("."),
        "--project-dir",
        "-C",
        help="Project root directory (defaults to current directory).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    editor: str | None = typer.Option(
        None,
        "--editor",
        "-e",
        help="Text editor command (default: $VISUAL, then $EDITOR, then nano/vi).",
    ),
    create: bool = typer.Option(
        False,
        "--create",
        help="Seed a default config.toml when the file is missing.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit path/editor info without opening an interactive editor.",
    ),
) -> None:
    """Open config.toml in your text editor ($VISUAL / $EDITOR)."""
    from issue_flow.agent import run_config_edit

    raise typer.Exit(
        code=run_config_edit(
            project_dir,
            _console,
            editor=editor,
            create=create,
            as_json=json_output,
        )
    )


@workspace_app.command("init")
def workspace_init(
    workspace_dir: Path = typer.Argument(
        default=Path("."),
        help=(
            "Workspace root directory — the folder that contains the member "
            "repos (defaults to current directory)."
        ),
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    default: str | None = typer.Option(
        None,
        "--default",
        help=(
            "Member folder name that lifecycle commands default to (the "
            "'parent repo'). Must be a scaffolded member. When omitted and "
            "exactly one member exists, that member becomes the default."
        ),
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help=(
            "Overwrite an existing registry file. With --code-workspace, "
            "also drop extra relative folders that are not members."
        ),
    ),
    sync_code_workspace: bool = typer.Option(
        False,
        "--code-workspace",
        help=(
            "Also sync a VS Code/Cursor *.code-workspace folder list to "
            "the toml members. Off by default."
        ),
    ),
    code_workspace_path: str | None = typer.Option(
        None,
        "--code-workspace-path",
        help="Explicit *.code-workspace path (required if more than one exists).",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Create issueflow-workspace.toml listing the scaffolded member repos.

    The registry only ever fills the bottom of the resolution order: explicit
    ``root:``/``repo:`` hints and the nearest scaffold always win; the
    ``default`` member is used when a command runs from outside any scaffold
    (typically the workspace root), replacing the "stop and ask" step.
    """
    from issue_flow.agent import run_workspace_init

    raise typer.Exit(
        code=run_workspace_init(
            workspace_dir,
            _console,
            default,
            force,
            json_output,
            sync_code_workspace=sync_code_workspace or code_workspace_path is not None,
            code_workspace_path=code_workspace_path,
            drop_unknown_folders=force,
        )
    )


@workspace_app.command("bootstrap")
def workspace_bootstrap(
    workspace_dir: Path = typer.Argument(
        default=Path("."),
        help=(
            "Workspace root directory — the folder that contains the member "
            "repos (defaults to current directory)."
        ),
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    default: str | None = typer.Option(
        None,
        "--default",
        help=(
            "Member folder name (not a bare flag) that lifecycle commands "
            "default to. Required with --yes when more than one git member "
            "is present."
        ),
    ),
    apply: bool = typer.Option(
        False,
        "--yes",
        help=(
            "Init unscaffolded git members and write (or refresh) "
            "issueflow-workspace.toml members from the current classify. "
            "Without this flag the command only classifies children."
        ),
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help=(
            "With --code-workspace, drop extra relative folders that are "
            "not members. (Toml members are always refreshed on --yes.)"
        ),
    ),
    skip_dep_check: bool = typer.Option(
        False,
        "--skip-dep-check",
        help=(
            "Skip the external-CLI dependency check (git, gh) and the "
            "confirmation prompt that follows if anything is missing."
        ),
    ),
    editor: list[str] = typer.Option(
        ["cursor"],
        "--editor",
        "-e",
        help=_EDITOR_HELP,
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
    sync_code_workspace: bool = typer.Option(
        False,
        "--code-workspace",
        help=(
            "With --yes, also sync a VS Code/Cursor *.code-workspace folder "
            "list. Off by default."
        ),
    ),
    code_workspace_path: str | None = typer.Option(
        None,
        "--code-workspace-path",
        help="Explicit *.code-workspace path (required if more than one exists).",
    ),
) -> None:
    """Init git sibling repos and create the workspace registry.

    Classifies immediate child directories that are their own git top-level
    (skips non-git folders and nested work trees). Without ``--yes`` this is
    classify-only. With ``--yes`` it runs ``issue-flow init`` on unscaffolded
    members, then ``workspace init``. Does not write ``.issueflows/`` on the
    parent and does not ``git init`` children.
    """
    from issue_flow.agent import run_workspace_bootstrap

    raise typer.Exit(
        code=run_workspace_bootstrap(
            workspace_dir,
            _console,
            default,
            apply,
            force,
            skip_dep_check,
            editor,
            json_output,
            sync_code_workspace=sync_code_workspace or code_workspace_path is not None,
            code_workspace_path=code_workspace_path,
        )
    )


@workspace_app.command("update")
def workspace_update(
    workspace_dir: Path = typer.Argument(
        default=Path("."),
        help=(
            "Workspace root directory — the folder that contains the member "
            "repos (defaults to current directory)."
        ),
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    skip_dep_check: bool = typer.Option(
        False,
        "--skip-dep-check",
        help=(
            "Skip the external-CLI dependency check (git, gh) and the "
            "confirmation prompt that follows if anything is missing."
        ),
    ),
    editor: list[str] = typer.Option(
        ["cursor"],
        "--editor",
        "-e",
        help=_EDITOR_HELP,
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Refresh packaged scaffolds in every scaffolded workspace member.

    Walks up from ``workspace_dir`` for ``issueflow-workspace.toml``, then
    runs ``issue-flow update`` in each member repo that carries a
    ``.issueflows/`` tree. Per-member ``mode`` and ``skill_level`` come from
    each repo's own ``config.toml``.
    """
    from issue_flow.agent import run_workspace_update

    raise typer.Exit(
        code=run_workspace_update(
            workspace_dir, _console, skip_dep_check, editor, json_output
        )
    )


_WORKSPACE_DIR_ARGUMENT = typer.Argument(
    default=Path("."),
    help=(
        "Workspace root directory — the folder that contains the member "
        "repos (defaults to current directory). Walks up for "
        "issueflow-workspace.toml."
    ),
    exists=True,
    file_okay=False,
    resolve_path=True,
)


@workspace_app.command("status")
def workspace_status(
    workspace_dir: Path = _WORKSPACE_DIR_ARGUMENT,
    local: bool = typer.Option(
        False,
        "--local",
        help="Skip the GitHub query in each member; report only local state.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Read-only status overview for every scaffolded workspace member."""
    from issue_flow.agent import run_workspace_status

    raise typer.Exit(
        code=run_workspace_status(workspace_dir, _console, local, json_output)
    )


@workspace_app.command("doctor")
def workspace_doctor(
    workspace_dir: Path = _WORKSPACE_DIR_ARGUMENT,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Audit ``.issueflows/`` in every scaffolded workspace member.

    Audit only — there is no ``--fix``. Repair one member at a time with
    ``issue-flow doctor --fix -C <member>``.
    """
    from issue_flow.agent import run_workspace_doctor

    raise typer.Exit(code=run_workspace_doctor(workspace_dir, _console, json_output))


@workspace_app.command("dirty")
def workspace_dirty(
    workspace_dir: Path = _WORKSPACE_DIR_ARGUMENT,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Classify each member's working tree after a workspace update.

    Reports ``clean``, ``issueflows_only``, ``mixed``, or ``unknown``.
    Does not commit or push.
    """
    from issue_flow.agent import run_workspace_dirty

    raise typer.Exit(code=run_workspace_dirty(workspace_dir, _console, json_output))


@workspace_git_app.callback(invoke_without_command=True)
def workspace_git_default(ctx: typer.Context) -> None:
    """Default verb is ``status`` when no subcommand is given."""
    if ctx.invoked_subcommand is not None:
        return
    from issue_flow.agent import run_workspace_git_status

    raise typer.Exit(code=run_workspace_git_status(Path("."), _console, False))


@workspace_git_app.command("status")
def workspace_git_status(
    workspace_dir: Path = _WORKSPACE_DIR_ARGUMENT,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Read-only git snapshot for every scaffolded workspace member.

    Branch, dirty paths, and ahead/behind vs ``origin/<default>``. Does not
    fetch. Distinct from ``workspace status`` (issue-flow lifecycle).
    """
    from issue_flow.agent import run_workspace_git_status

    raise typer.Exit(
        code=run_workspace_git_status(workspace_dir, _console, json_output)
    )


@workspace_git_app.command("fetch")
def workspace_git_fetch(
    workspace_dir: Path = _WORKSPACE_DIR_ARGUMENT,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Run ``git fetch --prune`` in every scaffolded workspace member.

    Continue-on-fail. Does not pull, rebase, merge, or push.
    """
    from issue_flow.agent import run_workspace_git_fetch

    raise typer.Exit(code=run_workspace_git_fetch(workspace_dir, _console, json_output))


@app.command()
def register(
    project_dir: Path = typer.Argument(
        default=Path("."),
        help=(
            "Project root to add, or the walk start when ``--discover`` "
            "is set (defaults to current directory)."
        ),
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
    discover: bool = typer.Option(
        False,
        "--discover",
        help=(
            "Walk PROJECT_DIR for existing issue-flow scaffolds and offer "
            "to register them. Never runs from update --all / init / "
            "workspace update."
        ),
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="With --discover, register candidates without a confirm prompt.",
    ),
    max_depth: int = typer.Option(
        4,
        "--max-depth",
        help="With --discover, maximum directory depth below PROJECT_DIR.",
    ),
) -> None:
    """Add a project root to the user-global registry for ``update --all``."""
    from issue_flow.config import Settings
    from issue_flow.project import discover_issueflow_roots
    from issue_flow.user_global import register_root, user_global_registry_path

    if discover:
        if max_depth < 0:
            _console.print("[red]error[/red]  --max-depth must be >= 0")
            raise typer.Exit(code=2)
        settings = Settings()
        candidates = discover_issueflow_roots(
            project_dir,
            issueflows_dir=settings.issueflows_dir,
            max_depth=max_depth,
        )
        if not yes:
            _console.print(
                f"[bold]{len(candidates)} scaffold(s) under {project_dir}[/bold]"
            )
            for root in candidates:
                _console.print(f"  {root}")
            if not candidates:
                payload = {
                    "ok": True,
                    "discover": True,
                    "candidates": [],
                    "added": [],
                    "already": [],
                    "registry": str(user_global_registry_path()),
                }
                if json_output:
                    _console.print_json(data=payload)
                else:
                    _console.print("[dim]nothing to register[/dim]")
                return
            if not typer.confirm("Register these roots?", default=False):
                raise typer.Exit(code=1)
        added_paths: list[str] = []
        already_paths: list[str] = []
        for root in candidates:
            if register_root(root):
                added_paths.append(str(root))
            else:
                already_paths.append(str(root))
        payload = {
            "ok": True,
            "discover": True,
            "candidates": [str(root) for root in candidates],
            "added": added_paths,
            "already": already_paths,
            "registry": str(user_global_registry_path()),
        }
        if json_output:
            _console.print_json(data=payload)
            return
        for path in added_paths:
            _console.print(f"[green]registered[/green]  {path}")
        for path in already_paths:
            _console.print(f"[dim]already registered[/dim]  {path}")
        if not candidates:
            _console.print("[dim]nothing to register[/dim]")
        return

    added = register_root(project_dir)
    payload = {
        "ok": True,
        "added": added,
        "path": str(project_dir),
        "registry": str(user_global_registry_path()),
    }
    if json_output:
        _console.print_json(data=payload)
    elif added:
        _console.print(f"[green]registered[/green]  {project_dir}")
    else:
        _console.print(f"[dim]already registered[/dim]  {project_dir}")


@app.command()
def unregister(
    project_dir: Path = typer.Argument(
        default=Path("."),
        help="Project root to remove from the user-global registry.",
        exists=False,
        file_okay=False,
        resolve_path=True,
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Remove a project root from the user-global registry."""
    from issue_flow.user_global import unregister_root, user_global_registry_path

    removed = unregister_root(project_dir)
    payload = {
        "ok": True,
        "removed": removed,
        "path": str(project_dir),
        "registry": str(user_global_registry_path()),
    }
    if json_output:
        _console.print_json(data=payload)
    elif removed:
        _console.print(f"[green]unregistered[/green]  {project_dir}")
    else:
        _console.print(f"[dim]not in registry[/dim]  {project_dir}")


app.add_typer(agent_app)
app.add_typer(config_app)
workspace_app.add_typer(workspace_git_app)
app.add_typer(workspace_app)


def main() -> None:
    """Entry point for the `issue-flow` console script."""
    app()
