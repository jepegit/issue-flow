"""Implementation of the `issue-flow init` and `issue-flow update` commands."""

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


def _write_manifest_files(
    project_root: Path,
    context: dict[str, str],
    *,
    force: bool,
) -> tuple[list[Path], list[Path]]:
    """Render templates from TEMPLATE_MANIFEST and write under project_root.

    When ``force`` is False, existing files are skipped (not overwritten).
    Issue markdown under ``.issueflows/`` is never part of the manifest.

    Returns:
        (written_relative_paths, skipped_relative_paths)
    """
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

    return written_files, skipped_files


def _already_initialized(
    project_root: Path, settings: Settings, context: dict[str, str]
) -> bool:
    """True if the tree looks like issue-flow was set up here before."""
    base = project_root / settings.issueflows_dir
    if not base.is_dir():
        return False
    return any(
        (project_root / resolve_output_path(path_template, context)).is_file()
        for _, path_template in TEMPLATE_MANIFEST
    )


def run_init(project_root: Path, force: bool = False) -> None:
    """Scaffold .issueflows/ directories and .cursor/ config (commands, rules, skills).

    Re-running without ``force`` skips existing manifest outputs so local
    edits and issue markdown under ``.issueflows/`` are preserved. Manifest
    paths never include issue status or description files.

    Args:
        project_root: Absolute path to the user's project directory.
        force: If True, overwrite existing manifest files without asking.
    """
    settings = Settings()
    context = settings.template_context(project_root)

    console.print(
        f"\n[bold]Initializing issue-flow in [cyan]{project_root}[/cyan][/bold]\n"
    )

    if not force and _already_initialized(project_root, settings, context):
        console.print(
            "[dim]This project already has issue-flow scaffold files. "
            "Existing files are skipped so your issue notes stay intact. "
            "Run [bold]issue-flow update[/bold] to refresh commands, rules, and docs "
            "from your installed package version. Use [bold]issue-flow init --force[/bold] "
            "to overwrite scaffold files in place.[/dim]\n"
        )

    _create_issueflow_dirs(project_root, settings)

    written_files, skipped_files = _write_manifest_files(
        project_root, context, force=force
    )

    console.print()
    if written_files:
        console.print(f"[bold green]Created {len(written_files)} file(s).[/bold green]")
    if skipped_files:
        console.print(
            f"[bold yellow]Skipped {len(skipped_files)} existing file(s).[/bold yellow]"
        )
    if not written_files and not skipped_files:
        console.print("[bold]Nothing to do.[/bold]")

    console.print(
        "\n[dim]Run [bold]/issue-init <number>[/bold] or [bold]/issue-init[/bold] "
        "(on a branch like [bold]42-slug[/bold], after confirmation) in Cursor "
        "to start tracking a GitHub issue. "
        "Optional Agent Skills live under [bold].cursor/skills/[/bold] "
        "([bold]/issueflow-issue-init[/bold], etc.).[/dim]\n"
    )


def run_update(project_root: Path) -> None:
    """Refresh packaged scaffold files (commands, rule, skills, workflow doc).

    Overwrites every path in ``TEMPLATE_MANIFEST`` with the templates from the
    installed package. Does not read or delete other files under ``.issueflows/``
    (issue markdown is never written by the manifest).

    Ensures ``.issueflows/`` subdirectories from settings exist (e.g. new
    folders in a newer package version).
    """
    settings = Settings()
    context = settings.template_context(project_root)

    console.print(
        f"\n[bold]Updating issue-flow scaffold in [cyan]{project_root}[/cyan][/bold]\n"
    )

    _create_issueflow_dirs(project_root, settings)

    written_files, _skipped = _write_manifest_files(project_root, context, force=True)

    console.print()
    if written_files:
        console.print(
            f"[bold green]Refreshed {len(written_files)} file(s).[/bold green]"
        )
    else:
        console.print("[bold]Nothing to write.[/bold]")

    console.print(
        "\n[dim]Manifest outputs were overwritten from the installed package. "
        "Issue files under [bold].issueflows/[/bold] were not modified by this command.[/dim]\n"
    )


def _create_issueflow_dirs(project_root: Path, settings: Settings) -> None:
    """Create the .issueflows/ directory tree."""
    base = project_root / settings.issueflows_dir

    for subdir_name in settings.issueflows_subdirs:
        dir_path = base / subdir_name
        if dir_path.exists():
            console.print(
                f"  [dim]exists[/dim] {settings.issueflows_dir}/{subdir_name}/"
            )
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            console.print(
                f"  [green]mkdir[/green]  {settings.issueflows_dir}/{subdir_name}/"
            )

        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
