"""Convert between canonical and per-editor issue-flow scaffold layouts."""

from __future__ import annotations

from pathlib import Path

import typer

from issue_flow import modes as modes_module
import issue_flow.console_io as console_io
from issue_flow.config import Settings
from issue_flow.editors import get_profile
from issue_flow.init import _create_issueflow_dirs, _ensure_agents_md
from issue_flow.surfaces import (
    ensure_editor_gitignore,
    materialize_canonical_store,
    materialize_editor_profile,
    prune_all_editor_surfaces,
    prune_other_editor_surfaces,
)


def run_convert(
    project_root: Path,
    *,
    to: str | None = None,
    force: bool = False,
    prune_other: bool = False,
    gitignore: bool = False,
) -> None:
    """Materialize canonical or per-editor scaffold surfaces.

    Args:
        project_root: Absolute path to the user's project directory.
        to: Target layout — an editor id (``cursor``, ``claude``, …) or
            ``canonical`` for the team-committed store under
            ``.issueflows/agent/``.
        force: Overwrite existing manifest outputs.
        prune_other: Remove scaffold trees for non-target editors afterward.
        gitignore: Append a managed ``.gitignore`` block for local editor dirs.
    """
    settings = Settings()
    try:
        mode_obj = settings.resolve_mode(project_root)
    except ValueError as exc:
        console_io.console.print(f"[red]error[/red]  {exc}")
        raise typer.Exit(code=2) from None

    skill_level_id = settings.resolve_skill_level(project_root)
    target = settings.resolve_target_editor(project_root, to)
    cfg_path = settings.config_path(project_root)

    console_io.console.print(
        f"\n[bold]Converting issue-flow surfaces in [cyan]{project_root}[/cyan][/bold]"
    )
    console_io.console.print(f"[dim]Target: {target}[/dim]")
    console_io.console.print(f"[dim]Mode: {mode_obj.id}[/dim]")
    console_io.console.print(f"[dim]Skill level: {skill_level_id}[/dim]\n")

    _create_issueflow_dirs(project_root, settings)

    if target == "canonical":
        console_io.console.print("[bold]Canonical store[/bold] (.issueflows/agent/)")
        result = materialize_canonical_store(
            project_root,
            settings,
            mode_obj,
            skill_level_id,
            force=force,
            ensure_agents_md=_ensure_agents_md,
        )
        modes_module.write_canonical_format(cfg_path, True)
        console_io.console.print(
            f"  [green]write[/green] {cfg_path.relative_to(project_root).as_posix()}  "
            "(canonical_format = true)"
        )
        if prune_other:
            pruned = prune_all_editor_surfaces(
                project_root, settings, mode_obj, skill_level_id
            )
            result.pruned += pruned
    else:
        try:
            profile = get_profile(target)
        except ValueError as exc:
            console_io.console.print(f"[red]error[/red]  {exc}")
            raise typer.Exit(code=2) from None

        console_io.console.print(
            f"[bold]{profile.name}[/bold] ([cyan]{profile.agent_dir}[/cyan])"
        )
        result = materialize_editor_profile(
            project_root,
            settings,
            profile,
            mode_obj,
            skill_level_id,
            force=force,
            prune=True,
            ensure_agents_md=_ensure_agents_md,
        )
        modes_module.write_persisted_editor(cfg_path, profile.id)
        if prune_other:
            result.pruned += prune_other_editor_surfaces(
                project_root,
                settings,
                keep_profile=profile,
                mode=mode_obj,
                skill_level=skill_level_id,
            )

    if gitignore:
        ensure_editor_gitignore(project_root)

    console_io.console.print()
    if result.written:
        console_io.console.print(
            f"[bold green]Wrote {len(result.written)} file(s).[/bold green]"
        )
    if result.skipped:
        console_io.console.print(
            f"[bold yellow]Skipped {len(result.skipped)} existing file(s).[/bold yellow]"
        )
    if result.pruned:
        console_io.console.print(
            f"[bold yellow]Pruned {result.pruned} scaffold path(s).[/bold yellow]"
        )
    if not result.written and not result.skipped and not result.pruned:
        console_io.console.print("[bold]Nothing to do.[/bold]")

    console_io.console.print(
        "\n[dim]Editor-specific trees are generated artifacts. When using the "
        "canonical workflow, commit [bold].issueflows/agent/[/bold] and "
        "[bold]AGENTS.md[/bold]; run [bold]issue-flow convert --to <editor>[/bold] "
        "after checkout.[/dim]\n"
    )
