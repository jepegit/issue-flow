"""Jinja2 template loading and rendering for issue-flow."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, BaseLoader, TemplateNotFound

from issue_flow.editors import EDITORS, EditorProfile

if TYPE_CHECKING:
    from issue_flow.modes import Mode


# ---------------------------------------------------------------------------
# Custom loader that reads from the package's templates/ directory using
# importlib.resources so it works whether the package is installed as a
# directory, zip, or editable install.
# ---------------------------------------------------------------------------

_TEMPLATES_PACKAGE = "issue_flow.templates"


class _PackageLoader(BaseLoader):
    """Load Jinja2 templates shipped inside the issue_flow.templates package."""

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str, callable]:
        # template is e.g. "commands/issue-init.md.j2"
        parts = template.replace("\\", "/").split("/")
        package = (
            _TEMPLATES_PACKAGE + "." + ".".join(parts[:-1])
            if len(parts) > 1
            else _TEMPLATES_PACKAGE
        )
        filename = parts[-1]

        try:
            ref = resources.files(package).joinpath(filename)
            source = ref.read_text(encoding="utf-8")
        except (ModuleNotFoundError, FileNotFoundError, TypeError) as exc:
            raise TemplateNotFound(template) from exc

        # The third element is a callable that returns True if the template
        # is still up-to-date (always True for packaged templates).
        return source, template, lambda: True


def get_environment() -> Environment:
    """Return a configured Jinja2 environment that loads from the package."""
    env = Environment(
        loader=_PackageLoader(),
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    return env


def render_template(template_name: str, context: dict[str, object]) -> str:
    """Render a single template by name and return the result string."""
    env = get_environment()
    template = env.get_template(template_name)
    return template.render(context)


# ---------------------------------------------------------------------------
# Template surfaces shared by every editor profile.
#
# Output paths may contain ``str.format`` placeholders (``{agent_dir}``,
# ``{commands_dir}``, ``{docs_dir}``) resolved from the render context, so the
# same surface description works for any editor.
# ---------------------------------------------------------------------------

# Slash-command template stems (emitted only for editors with a commands_dir).
COMMAND_NAMES: list[str] = [
    "iflow",
    "iflow-pick",
    "iflow-init",
    "iflow-plan",
    "iflow-start",
    "iflow-pause",
    "iflow-close",
    "iflow-cleanup",
    "iflow-yolo",
    "iflow-fix",
    "iflow-status",
    "iflow-graphify",
]

# Skill template sub-directories (underscored). Output folder name is the same
# with underscores swapped for hyphens (``iflow_iflow`` -> ``iflow-iflow``).
# Skills are the portable core and are emitted for every editor.
SKILL_DIRS: list[str] = [
    "iflow_iflow",
    "iflow_pick",
    "iflow_init",
    "iflow_comments",
    "iflow_plan",
    "iflow_start",
    "iflow_pause",
    "iflow_close",
    "iflow_cleanup",
    "iflow_yolo",
    "iflow_fix",
    "iflow_status",
    "iflow_version_bump",
    "iflow_history_update",
    "iflow_graphify",
    # Behavior skill (not a workflow command): a terse "caveman" response style.
    # Part of the "all"/standard surface; excluded by the explicit "simple" list.
    "caveman",
]

SKILL_OUTPUT_NAMES: dict[str, str] = {
    # Keep the template directory stable while exposing the dispatcher as
    # `/iflow`, not the awkward `/iflow-iflow`, in skills-first editors.
    "iflow_iflow": "iflow",
}

# Retired command names (pre-v0.5.0 rename) to be removed on update.
RETIRED_COMMANDS: list[str] = [
    "issue-pick",
    "issue-init",
    "issue-plan",
    "issue-start",
    "issue-pause",
    "issue-close",
    "issue-cleanup",
    "issue-yolo",
    "issue-fix",
    "issue-status",
    "graphify",
]

# Retired skill folder names (pre-v0.5.0 rename) to be removed on update.
RETIRED_SKILLS: list[str] = [
    "issueflow-issue-pick",
    "issueflow-issue-init",
    "issueflow-issue-comments",
    "issueflow-issue-plan",
    "issueflow-issue-start",
    "issueflow-issue-pause",
    "issueflow-issue-close",
    "issueflow-issue-cleanup",
    "issueflow-issue-yolo",
    "issueflow-issue-fix",
    "issueflow-issue-status",
    "issueflow-version-bump",
    "issueflow-history-update",
    "issueflow-graphify",
    "issueflow-iflow",
    "iflow-iflow",
]

# Editor-neutral human-readable workflow doc, emitted for every editor.
DOCS_ENTRY: tuple[str, str] = (
    "docs/issue-workflow.md.j2",
    "{docs_dir}/issue-workflow.md",
)


def build_manifest(
    profile: EditorProfile, mode: Mode | None = None
) -> list[tuple[str, str]]:
    """Return the ``(template, output_path_template)`` entries for ``profile``.

    When ``mode`` is given, only the command/skill surfaces that mode includes
    are emitted (its ``commands`` / ``skills`` stem sets). ``mode=None`` keeps the
    full set (the back-compat ``standard`` behaviour), so existing call sites and
    tests are unaffected.

    The per-editor rules extra (``.mdc`` / ``CLAUDE.md``) and the workflow doc are
    always emitted regardless of mode; their *content* adapts via the
    ``included_skills`` membership available in the render context. The always-on
    ``AGENTS.md`` rules file is written separately by the init layer (as a managed
    block) and is intentionally not part of this manifest.
    """
    skills_filter = None if mode is None else mode.skills
    commands_filter = None if mode is None else mode.commands

    entries: list[tuple[str, str]] = []

    if profile.commands_dir:
        for name in COMMAND_NAMES:
            if commands_filter is not None and name not in commands_filter:
                continue
            entries.append(
                (f"commands/{name}.md.j2", "{agent_dir}/{commands_dir}/" + f"{name}.md")
            )

    for skill_dir in SKILL_DIRS:
        if skills_filter is not None and skill_dir not in skills_filter:
            continue
        output_name = SKILL_OUTPUT_NAMES.get(skill_dir, skill_dir.replace("_", "-"))
        entries.append(
            (
                f"skills/{skill_dir}/SKILL.md.j2",
                "{agent_dir}/skills/" + f"{output_name}/SKILL.md",
            )
        )

    if profile.rules_extra:
        entries.append(profile.rules_extra)

    entries.append(DOCS_ENTRY)
    return entries


def skill_output_name(skill_dir: str) -> str:
    """Map a skill template stem to its output folder name (underscores->hyphens)."""
    return SKILL_OUTPUT_NAMES.get(skill_dir, skill_dir.replace("_", "-"))


# Backwards-compatible default manifest (Cursor). Kept so existing imports and
# tests that reference ``TEMPLATE_MANIFEST`` continue to work.
TEMPLATE_MANIFEST: list[tuple[str, str]] = build_manifest(EDITORS["cursor"])


def resolve_output_path(path_template: str, context: dict[str, str]) -> Path:
    """Resolve a path template like '{agent_dir}/commands/foo.md' into a Path."""
    return Path(path_template.format(**context))
