"""Shared scaffolding helpers for init, update, and convert."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import issue_flow.console_io as console_io
from issue_flow.config import Settings
from issue_flow.editors import EDITORS, EditorProfile, get_profile
from issue_flow.modes import Mode
from issue_flow.step_profiles import enrich_render_context
from issue_flow.skill_ownership import (
    foreign_skill_reason,
    hash_skill_text,
    load_stamp_hashes,
    load_stamps,
    prepare_skill_dir_for_write,
    replace_skill_file,
    save_stamp,
    save_stamp_hash,
    stamp_key,
    user_global_stamp_key,
)
from issue_flow.templating import (
    BOTH_SKILL_STEMS,
    build_canonical_manifest,
    build_manifest,
    is_skill_template,
    render_template,
    resolve_output_path,
    skill_output_name,
)
from issue_flow.user_global import (
    editor_user_global_skills_root,
    user_global_skill_stamp_path,
)

SurfaceTarget = Literal["editor", "canonical"]

# Neutral render profile for canonical skill snapshots (skills-first, no rules extra).
_CANONICAL_RENDER_PROFILE = get_profile("codex")

_GITIGNORE_MARKER_BEGIN = "# BEGIN issue-flow editor surfaces (generated; do not edit)"
_GITIGNORE_MARKER_END = "# END issue-flow editor surfaces"

_LINGUIST_MARKER_BEGIN = "# BEGIN issue-flow linguist (generated; do not edit)"
_LINGUIST_MARKER_END = "# END issue-flow linguist"

# Keep GitHub Linguist focused on library source; paths match issue #168.
_LINGUIST_BLOCK_LINES = (
    _LINGUIST_MARKER_BEGIN,
    "# GitHub Linguist: keep language stats focused on library source.",
    "# Without this, graphify-out/graph.html might dominate as HTML.",
    "",
    "graphify-out/** linguist-generated",
    "docs/** linguist-documentation",
    "tests/** linguist-documentation",
    ".issueflows/** linguist-documentation",
    "dev/** linguist-documentation",
    "scripts/** linguist-documentation",
    "",
    "# Cross-platform line endings for shell helpers",
    ".aliases     text eol=lf",
    "*.sh         text eol=lf",
    "*.lock       text eol=lf",
    _LINGUIST_MARKER_END,
    "",
)


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
    overwrite_foreign: bool = False,
) -> tuple[list[Path], list[Path]]:
    """Render templates from ``manifest`` and write under ``project_root``."""
    written_files: list[Path] = []
    skipped_files: list[Path] = []
    issueflows_dir = str(context.get("issueflows_dir") or ".issueflows")
    stamps = load_stamps(project_root, issueflows_dir)

    for template_name, path_template in manifest:
        relative_path = resolve_output_path(path_template, context)
        absolute_path = project_root / relative_path

        if absolute_path.exists() and not force:
            console_io.console.print(
                f"  [yellow]skip[/yellow]  {relative_path}  "
                "(already exists, use --force to overwrite)"
            )
            skipped_files.append(relative_path)
            continue

        if is_skill_template(template_name) and not overwrite_foreign:
            skill_dir = absolute_path.parent
            reason = foreign_skill_reason(
                skill_dir,
                stamp=stamps.get(stamp_key(project_root, skill_dir)),
            )
            if reason:
                rel_dir = skill_dir.relative_to(project_root).as_posix()
                console_io.console.print(
                    f"  [yellow]skip[/yellow]  {rel_dir}/  "
                    f"(foreign skill: {reason}; use --force to overwrite)"
                )
                skipped_files.append(relative_path)
                continue

        render_context = enrich_render_context(context, template_name)
        rendered = render_template(template_name, render_context)
        if is_skill_template(template_name):
            prepare_skill_dir_for_write(absolute_path.parent)
            replace_skill_file(absolute_path, rendered)
            save_stamp(
                project_root,
                issueflows_dir,
                absolute_path.parent,
                hash_skill_text(rendered),
            )
        else:
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            absolute_path.write_text(rendered, encoding="utf-8")
        console_io.console.print(f"  [green]write[/green] {relative_path}")
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
        console_io.console.print(
            f"  [yellow]skip[/yellow]  {relative}  "
            "(already exists, use --force to overwrite)"
        )
        return None

    path.write_text(text, encoding="utf-8")
    console_io.console.print(f"  [green]write[/green] {relative}")
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
    overwrite_foreign: bool = False,
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
        overwrite_foreign=overwrite_foreign,
    )
    ensure_agents_md(project_root, context)
    pruned = 0
    if prune:
        pruned += _prune_retired_files(project_root, profile)
        pruned += _prune_excluded_surfaces(project_root, profile, mode)
    return MaterializeResult(written=written, skipped=skipped, pruned=pruned)


def materialize_user_global_both_skills(
    project_root: Path,
    settings: Settings,
    profiles: list[EditorProfile],
    mode: Mode,
    skill_level: str,
    *,
    overwrite_foreign: bool,
) -> MaterializeResult:
    """Write ``both`` stems to each selected editor's user-global skill dir.

    Project-local copies stay (no ``global``-only stems). Stamps live under
    the user-global issue-flow dir. Foreign global dirs are skipped unless
    ``overwrite_foreign``. Cursor globals never land in ``~/.claude/skills``.
    """
    stems = [stem for stem in BOTH_SKILL_STEMS if stem in mode.skills]
    if not stems:
        return MaterializeResult(written=[], skipped=[], pruned=0)

    stamp_path = user_global_skill_stamp_path()
    stamps = load_stamp_hashes(stamp_path)
    written: list[Path] = []
    skipped: list[Path] = []

    console_io.console.print("\n[bold]User-global both skills[/bold]")
    for profile in profiles:
        root = editor_user_global_skills_root(profile.id)
        if root is None:
            continue
        context = settings.template_context(
            project_root, profile, mode=mode, skill_level=skill_level
        )
        for stem in stems:
            output_name = skill_output_name(stem)
            skill_dir = root / output_name
            dest = skill_dir / "SKILL.md"
            key = user_global_stamp_key(profile.id, output_name)
            label = f"{profile.id}:{dest}"

            if not overwrite_foreign:
                reason = foreign_skill_reason(skill_dir, stamp=stamps.get(key))
                if reason:
                    console_io.console.print(
                        f"  [yellow]skip[/yellow]  {label}  "
                        f"(foreign skill: {reason}; use --force to overwrite)"
                    )
                    skipped.append(dest)
                    continue

            template_name = f"skills/{stem}/SKILL.md.j2"
            render_context = enrich_render_context(context, template_name)
            rendered = render_template(template_name, render_context)
            prepare_skill_dir_for_write(skill_dir)
            replace_skill_file(dest, rendered)
            digest = hash_skill_text(rendered)
            save_stamp_hash(stamp_path, key, digest)
            stamps[key] = digest
            console_io.console.print(f"  [green]write[/green] {label}")
            written.append(dest)

    return MaterializeResult(written=written, skipped=skipped, pruned=0)


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
        overwrite_foreign=force,
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
            console_io.console.print(
                f"  [yellow]prune[/yellow]  {agent_root.relative_to(project_root)}/"
            )
            pruned += 1
        for relative in collect_profile_paths(
            project_root, settings, profile, mode, skill_level
        ):
            absolute = project_root / relative
            if absolute.is_file():
                absolute.unlink()
                console_io.console.print(f"  [yellow]prune[/yellow]  {relative}")
                pruned += 1
        if profile.rules_extra:
            _, rules_template = profile.rules_extra
            context = settings.template_context(
                project_root, profile, mode=mode, skill_level=skill_level
            )
            rules_path = project_root / resolve_output_path(rules_template, context)
            if rules_path.is_file():
                rules_path.unlink()
                console_io.console.print(
                    f"  [yellow]prune[/yellow]  {rules_path.relative_to(project_root)}"
                )
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
            console_io.console.print(
                "  [dim]skip[/dim]  .gitignore  (issue-flow editor block present)"
            )
            return False
        updated = existing.rstrip("\n") + "\n\n" + block
    else:
        updated = block
    path.write_text(updated, encoding="utf-8")
    console_io.console.print(
        "  [green]write[/green] .gitignore  (issue-flow editor surfaces)"
    )
    return True


def ensure_linguist_gitattributes(project_root: Path) -> bool:
    """Append a managed Linguist ``.gitattributes`` block. Returns True if changed.

    Idempotent: skips when the begin marker is already present. Never rewrites
    user content outside the managed block. Does not remove the block when the
    feature is later disabled — callers gate invocation on the config flag.
    """
    block = "\n".join(_LINGUIST_BLOCK_LINES)
    path = project_root / ".gitattributes"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if _LINGUIST_MARKER_BEGIN in existing:
            console_io.console.print(
                "  [dim]skip[/dim]  .gitattributes  (issue-flow linguist block present)"
            )
            return False
        updated = existing.rstrip("\n") + "\n\n" + block
    else:
        updated = block
    path.write_text(updated, encoding="utf-8")
    console_io.console.print(
        "  [green]write[/green] .gitattributes  (issue-flow linguist)"
    )
    return True


def maybe_ensure_linguist_gitattributes(project_root: Path, settings: Settings) -> bool:
    """Write the Linguist block when ``linguist_attributes`` resolves true."""
    if not settings.resolve_linguist_attributes(project_root):
        return False
    return ensure_linguist_gitattributes(project_root)
