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
) -> None:
    """Scaffold issue-flow directories and Cursor config files in a project."""
    from issue_flow.init import run_init

    run_init(project_root=project_dir, force=force)


def main() -> None:
    """Entry point for the `issue-flow` console script."""
    app()
