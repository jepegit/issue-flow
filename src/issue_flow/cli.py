"""Command-line interface for issue-flow."""

from __future__ import annotations

from importlib.metadata import version as _package_version
from pathlib import Path

import typer
from rich.console import Console

from issue_flow.editors import EDITORS

app = typer.Typer(
    name="issue-flow",
    add_completion=False,
)

agent_app = typer.Typer(
    name="agent",
    add_completion=False,
    help=(
        "Agent-facing helpers that read the .issueflows/ tree and git/gh so "
        "AI agents get deterministic answers instead of re-deriving lifecycle "
        "state by hand. All are read-only except `sweep`, `archive`, `capture`, "
        "and `switchback`."
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

_console = Console()

_PROJECT_DIR_ARGUMENT = typer.Argument(
    default=Path("."),
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
    "'standard' (full workflow) and 'simple' (markdown-only lifecycle). "
    "Projects may define custom modes in .issueflows/config.toml. The choice is "
    "persisted; change it by re-running init. Defaults to the persisted mode "
    "(or 'standard')."
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
) -> None:
    """Refresh packaged editor commands, rules, and workflow doc from this package."""
    from issue_flow.init import run_update

    run_update(project_root=project_dir, skip_dep_check=skip_dep_check, editors=editor)


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


@agent_app.command("state")
def agent_state(
    project_dir: Path = _PROJECT_DIR_ARGUMENT,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Resolve the focus issue, its lifecycle stage, and the next command."""
    from issue_flow.agent import run_state

    raise typer.Exit(code=run_state(project_dir, _console, json_output))


@agent_app.command("preflight")
def agent_preflight(
    project_dir: Path = _PROJECT_DIR_ARGUMENT,
    json_output: bool = typer.Option(
        False, "--json", help="Emit a machine-readable JSON object."
    ),
) -> None:
    """Branch hygiene report: default branch, clean/dirty, ahead/behind, stale."""
    from issue_flow.agent import run_preflight

    raise typer.Exit(code=run_preflight(project_dir, _console, json_output))


@agent_app.command("switchback")
def agent_switchback(
    project_dir: Path = _PROJECT_DIR_ARGUMENT,
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


@agent_app.command("version-plan")
def agent_version_plan(
    project_dir: Path = _PROJECT_DIR_ARGUMENT,
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


@agent_app.command("sweep")
def agent_sweep(
    project_dir: Path = _PROJECT_DIR_ARGUMENT,
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
    ``label_flows``, ``yolo_label``, ``step_directives``, ``model_label_flows``,
    ``deep_model_label``, ``fast_model_label`` — taking each from its
    ``ISSUEFLOW_*`` env var when set, else the default. Other ``ISSUEFLOW_*``
    settings are environment-only and are not written here. Existing files are
    left untouched unless ``--force`` is passed.
    """
    from issue_flow.agent import run_config_add

    raise typer.Exit(code=run_config_add(project_dir, _console, force, json_output))


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
        False, "--force", "-f", help="Overwrite an existing registry file."
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
        code=run_workspace_init(workspace_dir, _console, default, force, json_output)
    )


app.add_typer(agent_app)
app.add_typer(config_app)
app.add_typer(workspace_app)


def main() -> None:
    """Entry point for the `issue-flow` console script."""
    app()
