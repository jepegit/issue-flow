"""Jinja2 template loading and rendering for issue-flow."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from jinja2 import Environment, BaseLoader, TemplateNotFound

from issue_flow.editors import EDITORS, EditorProfile


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


def render_template(template_name: str, context: dict[str, str]) -> str:
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
    "issue-pick",
    "issue-init",
    "issue-plan",
    "issue-start",
    "issue-pause",
    "issue-close",
    "issue-cleanup",
    "issue-yolo",
    "issue-fix",
    "graphify",
]

# Skill template sub-directories (underscored). Output folder name is the same
# with underscores swapped for hyphens (``issueflow_iflow`` -> ``issueflow-iflow``).
# Skills are the portable core and are emitted for every editor.
SKILL_DIRS: list[str] = [
    "issueflow_iflow",
    "issueflow_issue_pick",
    "issueflow_issue_init",
    "issueflow_issue_comments",
    "issueflow_issue_plan",
    "issueflow_issue_start",
    "issueflow_issue_pause",
    "issueflow_issue_close",
    "issueflow_issue_cleanup",
    "issueflow_issue_yolo",
    "issueflow_issue_fix",
    "issueflow_version_bump",
    "issueflow_history_update",
    "issueflow_graphify",
]

# Editor-neutral human-readable workflow doc, emitted for every editor.
DOCS_ENTRY: tuple[str, str] = (
    "docs/issue-workflow.md.j2",
    "{docs_dir}/issue-workflow.md",
)


def build_manifest(profile: EditorProfile) -> list[tuple[str, str]]:
    """Return the ``(template, output_path_template)`` entries for ``profile``.

    Skills and the workflow doc are always emitted. Slash commands are emitted
    only when the profile defines a ``commands_dir`` (Codex has none). The
    per-editor rules extra (``.mdc`` / ``CLAUDE.md``) is added when present. The
    always-on ``AGENTS.md`` rules file is written separately by the init layer
    (as a managed block) and is intentionally not part of this manifest.
    """
    entries: list[tuple[str, str]] = []

    if profile.commands_dir:
        for name in COMMAND_NAMES:
            entries.append(
                (f"commands/{name}.md.j2", "{agent_dir}/{commands_dir}/" + f"{name}.md")
            )

    for skill_dir in SKILL_DIRS:
        output_name = skill_dir.replace("_", "-")
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


# Backwards-compatible default manifest (Cursor). Kept so existing imports and
# tests that reference ``TEMPLATE_MANIFEST`` continue to work.
TEMPLATE_MANIFEST: list[tuple[str, str]] = build_manifest(EDITORS["cursor"])


def resolve_output_path(path_template: str, context: dict[str, str]) -> Path:
    """Resolve a path template like '{agent_dir}/commands/foo.md' into a Path."""
    return Path(path_template.format(**context))
