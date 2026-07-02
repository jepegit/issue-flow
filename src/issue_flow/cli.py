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
        "state by hand. All are read-only except `sweep` and `capture`."
    ),
)

config_app = typer.Typer(
    name="config",
    add_completion=False,
    help="Manage the project's .issueflows/config.toml.",
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

    run_update(
        project_root=project_dir, skip_dep_check=skip_dep_check, editors=editor
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

    Writes the six keys issue-flow reads from config.toml — ``mode``,
    ``skill_level``, ``caveman_default``, ``grill_me_default``, ``label_flows``,
    ``yolo_label`` — taking each from its ``ISSUEFLOW_*`` env var when set, else
    the default. Other ``ISSUEFLOW_*`` settings are environment-only and are not
    written here. Existing files are left untouched unless ``--force`` is passed.
    """
    from issue_flow.agent import run_config_add

    raise typer.Exit(code=run_config_add(project_dir, _console, force, json_output))


app.add_typer(agent_app)
app.add_typer(config_app)


def main() -> None:
    """Entry point for the `issue-flow` console script."""
    app()
