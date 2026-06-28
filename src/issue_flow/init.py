"""Implementation of the `issue-flow init` and `issue-flow update` commands."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import typer
from rich.console import Console

from issue_flow import modes as modes_module
from issue_flow.config import Settings
from issue_flow.dependencies import (
    check_dependencies,
    prompt_or_skip,
)
from issue_flow.editors import EditorProfile, resolve_editors
from issue_flow.graphify import register_with_editor as graphify_register_with_editor
from issue_flow.modes import Mode
from issue_flow.templating import (
    COMMAND_NAMES,
    RETIRED_COMMANDS,
    RETIRED_SKILLS,
    SKILL_DIRS,
    build_manifest,
    render_template,
    resolve_output_path,
    skill_output_name,
)

console = Console()

# Optional project-root `.env` entries (see README). Values are defaults for comments only.
_DOTENV_KEYS: tuple[tuple[str, str], ...] = (
    ("ISSUEFLOW_DIR", ".issueflows"),
    ("ISSUEFLOW_EDITOR", "cursor"),
    ("ISSUEFLOW_AGENT_DIR", ".cursor"),
    ("ISSUEFLOW_DOCS_DIR", "docs"),
    ("ISSUEFLOW_HISTORY_FILE", "HISTORY.md"),
    ("ISSUEFLOW_MODE", "standard"),
)
_DOTENV_SECTION_HEADER = "# --- issue-flow: optional environment variables ---\n"

# Marker-delimited managed block for AGENTS.md. AGENTS.md is frequently a
# hand-maintained user file, so issue-flow only ever owns the content between
# these markers and never clobbers the rest.
_AGENTS_FILE = "AGENTS.md"
_AGENTS_BEGIN = "<!-- BEGIN issue-flow (managed: do not edit this block) -->"
_AGENTS_END = "<!-- END issue-flow (managed) -->"
_AGENTS_BLOCK_RE = re.compile(
    re.escape(_AGENTS_BEGIN) + ".*?" + re.escape(_AGENTS_END),
    re.DOTALL,
)
_PROJECT_BRIEF_FILE = "this-project.md"


def _dotenv_documents_key(content: str, key: str) -> bool:
    """True if ``key`` appears as an assignment, optionally after ``#`` or ``export``."""
    pattern = re.compile(
        rf"(?m)^\s*#?\s*(?:export\s+)?{re.escape(key)}\s*=",
    )
    return bool(pattern.search(content))


def _ensure_dotenv_file(project_root: Path) -> None:
    """Create or extend ``.env`` with commented ``ISSUEFLOW_*`` hints.

    Never removes or replaces an existing ``.env`` (including with ``init
    --force``): only creates a starter file or appends missing keys as
    comments.
    """
    env_path = project_root / ".env"
    relative = Path(".env")

    if not env_path.exists():
        lines = [
            "# issue-flow reads optional ISSUEFLOW_* variables from this file.\n",
            "# Uncomment to override defaults.\n",
            "\n",
        ]
        for key, default in _DOTENV_KEYS:
            lines.append(f"# {key}={default}\n")
        env_path.write_text("".join(lines), encoding="utf-8")
        console.print(f"  [green]write[/green] {relative}")
        return

    existing = env_path.read_text(encoding="utf-8")
    missing = [(k, d) for k, d in _DOTENV_KEYS if not _dotenv_documents_key(existing, k)]
    if not missing:
        console.print(
            f"  [dim]skip[/dim]  {relative}  "
            "(already lists ISSUEFLOW_* settings; not modified)"
        )
        return

    block: list[str] = ["\n", _DOTENV_SECTION_HEADER]
    for key, default in missing:
        block.append(f"# {key}={default}\n")
    with env_path.open("a", encoding="utf-8") as f:
        f.write("".join(block))
    console.print(
        f"  [green]append[/green] {relative}  "
        f"(added {len(missing)} commented ISSUEFLOW_* line(s))"
    )


def _write_manifest_files(
    project_root: Path,
    manifest: list[tuple[str, str]],
    context: dict[str, str],
    *,
    force: bool,
) -> tuple[list[Path], list[Path]]:
    """Render templates from ``manifest`` and write under project_root.

    When ``force`` is False, existing files are skipped (not overwritten).
    Issue markdown under ``.issueflows/`` is never part of the manifest.

    Returns:
        (written_relative_paths, skipped_relative_paths)
    """
    written_files: list[Path] = []
    skipped_files: list[Path] = []

    for template_name, path_template in manifest:
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


def _ensure_agents_md(project_root: Path, context: dict[str, str]) -> None:
    """Upsert the issue-flow managed block into the project-root ``AGENTS.md``.

    ``AGENTS.md`` is the convergent rules target across editors and is often a
    hand-maintained user file. This writer therefore only owns the content
    between the issue-flow markers:

    * file missing -> create it with just the managed block;
    * markers present -> replace the block in place, leaving surrounding
      content untouched;
    * file exists without markers -> append the block after existing content.

    Idempotent: if the resulting file would be unchanged, nothing is written.
    """
    rendered = render_template("rules/AGENTS.md.j2", context)
    block = f"{_AGENTS_BEGIN}\n{rendered}{_AGENTS_END}\n"

    path = project_root / _AGENTS_FILE
    relative = Path(_AGENTS_FILE)

    if not path.exists():
        path.write_text(block, encoding="utf-8")
        console.print(f"  [green]write[/green] {relative}  (issue-flow managed block)")
        return

    existing = path.read_text(encoding="utf-8")

    if _AGENTS_BLOCK_RE.search(existing):
        replacement = f"{_AGENTS_BEGIN}\n{rendered}{_AGENTS_END}"
        updated = _AGENTS_BLOCK_RE.sub(lambda _m: replacement, existing)
        if updated == existing:
            console.print(
                f"  [dim]skip[/dim]  {relative}  (issue-flow block already up to date)"
            )
            return
        path.write_text(updated, encoding="utf-8")
        console.print(
            f"  [green]update[/green] {relative}  (refreshed issue-flow managed block)"
        )
        return

    updated = existing.rstrip("\n") + "\n\n" + block
    path.write_text(updated, encoding="utf-8")
    console.print(
        f"  [green]append[/green] {relative}  (added issue-flow managed block)"
    )


def _ensure_project_brief(
    project_root: Path,
    settings: Settings,
    context: dict[str, str],
) -> None:
    """Create the durable project brief when it is missing.

    The brief lives in ``04-designs-and-guides`` and is intended for users to edit
    freely, so it is deliberately outside the manifest that ``run_update``
    refreshes.
    """
    relative = (
        Path(settings.issueflows_dir) / settings.designs_folder / _PROJECT_BRIEF_FILE
    )
    path = project_root / relative

    if path.exists():
        console.print(
            f"  [dim]skip[/dim]  {relative}  (project brief already exists)"
        )
        return

    rendered = render_template("docs/this-project.md.j2", context)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    console.print(f"  [green]write[/green] {relative}")


def _already_initialized(
    project_root: Path,
    settings: Settings,
    profiles: list[EditorProfile],
) -> bool:
    """True if the tree looks like issue-flow was set up here for any profile."""
    base = project_root / settings.issueflows_dir
    if not base.is_dir():
        return False
    for profile in profiles:
        context = settings.template_context(project_root, profile)
        manifest = build_manifest(profile)
        if any(
            (project_root / resolve_output_path(path_template, context)).is_file()
            for _, path_template in manifest
        ):
            return True
    return False


def run_init(
    project_root: Path,
    force: bool = False,
    skip_dep_check: bool = False,
    editors: list[str] | None = None,
    mode: str | None = None,
) -> None:
    """Scaffold .issueflows/ directories and editor config (commands, rules, skills).

    Scaffolds once per selected editor profile (``editors``; defaults to
    ``["cursor"]``). Each profile writes its own ``agent_dir`` tree (skills
    always, slash commands when supported, optional ``.mdc`` / ``CLAUDE.md``)
    plus the shared, editor-neutral ``AGENTS.md`` managed block and workflow doc.

    Also ensures a project-root ``.env`` exists or appends commented
    ``ISSUEFLOW_*`` lines for any keys not yet documented there. Existing
    ``.env`` files are never replaced in full (even with ``force``).

    Re-running without ``force`` skips existing manifest outputs so local
    edits and issue markdown under ``.issueflows/`` are preserved. Manifest
    paths never include issue status or description files.

    Before scaffolding, checks for required external CLI tools (``git``,
    ``gh``). If any are missing, prints install guidance and asks for
    confirmation before continuing (unless ``skip_dep_check`` is set or
    stdin is non-interactive).

    Args:
        project_root: Absolute path to the user's project directory.
        force: If True, overwrite existing manifest files without asking.
        skip_dep_check: If True, bypass the external-CLI dependency check.
        editors: Editor ids to scaffold for (``"all"`` expands to every
            supported editor). Defaults to the configured/default editor.
        mode: Scaffolding mode id (e.g. ``"simple"``). When given it is
            validated and persisted to ``.issueflows/config.toml`` so later
            ``update`` runs honour it. When omitted, the persisted/active mode is
            used (default ``standard``), and the persisted value is left as-is.
    """
    settings = Settings()
    try:
        profiles = resolve_editors(editors)
    except ValueError as exc:
        console.print(f"[red]error[/red]  {exc}")
        raise typer.Exit(code=2) from None

    cfg_path = settings.config_path(project_root)
    explicit_mode = mode is not None
    mode_id = mode if explicit_mode else settings.resolve_active_mode_id(project_root)
    try:
        mode_obj = modes_module.resolve_mode(mode_id, cfg_path)
    except ValueError as exc:
        console.print(f"[red]error[/red]  {exc}")
        raise typer.Exit(code=2) from None

    console.print(
        f"\n[bold]Initializing issue-flow in [cyan]{project_root}[/cyan][/bold]"
    )
    console.print(
        f"[dim]Editors: {', '.join(p.id for p in profiles)}[/dim]"
    )
    console.print(f"[dim]Mode: {mode_obj.id}[/dim]\n")

    if not _dependency_gate(skip_dep_check):
        raise typer.Exit(code=1)

    if not force and _already_initialized(project_root, settings, profiles):
        console.print(
            "[dim]This project already has issue-flow scaffold files. "
            "Existing files are skipped so your issue notes stay intact. "
            "Run [bold]issue-flow update[/bold] to refresh commands, rules, and docs "
            "from your installed package version. Use [bold]issue-flow init --force[/bold] "
            "to overwrite scaffold files in place.[/dim]\n"
        )

    _create_issueflow_dirs(project_root, settings)
    if explicit_mode:
        modes_module.write_active_mode(cfg_path, mode_obj.id)
        console.print(
            f"  [green]write[/green] {cfg_path.relative_to(project_root).as_posix()}  "
            f"(mode = {mode_obj.id})"
        )
    _ensure_project_brief(
        project_root,
        settings,
        settings.template_context(project_root, profiles[0], mode=mode_obj),
    )

    written_files: list[Path] = []
    skipped_files: list[Path] = []
    pruned_count = 0
    for profile in profiles:
        console.print(f"\n[bold]{profile.name}[/bold] ([cyan]{profile.agent_dir}[/cyan])")
        context = settings.template_context(project_root, profile, mode=mode_obj)
        written, skipped = _write_manifest_files(
            project_root, build_manifest(profile, mode_obj), context, force=force
        )
        _ensure_agents_md(project_root, context)
        pruned_count += _prune_retired_files(project_root, profile)
        pruned_count += _prune_excluded_surfaces(project_root, profile, mode_obj)
        written_files.extend(written)
        skipped_files.extend(skipped)

    console.print()
    _ensure_dotenv_file(project_root)

    console.print()
    _graphify_postinstall(project_root, profiles)

    console.print()
    if written_files:
        console.print(f"[bold green]Created {len(written_files)} file(s).[/bold green]")
    if skipped_files:
        console.print(
            f"[bold yellow]Skipped {len(skipped_files)} existing file(s).[/bold yellow]"
        )
    if pruned_count:
        console.print(
            f"[bold yellow]Pruned {pruned_count} retired scaffold file(s).[/bold yellow]"
        )
    if not written_files and not skipped_files and not pruned_count:
        console.print("[bold]Nothing to do.[/bold]")

    primary = profiles[0]
    console.print(
        "\n[dim]Run [bold]/iflow-init <number>[/bold] or [bold]/iflow-init[/bold] "
        "(on a branch like [bold]42-slug[/bold], after confirmation) in your editor "
        "to start tracking a GitHub issue. "
        f"Optional Agent Skills live under [bold]{primary.agent_dir}/skills/[/bold] "
        "([bold]/iflow-init[/bold], etc.).[/dim]\n"
    )


def run_update(
    project_root: Path,
    skip_dep_check: bool = False,
    editors: list[str] | None = None,
) -> None:
    """Refresh packaged scaffold files (commands, rule, skills, workflow doc).

    Overwrites every manifest path for each selected editor profile with the
    templates from the installed package, and refreshes the ``AGENTS.md``
    managed block. Does not read or delete other files under ``.issueflows/``
    (issue markdown is never written by the manifest).

    Ensures ``.issueflows/`` subdirectories from settings exist (e.g. new
    folders in a newer package version).

    Runs the same external-CLI dependency check as :func:`run_init` so
    upgrades also surface missing tools.

    Args:
        project_root: Absolute path to the user's project directory.
        skip_dep_check: If True, bypass the external-CLI dependency check.
        editors: Editor ids to refresh (``"all"`` expands to every supported
            editor). Defaults to the configured/default editor.

    The scaffolding mode is read from the persisted ``.issueflows/config.toml``
    (or ``ISSUEFLOW_MODE``); ``update`` never changes the mode — switch modes via
    ``issue-flow init --mode <id>``.
    """
    settings = Settings()
    try:
        profiles = resolve_editors(editors)
    except ValueError as exc:
        console.print(f"[red]error[/red]  {exc}")
        raise typer.Exit(code=2) from None

    try:
        mode_obj = settings.resolve_mode(project_root)
    except ValueError as exc:
        console.print(f"[red]error[/red]  {exc}")
        raise typer.Exit(code=2) from None

    console.print(
        f"\n[bold]Updating issue-flow scaffold in [cyan]{project_root}[/cyan][/bold]"
    )
    console.print(
        f"[dim]Editors: {', '.join(p.id for p in profiles)}[/dim]"
    )
    console.print(f"[dim]Mode: {mode_obj.id}[/dim]\n")

    if not _dependency_gate(skip_dep_check):
        raise typer.Exit(code=1)

    _create_issueflow_dirs(project_root, settings)
    _ensure_project_brief(
        project_root,
        settings,
        settings.template_context(project_root, profiles[0], mode=mode_obj),
    )

    written_files: list[Path] = []
    pruned_count = 0
    for profile in profiles:
        console.print(f"\n[bold]{profile.name}[/bold] ([cyan]{profile.agent_dir}[/cyan])")
        context = settings.template_context(project_root, profile, mode=mode_obj)
        written, _skipped = _write_manifest_files(
            project_root, build_manifest(profile, mode_obj), context, force=True
        )
        _ensure_agents_md(project_root, context)
        pruned_count += _prune_retired_files(project_root, profile)
        pruned_count += _prune_excluded_surfaces(project_root, profile, mode_obj)
        written_files.extend(written)

    console.print()
    _graphify_postinstall(project_root, profiles)

    console.print()
    if written_files:
        console.print(
            f"[bold green]Refreshed {len(written_files)} file(s).[/bold green]"
        )
    if pruned_count:
        console.print(
            f"[bold yellow]Pruned {pruned_count} retired scaffold file(s).[/bold yellow]"
        )
    if not written_files and not pruned_count:
        console.print("[bold]Nothing to write.[/bold]")

    console.print(
        "\n[dim]Manifest outputs were overwritten from the installed package. "
        "Issue files under [bold].issueflows/[/bold] were not modified by this command.[/dim]\n"
    )


def _prune_retired_files(
    project_root: Path,
    profile: EditorProfile,
) -> int:
    """Remove generated files retired by scaffold migrations.

    Returns the count of pruned files/folders for user reporting.
    """
    pruned_count = 0

    # Prune command files. For command-emitting profiles this removes pre-v0.5.0
    # command names. For skills-first Cursor, this also removes the known
    # generated issue-flow commands from the old `.cursor/commands/` surface
    # without touching arbitrary user commands.
    if profile.commands_dir:
        pruned_count += _prune_command_files(
            project_root,
            profile.agent_dir,
            profile.commands_dir,
            RETIRED_COMMANDS,
        )
    elif profile.id == "cursor":
        pruned_count += _prune_command_files(
            project_root,
            profile.agent_dir,
            "commands",
            [*COMMAND_NAMES, *RETIRED_COMMANDS],
            remove_empty_dir=True,
        )

    # Prune retired skill folders.
    skills_dir = project_root / profile.agent_dir / "skills"
    for old_skill in RETIRED_SKILLS:
        old_folder = skills_dir / old_skill
        if old_folder.exists():
            import shutil

            shutil.rmtree(old_folder)
            relative = old_folder.relative_to(project_root)
            console.print(f"  [yellow]prune[/yellow]  {relative}")
            pruned_count += 1

    return pruned_count


def _prune_command_files(
    project_root: Path,
    agent_dir: str,
    commands_dir: str,
    command_names: list[str],
    *,
    remove_empty_dir: bool = False,
) -> int:
    """Remove specific generated command files, preserving unrelated commands."""
    pruned_count = 0
    cmd_dir = project_root / agent_dir / commands_dir

    for name in command_names:
        command_file = cmd_dir / f"{name}.md"
        if command_file.exists():
            command_file.unlink()
            relative = command_file.relative_to(project_root)
            console.print(f"  [yellow]prune[/yellow]  {relative}")
            pruned_count += 1

    if remove_empty_dir and cmd_dir.is_dir() and not any(cmd_dir.iterdir()):
        cmd_dir.rmdir()
        relative = cmd_dir.relative_to(project_root)
        console.print(f"  [yellow]prune[/yellow]  {relative}/")
        pruned_count += 1

    return pruned_count


def _prune_excluded_surfaces(
    project_root: Path,
    profile: EditorProfile,
    mode: Mode,
) -> int:
    """Remove generated skills/commands that the active ``mode`` excludes.

    This keeps a narrower mode honest after a mode switch (e.g.
    ``standard`` -> ``simple``) and keeps ``update`` idempotent: any packaged
    surface not in the mode is removed if it was previously scaffolded. Only
    issue-flow's own generated surfaces are touched; user files are left alone.
    """
    pruned_count = 0

    skills_dir = project_root / profile.agent_dir / "skills"
    for skill_dir in SKILL_DIRS:
        if skill_dir in mode.skills:
            continue
        folder = skills_dir / skill_output_name(skill_dir)
        if folder.exists():
            shutil.rmtree(folder)
            console.print(
                f"  [yellow]prune[/yellow]  {folder.relative_to(project_root)}  "
                f"(excluded by mode {mode.id})"
            )
            pruned_count += 1

    if profile.commands_dir:
        cmd_dir = project_root / profile.agent_dir / profile.commands_dir
        for name in COMMAND_NAMES:
            if name in mode.commands:
                continue
            command_file = cmd_dir / f"{name}.md"
            if command_file.exists():
                command_file.unlink()
                console.print(
                    f"  [yellow]prune[/yellow]  "
                    f"{command_file.relative_to(project_root)}  "
                    f"(excluded by mode {mode.id})"
                )
                pruned_count += 1
        if cmd_dir.is_dir() and not any(cmd_dir.iterdir()):
            cmd_dir.rmdir()
            console.print(
                f"  [yellow]prune[/yellow]  {cmd_dir.relative_to(project_root)}/"
            )
            pruned_count += 1

    return pruned_count


def _graphify_postinstall(
    project_root: Path, profiles: list[EditorProfile]
) -> None:
    """Best-effort graphify integration step for ``run_init`` / ``run_update``.

    Auto-detects the ``graphify`` CLI (the user opts in by installing
    ``graphifyy``; there is no flag). Runs ``graphify <installer> install``
    once for each selected editor profile that graphify can register with
    (currently only Cursor). Editors without a graphify installer are skipped.
    When graphify is absent, :func:`register_with_editor` itself prints
    install hints. Never raises and never aborts the parent ``init`` /
    ``update``.
    """
    installable = [p for p in profiles if p.graphify_installer]
    if not installable:
        return

    console.print("[bold]Graphify integration[/bold]")
    seen: set[str] = set()
    for profile in installable:
        installer = profile.graphify_installer
        assert installer is not None  # narrowed by the filter above
        if installer in seen:
            continue
        seen.add(installer)
        graphify_register_with_editor(project_root, console, installer)


def _dependency_gate(skip_dep_check: bool) -> bool:
    """Run the external-CLI dependency check and decide whether to proceed.

    Returns True if ``run_init`` / ``run_update`` should continue, False if
    the user declined the confirmation prompt after seeing a missing-deps
    report.
    """
    missing = check_dependencies()
    return prompt_or_skip(missing, console, skip=skip_dep_check)


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
