"""Shared scaffolding helpers for init, update, and convert."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rich.console import Console

from issue_flow.config import Settings
from issue_flow.editors import EDITORS, EditorProfile, get_profile
from issue_flow.modes import Mode
from issue_flow.step_profiles import enrich_render_context
from issue_flow.templating import (
    build_canonical_manifest,
    build_manifest,
    render_template,
    resolve_output_path,
)

console = Console()

SurfaceTarget = Literal["editor", "canonical"]

# Neutral render profile for canonical skill snapshots (skills-first, no rules extra).
_CANONICAL_RENDER_PROFILE = get_profile("codex")

_GITIGNORE_MARKER_BEGIN = "# BEGIN issue-flow editor surfaces (generated; do not edit)"
_GITIGNORE_MARKER_END = "# END issue-flow editor surfaces"


@dataclass
class MaterializeResult:
    written: list[Path]
    skipped: list[Path]
    pruned: int


def write_manifest_files(
    project_root: Path,
    manifest: list[tuple[str, str]],
    context: dict[str, object],
    *,
    force: bool,
) -> tuple[list[Path], list[Path]]:
    """Render templates from ``manifest`` and write under ``project_root``."""
    written_files: list[Path] = []
    skipped_files: list[Path] = []

    for template_name, path_template in manifest:
        relative_path = resolve_output_path(path_template, context)
        absolute_path = project_root / relative_path

        if absolute_path.exists() and not force:
            console.print(
                f"  [yellow]skip[/yellow]  {relative_path}  "
                "(already exists, use --force to overwrite)"
            )
            skipped_files.append(relative_path)
            continue

        render_context = enrich_render_context(context, template_name)
        rendered = render_template(template_name, render_context)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text(rendered, encoding="utf-8")
        console.print(f"  [green]write[/green] {relative_path}")
        written_files.append(relative_path)

    return written_files, skipped_files


def write_canonical_manifest_json(
    project_root: Path,
    settings: Settings,
    mode: Mode,
    skill_level: str,
    *,
    force: bool,
) -> Path | None:
    """Write ``.issueflows/agent/manifest.json`` describing the canonical store."""
    from issue_flow import __version__ as issue_flow_version

    agent_dir = project_root / settings.issueflows_dir / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    path = agent_dir / "manifest.json"
    relative = path.relative_to(project_root)

    payload = {
        "issue_flow_version": issue_flow_version,
        "mode": mode.id,
        "skill_level": skill_level,
        "skills": sorted(mode.skills),
        "commands": sorted(mode.commands),
        "format": "issueflow-canonical-v1",
    }
    text = json.dumps(payload, indent=2) + "\n"
    if path.exists() and not force:
        console.print(
            f"  [yellow]skip[/yellow]  {relative}  "
            "(already exists, use --force to overwrite)"
        )
        return None

    path.write_text(text, encoding="utf-8")
    console.print(f"  [green]write[/green] {relative}")
    return relative


def materialize_editor_profile(
    project_root: Path,
    settings: Settings,
    profile: EditorProfile,
    mode: Mode,
    skill_level: str,
    *,
    force: bool,
    prune: bool,
    ensure_agents_md: Callable[[Path, dict[str, object]], None],
) -> MaterializeResult:
    """Render and write one editor profile's scaffold surfaces."""
    from issue_flow.init import (
        _prune_excluded_surfaces,
        _prune_retired_files,
    )

    context = settings.template_context(
        project_root, profile, mode=mode, skill_level=skill_level
    )
    written, skipped = write_manifest_files(
        project_root,
        build_manifest(profile, mode, skill_level=skill_level),
        context,
        force=force,
    )
    ensure_agents_md(project_root, context)
    pruned = 0
    if prune:
        pruned += _prune_retired_files(project_root, profile)
        pruned += _prune_excluded_surfaces(project_root, profile, mode)
    return MaterializeResult(written=written, skipped=skipped, pruned=pruned)


def materialize_canonical_store(
    project_root: Path,
    settings: Settings,
    mode: Mode,
    skill_level: str,
    *,
    force: bool,
    ensure_agents_md: Callable[[Path, dict[str, object]], None],
) -> MaterializeResult:
    """Render editor-neutral skills into ``.issueflows/agent/``."""
    context = settings.template_context(
        project_root,
        _CANONICAL_RENDER_PROFILE,
        mode=mode,
        skill_level=skill_level,
    )
    written, skipped = write_manifest_files(
        project_root,
        build_canonical_manifest(mode, skill_level=skill_level),
        context,
        force=force,
    )
    ensure_agents_md(project_root, context)
    manifest_path = write_canonical_manifest_json(
        project_root, settings, mode, skill_level, force=force
    )
    if manifest_path is not None:
        written.append(manifest_path)
    return MaterializeResult(written=written, skipped=skipped, pruned=0)


def collect_profile_paths(
    project_root: Path,
    settings: Settings,
    profile: EditorProfile,
    mode: Mode,
    skill_level: str,
) -> list[Path]:
    """Return manifest output paths for ``profile`` (files and parent dirs)."""
    context = settings.template_context(
        project_root, profile, mode=mode, skill_level=skill_level
    )
    paths: list[Path] = []
    for _, path_template in build_manifest(profile, mode, skill_level=skill_level):
        paths.append(resolve_output_path(path_template, context))
    return paths


def prune_other_editor_surfaces(
    project_root: Path,
    settings: Settings,
    keep_profile: EditorProfile | None,
    mode: Mode,
    skill_level: str,
) -> int:
    """Remove scaffold trees for every editor profile except ``keep_profile``."""
    pruned = 0
    for editor_id, profile in EDITORS.items():
        if keep_profile is not None and profile.id == keep_profile.id:
            continue
        agent_root = project_root / profile.agent_dir
        if agent_root.exists():
            shutil.rmtree(agent_root)
            console.print(f"  [yellow]prune[/yellow]  {agent_root.relative_to(project_root)}/")
            pruned += 1
        for relative in collect_profile_paths(
            project_root, settings, profile, mode, skill_level
        ):
            absolute = project_root / relative
            if absolute.is_file():
                absolute.unlink()
                console.print(f"  [yellow]prune[/yellow]  {relative}")
                pruned += 1
        if profile.rules_extra:
            _, rules_template = profile.rules_extra
            context = settings.template_context(
                project_root, profile, mode=mode, skill_level=skill_level
            )
            rules_path = project_root / resolve_output_path(rules_template, context)
            if rules_path.is_file():
                rules_path.unlink()
                console.print(f"  [yellow]prune[/yellow]  {rules_path.relative_to(project_root)}")
                pruned += 1
    return pruned


def prune_all_editor_surfaces(
    project_root: Path,
    settings: Settings,
    mode: Mode,
    skill_level: str,
) -> int:
    """Remove every known editor scaffold tree."""
    return prune_other_editor_surfaces(
        project_root, settings, keep_profile=None, mode=mode, skill_level=skill_level
    )

def ensure_editor_gitignore(project_root: Path) -> bool:
    """Append gitignore entries for local-only editor dirs. Returns True if changed."""
    lines = [
        _GITIGNORE_MARKER_BEGIN,
        ".cursor/",
        ".claude/",
        ".opencode/",
        ".codex/",
        _GITIGNORE_MARKER_END,
        "",
    ]
    block = "\n".join(lines)
    path = project_root / ".gitignore"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if _GITIGNORE_MARKER_BEGIN in existing:
            console.print("  [dim]skip[/dim]  .gitignore  (issue-flow editor block present)")
            return False
        updated = existing.rstrip("\n") + "\n\n" + block
    else:
        updated = block
    path.write_text(updated, encoding="utf-8")
    console.print("  [green]write[/green] .gitignore  (issue-flow editor surfaces)")
    return True
