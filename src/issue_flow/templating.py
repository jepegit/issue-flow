"""Jinja2 template loading and rendering for issue-flow."""

from __future__ import annotations

import functools
import re
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, BaseLoader, TemplateNotFound

from issue_flow.editors import EDITORS, EditorProfile

if TYPE_CHECKING:
    from issue_flow.modes import Mode

_ISSUE_FLOW_VERSION_KEY = "issue-flow-version"
_SKILL_TEMPLATE_RE = re.compile(r"^skills/[^/]+/SKILL\.md\.j2$")
_NOOB_SKILL_RE = re.compile(r"^skills/iflow_([^/]+)/SKILL\.md\.j2$")
_NOOB_CMD_RE = re.compile(r"^commands/iflow(?:-([^/]+))?\.md\.j2$")
_NOOB_SKIP_STEMS: frozenset[str] = frozenset()


def noob_stem_for_template(template_name: str) -> str | None:
    """Return the lifecycle stem that should get a noob footer, or ``None``."""
    name = template_name.replace("\\", "/")
    match = _NOOB_SKILL_RE.match(name)
    if match:
        stem = match.group(1)
        return None if stem in _NOOB_SKIP_STEMS else stem
    match = _NOOB_CMD_RE.match(name)
    if match:
        stem = (match.group(1) or "iflow").replace("-", "_")
        return None if stem in _NOOB_SKIP_STEMS else stem
    return None


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
    rendered = template.render(context)
    if context.get("noob"):
        stem = noob_stem_for_template(template_name)
        if stem is not None:
            footer = env.get_template("skills/_noob_next.md.j2").render(
                {**context, "noob_stem": stem}
            )
            footer = footer.strip()
            if footer:
                rendered = rendered.rstrip() + "\n\n" + footer + "\n"
    if is_skill_template(template_name):
        version = context.get("issue_flow_version")
        if isinstance(version, str) and version:
            rendered = stamp_skill_version(rendered, version)
    return rendered


def is_skill_template(template_name: str) -> bool:
    """Return True when ``template_name`` is a packaged skill SKILL.md.j2 path."""
    return _SKILL_TEMPLATE_RE.match(template_name.replace("\\", "/")) is not None


def stamp_skill_version(content: str, version: str) -> str:
    """Inject or refresh ``issue-flow-version`` in skill YAML frontmatter."""
    if not content.startswith("---\n"):
        return content.rstrip() + f"\n\n<!-- Scaffolded by issue-flow {version} -->\n"

    closing = content.find("\n---\n", 4)
    if closing == -1:
        return content.rstrip() + f"\n\n<!-- Scaffolded by issue-flow {version} -->\n"

    frontmatter = content[4:closing]
    rest = content[closing:]
    lines = frontmatter.splitlines()
    stamped = False
    new_lines: list[str] = []
    for line in lines:
        if line.startswith(f"{_ISSUE_FLOW_VERSION_KEY}:"):
            new_lines.append(f"{_ISSUE_FLOW_VERSION_KEY}: {version}")
            stamped = True
        else:
            new_lines.append(line)
    if not stamped:
        new_lines.append(f"{_ISSUE_FLOW_VERSION_KEY}: {version}")
    return "---\n" + "\n".join(new_lines) + rest


# ---------------------------------------------------------------------------
# Template surfaces shared by every editor profile.
#
# Output paths may contain ``str.format`` placeholders (``{agent_dir}``,
# ``{commands_dir}``, ``{docs_dir}``) resolved from the render context, so the
# same surface description works for any editor.
# ---------------------------------------------------------------------------

# The lifecycle command surface (issue #406): eleven merged commands, each
# with modes. ``(name, purpose, modes)`` rows feed the always-on rule and the
# workflow doc; the names double as skill folder names and command stems.
COMMANDS: list[tuple[str, str, str]] = [
    ("iflow", "Dispatcher: run the next of capture / plan / build / close.", "—"),
    ("iflow-setup", "Get a project ready (uv, git, GitHub, scaffold).", "`harness`, `check`"),
    ("iflow-pick", "Choose an issue, branch, and capture it.", "`<N>`, `capture`, `fix`, `label:<L>`"),
    ("iflow-plan", "Write the plan and stop for approval.", "—"),
    ("iflow-build", "Implement the approved plan.", "—"),
    ("iflow-pause", "Park unfinished work with resume notes.", "—"),
    ("iflow-close", "Tests, bump, changelog trailers, commit, push, PR.", "`yolo`, `ops`, `draft`, `bump`"),
    ("iflow-cleanup", "After merge: default branch, pull, delete landed branches.", "`all`, `github`, `prs`, `archive`"),
    ("iflow-run", "Hands-off runs under one up-front confirm.", "`yolo`, `cycle`, `auto`, `drive`"),
    ("iflow-issue", "Create and shape GitHub issues.", "`fix`, `epic`, `split`, `review`"),
    ("iflow-status", "Read-only overview of every issue.", "`doctor`, `git`, `graph`"),
]

# Command stems (emitted as thin wrappers only for editors with a commands_dir).
COMMAND_NAMES: list[str] = [name for name, _purpose, _modes in COMMANDS]

# Skill template sub-directories (underscored). Output folder name is the same
# with underscores swapped for hyphens (``iflow_pick`` -> ``iflow-pick``).
# Skills are the portable core and are emitted for every editor. A skill folder
# may hold mode files next to ``SKILL.md`` (progressive disclosure); see
# :func:`skill_side_templates`.
#
# ``DEFAULT_SKILL_DIRS`` is what a mode's ``skills = "all"`` expands to; the
# optional pstack stems below are appended into ``SKILL_DIRS`` (every packaged
# stem) but must be opted into explicitly.
DEFAULT_SKILL_DIRS: list[str] = [
    "iflow_iflow",
    "iflow_setup",
    "iflow_pick",
    "iflow_plan",
    "iflow_build",
    "iflow_pause",
    "iflow_close",
    "iflow_cleanup",
    "iflow_run",
    "iflow_issue",
    "iflow_status",
    # Behavior skill (not a workflow command): a terse "caveman" response style.
    "caveman",
    # Planning skill (not a workflow command): a "grill-me" design interview.
    "grill_me",
]

# Retired skill and command stems (issue #406) mapped to the merged stem that
# absorbed them. ``update`` rewrites old stems in ``config.toml`` with this map,
# and mode / step-profile resolution applies it on read so an old config never
# breaks the CLI.
STEM_RENAMES: dict[str, str] = {
    "iflow_capture": "iflow_pick",
    "iflow_comments": "iflow_pick",
    "iflow_init": "iflow_setup",
    "iflow_ops": "iflow_close",
    "iflow_version_bump": "iflow_close",
    "iflow_history_update": "iflow_close",
    "gh_ci": "iflow_close",
    "iflow_pr_sync": "iflow_cleanup",
    "iflow_archive": "iflow_cleanup",
    "iflow_yolo": "iflow_run",
    "iflow_cycle": "iflow_run",
    "iflow_auto": "iflow_run",
    "iflow_drive": "iflow_run",
    "iflow_fix": "iflow_issue",
    "iflow_epic": "iflow_issue",
    "iflow_split": "iflow_issue",
    "iflow_review": "iflow_issue",
    "iflow_doctor": "iflow_status",
    "iflow_workspace_git": "iflow_status",
    "iflow_graphify": "iflow_status",
}
# Merged skills that did not exist before #406 (every part was a retired skill).
_NEW_PARENT_STEMS = frozenset({"iflow_run"})

COMMAND_RENAMES: dict[str, str] = {
    "iflow-" + old.removeprefix("iflow_").replace("_", "-"): "iflow-"
    + new.removeprefix("iflow_").replace("_", "-")
    for old, new in STEM_RENAMES.items()
    if old.startswith("iflow_")
}


def rename_stem(stem: str) -> str:
    """Map a retired skill or command stem to its merged replacement."""
    return STEM_RENAMES.get(stem) or COMMAND_RENAMES.get(stem) or stem


def rename_removed_stems(stems: list[str]) -> list[str]:
    """Map a mode's ``remove`` list, where a retired stem is only part of a skill.

    Removing a retired stem must not remove more than it used to. When the
    merged skill existed before #406 (``iflow_close`` absorbed ``gh_ci``), the
    stem is dropped: the parent stays. When the merged skill is new
    (``iflow_run``), it is removed only once *every* stem merged into it is
    listed; otherwise the stem is dropped too.
    """
    listed = set(stems)
    renamed: list[str] = []
    for stem in stems:
        new = rename_stem(stem)
        if new == stem:
            if stem not in renamed:
                renamed.append(stem)
            continue
        renames = STEM_RENAMES if stem in STEM_RENAMES else COMMAND_RENAMES
        siblings = {old for old, parent in renames.items() if parent == new}
        is_new_parent = new.replace("-", "_") in _NEW_PARENT_STEMS
        if is_new_parent and siblings <= listed and new not in renamed:
            renamed.append(new)
    return renamed


# Stems that also install into the editor's user-global skill dir
# (placement ``both``). Project copy stays; local wins. See the
# global-vs-local section of ``scaffolding-and-editors.md``. ``iflow_setup`` is
# the one lifecycle exception (it must work before a project scaffold exists).
BOTH_SKILL_STEMS: tuple[str, ...] = ("caveman", "grill_me", "iflow_setup")

# Curated subset of Lauren Tan's (poteto) pstack skills library
# (https://github.com/cursor/plugins/tree/main/pstack, MIT), vendored verbatim
# as ``skills/pstack_<name>/SKILL.md.j2``. Upstream folder names; re-sync with
# ``.issueflows/00-tools/vendor_pstack.py`` (keep its CURATED tuple in step).
PSTACK_SKILL_NAMES: tuple[str, ...] = (
    "unslop",
    "tdd",
    "blast-radius",
    "technical-writing",
    "bro",
    "principle-prove-it-works",
    "principle-subtract-before-you-add",
    "principle-fix-root-causes",
    "principle-test-behavior-not-implementation",
)


def pstack_stem(name: str) -> str:
    """Map an upstream pstack skill name to its template stem (``unslop`` -> ``pstack_unslop``)."""
    return "pstack_" + name.replace("-", "_")


PSTACK_NAME_TO_STEM: dict[str, str] = {
    name: pstack_stem(name) for name in PSTACK_SKILL_NAMES
}

# Optional stems: valid surfaces (custom-mode ``add``, ``pstack_skills``), but
# never part of the ``"all"`` universe, so ``standard`` renders without them.
PSTACK_SKILL_DIRS: list[str] = [
    PSTACK_NAME_TO_STEM[name] for name in PSTACK_SKILL_NAMES
]
OPTIONAL_SKILL_DIRS: list[str] = list(PSTACK_SKILL_DIRS)

# Every packaged skill stem, default and optional, in manifest order.
SKILL_DIRS: list[str] = DEFAULT_SKILL_DIRS + OPTIONAL_SKILL_DIRS

SKILL_OUTPUT_NAMES: dict[str, str] = {
    # Keep the template directory stable while exposing the dispatcher as
    # `/iflow`, not the awkward `/iflow-iflow`, in skills-first editors.
    "iflow_iflow": "iflow",
    # pstack skills keep their upstream folder names so `/unslop`, `/tdd`, ...
    # match pstack's own docs and the `name:` frontmatter.
    **{stem: name for name, stem in PSTACK_NAME_TO_STEM.items()},
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
    # Renamed in #183: iflow-start → iflow-build
    "iflow-start",
    # Merged in #406
    *COMMAND_RENAMES,
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
    # Renamed in #183: iflow-start → iflow-build
    "iflow-start",
    # Merged in #406
    *(old.replace("_", "-") for old in STEM_RENAMES),
]

# Editor-neutral human-readable workflow doc, emitted for every editor.
DOCS_ENTRY: tuple[str, str] = (
    "docs/issue-workflow.md.j2",
    "{docs_dir}/issue-workflow.md",
)


def _selected_skill_dirs(mode: Mode | None) -> list[str]:
    """Skill stems to emit for ``mode`` in manifest order.

    ``mode=None`` keeps the back-compat default surface (``DEFAULT_SKILL_DIRS``);
    optional stems such as the pstack skills are only emitted when the resolved
    mode lists them.
    """
    if mode is None:
        return list(DEFAULT_SKILL_DIRS)
    return [skill_dir for skill_dir in SKILL_DIRS if skill_dir in mode.skills]


COMMAND_WRAPPER_TEMPLATE = "commands/_wrapper.md.j2"


@functools.cache
def skill_side_templates(skill_dir: str) -> tuple[str, ...]:
    """Mode-file template names packaged next to ``skills/<skill_dir>/SKILL.md.j2``.

    Side files (``yolo.md.j2``, ``capture.md.j2``, ...) render to plain markdown
    in the same output folder; a skill's ``SKILL.md`` tells the agent which one
    to read for a given mode, so only that file enters the context.
    """
    try:
        root = resources.files(f"{_TEMPLATES_PACKAGE}.skills.{skill_dir}")
        names = [
            entry.name
            for entry in root.iterdir()
            if entry.name.endswith(".md.j2") and entry.name != "SKILL.md.j2"
        ]
    except (ModuleNotFoundError, FileNotFoundError, NotADirectoryError):
        return ()
    return tuple(sorted(names))


def skill_side_output_names(skill_dir: str) -> frozenset[str]:
    """Rendered file names of a skill's mode files (``yolo.md``, ...)."""
    return frozenset(name.removesuffix(".j2") for name in skill_side_templates(skill_dir))


def side_files_for_output_name(output_name: str) -> frozenset[str]:
    """Mode files that legitimately live in an output skill folder."""
    for stem in SKILL_DIRS:
        if skill_output_name(stem) == output_name:
            return skill_side_output_names(stem)
    return frozenset()


def skill_output_name(skill_dir: str) -> str:
    """Map a skill template stem to its output folder name (underscores->hyphens)."""
    return SKILL_OUTPUT_NAMES.get(skill_dir, skill_dir.replace("_", "-"))


def command_wrapper_context(command_name: str) -> dict[str, str]:
    """Per-file render values for a thin command wrapper (``commands_dir`` editors)."""
    for name, purpose, _modes in COMMANDS:
        if name == command_name:
            return {"command_name": name, "command_description": purpose}
    return {"command_name": command_name, "command_description": command_name}


def _skill_entries(skill_dir: str, base: str) -> list[tuple[str, str]]:
    output_name = skill_output_name(skill_dir)
    entries = [(f"skills/{skill_dir}/SKILL.md.j2", f"{base}/{output_name}/SKILL.md")]
    for name in skill_side_templates(skill_dir):
        entries.append(
            (
                f"skills/{skill_dir}/{name}",
                f"{base}/{output_name}/{name.removesuffix('.j2')}",
            )
        )
    return entries


def build_canonical_manifest(
    mode: Mode | None = None, skill_level: str | None = None
) -> list[tuple[str, str]]:
    """Return skill-only manifest entries under ``.issueflows/agent/skills/``.

    Canonical snapshots use editor-neutral skill bodies (rendered with the codex
    profile context) and omit per-editor rules, commands, and workflow docs.
    """
    entries: list[tuple[str, str]] = []

    for skill_dir in _selected_skill_dirs(mode):
        entries.extend(_skill_entries(skill_dir, "{issueflows_dir}/agent/skills"))

    if skill_level == "advanced":
        entries.append(
            (
                "designs/python-quality-tools.md.j2",
                "{issueflows_dir}/{designs_folder}/python-quality-tools.md",
            )
        )

    return entries


def build_manifest(
    profile: EditorProfile, mode: Mode | None = None, skill_level: str | None = None
) -> list[tuple[str, str]]:
    """Return the ``(template, output_path_template)`` entries for ``profile``.

    When ``mode`` is given, only the command/skill surfaces that mode includes
    are emitted (its ``commands`` / ``skills`` stem sets). ``mode=None`` keeps the
    full set (the back-compat ``standard`` behaviour), so existing call sites and
    tests are unaffected.

    When ``skill_level`` is ``"advanced"``, additional design docs (e.g.
    quality-tooling recommendations) are added to the manifest.

    The per-editor rules extra (``.mdc`` / ``CLAUDE.md``) and the workflow doc are
    always emitted regardless of mode; their *content* adapts via the
    ``included_skills`` membership available in the render context. The always-on
    ``AGENTS.md`` rules file is written separately by the init layer (as a managed
    block) and is intentionally not part of this manifest.
    """
    commands_filter = None if mode is None else mode.commands

    entries: list[tuple[str, str]] = []

    if profile.commands_dir:
        for name in COMMAND_NAMES:
            if commands_filter is not None and name not in commands_filter:
                continue
            entries.append(
                (COMMAND_WRAPPER_TEMPLATE, "{agent_dir}/{commands_dir}/" + f"{name}.md")
            )

    for skill_dir in _selected_skill_dirs(mode):
        entries.extend(_skill_entries(skill_dir, "{agent_dir}/skills"))

    if profile.rules_extra:
        entries.append(profile.rules_extra)

    entries.append(DOCS_ENTRY)

    if skill_level == "advanced":
        entries.append(
            (
                "designs/python-quality-tools.md.j2",
                "{issueflows_dir}/{designs_folder}/python-quality-tools.md",
            )
        )

    return entries


def packaged_skill_output_names() -> frozenset[str]:
    """On-disk folder names for every packaged stem in ``SKILL_DIRS``."""
    return frozenset(skill_output_name(stem) for stem in SKILL_DIRS)


# Backwards-compatible default manifest (Cursor). Kept so existing imports and
# tests that reference ``TEMPLATE_MANIFEST`` continue to work.
TEMPLATE_MANIFEST: list[tuple[str, str]] = build_manifest(EDITORS["cursor"])


def resolve_output_path(path_template: str, context: dict[str, str]) -> Path:
    """Resolve a path template like '{agent_dir}/commands/foo.md' into a Path."""
    return Path(path_template.format(**context))
