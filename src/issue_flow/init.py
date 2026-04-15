"""Implementation of the `issue-flow init` command."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from issue_flow.config import Settings
from issue_flow.templating import (
    TEMPLATE_MANIFEST,
    render_template,
    resolve_output_path,
)

console = Console()


def run_init(project_root: Path, force: bool = False) -> None:
    """Scaffold .issueflows/ directories and .cursor/ config files.

    Args:
        project_root: Absolute path to the user's project directory.
        force: If True, overwrite existing files without asking.
    """
    settings = Settings()
    context = settings.template_context(project_root)

    console.print(
        f"\n[bold]Initializing issue-flow in [cyan]{project_root}[/cyan][/bold]\n"
    )

    # ── 1. Create .issueflows/ subdirectories ────────────────────────
    _create_issueflow_dirs(project_root, settings)

    # ── 2. Render and write template files ───────────────────────────
    written_files: list[Path] = []
    skipped_files: list[Path] = []

    for template_name, path_template in TEMPLATE_MANIFEST:
        relative_path = resolve_output_path(path_template, context)
        absolute_path = project_root / relative_path

        if absolute_path.exists() and not force:
            console.print(
                f"  [yellow]skip[/yellow]  {relative_path}  (already exists, use --force to overwrite)"
            )
            skipped_files.append(relative_path)
            continue

        rendered = render_template(template_name, context)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text(rendered, encoding="utf-8")
        console.print(f"  [green]write[/green] {relative_path}")
        written_files.append(relative_path)

    # ── 3. Summary ───────────────────────────────────────────────────
    console.print()
    if written_files:
        console.print(
            f"[bold green]Created {len(written_files)} file(s).[/bold green]"
        )
    if skipped_files:
        console.print(
            f"[bold yellow]Skipped {len(skipped_files)} existing file(s).[/bold yellow]"
        )
    if not written_files and not skipped_files:
        console.print("[bold]Nothing to do.[/bold]")

    console.print(
        "\n[dim]Run [bold]/issue-init <number>[/bold] or [bold]/issue-init[/bold] "
        "(on a branch like [bold]42-slug[/bold], after confirmation) in Cursor "
        "to start tracking a GitHub issue.[/dim]\n"
    )


def _create_issueflow_dirs(project_root: Path, settings: Settings) -> None:
    """Create the .issueflows/ directory tree."""
    base = project_root / settings.issueflows_dir

    for subdir_name in settings.issueflows_subdirs:
        dir_path = base / subdir_name
        if dir_path.exists():
            console.print(f"  [dim]exists[/dim] {settings.issueflows_dir}/{subdir_name}/")
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"  [green]mkdir[/green]  {settings.issueflows_dir}/{subdir_name}/")

        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
