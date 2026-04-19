"""Command-line interface for issue-flow."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(
    name="issue-flow",
    add_completion=False,
)


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


def main() -> None:
    """Entry point for the `issue-flow` console script."""
    app()
