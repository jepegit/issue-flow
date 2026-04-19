"""Jinja2 template loading and rendering for issue-flow."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from jinja2 import Environment, BaseLoader, TemplateNotFound


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
# Mapping of template name -> output path (relative to the project root).
# The output path may itself contain Jinja-style placeholders, so we render
# the path first.
# ---------------------------------------------------------------------------

# Each entry: (template_file, output_path_template)
# The output_path_template uses simple str.format with the context dict.
TEMPLATE_MANIFEST: list[tuple[str, str]] = [
    ("commands/issue-init.md.j2", "{agent_dir}/commands/issue-init.md"),
    ("commands/issue-start.md.j2", "{agent_dir}/commands/issue-start.md"),
    ("commands/issue-close.md.j2", "{agent_dir}/commands/issue-close.md"),
    ("rules/issueflow-rules.mdc.j2", "{agent_dir}/rules/issueflow-rules.mdc"),
    ("docs/cursor-issue-workflow.md.j2", "{docs_dir}/cursor-issue-workflow.md"),
    (
        "skills/issueflow_issue_init/SKILL.md.j2",
        "{agent_dir}/skills/issueflow-issue-init/SKILL.md",
    ),
    (
        "skills/issueflow_issue_start/SKILL.md.j2",
        "{agent_dir}/skills/issueflow-issue-start/SKILL.md",
    ),
    (
        "skills/issueflow_issue_close/SKILL.md.j2",
        "{agent_dir}/skills/issueflow-issue-close/SKILL.md",
    ),
    (
        "skills/issueflow_version_bump/SKILL.md.j2",
        "{agent_dir}/skills/issueflow-version-bump/SKILL.md",
    ),
]


def resolve_output_path(path_template: str, context: dict[str, str]) -> Path:
    """Resolve a path template like '{agent_dir}/commands/foo.md' into a Path."""
    return Path(path_template.format(**context))
