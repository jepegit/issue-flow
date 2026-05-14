"""Command-line interface for issue-flow."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="issue-flow",
    add_completion=False,
)

_console = Console()


@app.callback()
def _callback() -> None:
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
) -> None:
    """Scaffold issue-flow directories and Cursor config files in a project."""
    from issue_flow.init import run_init

    run_init(
        project_root=project_dir, force=force, skip_dep_check=skip_dep_check
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
) -> None:
    """Refresh packaged Cursor commands, rules, and workflow doc from this package."""
    from issue_flow.init import run_update

    run_update(project_root=project_dir, skip_dep_check=skip_dep_check)


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def build(
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

    With no extra arguments runs ``graphify extract <project_dir>`` (the
    full AST + semantic LLM build). Override the subcommand by passing
    it as the first argument: ``issue-flow build update`` (fast,
    code-only re-extract), ``issue-flow build watch`` (live rebuild),
    ``issue-flow build cluster-only --no-viz`` (re-cluster), etc.
    Trailing flags pass through verbatim. Use ``-C <dir>`` to scan a
    project other than the current directory. Requires ``graphify`` to
    be on ``PATH`` (install with ``uv tool install graphifyy``).
    """
    from issue_flow.graphify import run_build

    exit_code = run_build(project_dir, ctx.args, _console)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


def main() -> None:
    """Entry point for the `issue-flow` console script."""
    app()
