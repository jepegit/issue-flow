"""Editor profiles for issue-flow's multi-tool scaffolding.

issue-flow renders the same template set for several AI coding tools. The only
things that differ per tool are *where* files land (the agent directory and the
slash-commands sub-directory), *which* surfaces a tool supports (slash commands
vs skills vs rules files), and whether graphify can be auto-registered with it.

An :class:`EditorProfile` captures exactly those differences; everything else
(the template bodies, the ``.issueflows/`` tree, skills) is shared. Skills are
the portable core — all four tools read ``<agent_dir>/skills/<name>/SKILL.md`` —
and ``AGENTS.md`` is the convergent rules target, so every profile emits both.
Slash commands and the per-editor rules extra (``.mdc`` / ``CLAUDE.md``) are
niceties layered on top.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EditorProfile:
    """How issue-flow should scaffold itself for one AI coding tool.

    Attributes:
        id: Stable identifier used by ``--editor`` and ``ISSUEFLOW_EDITOR``.
        name: Human-readable display name, surfaced in templates as
            ``editor_name``.
        agent_dir: The tool's config directory (e.g. ``.cursor``), unless the
            user overrides it with ``ISSUEFLOW_AGENT_DIR``.
        commands_dir: Sub-directory of ``agent_dir`` for slash commands, or
            ``None`` for tools without project slash commands (Codex CLI).
        rules_extra: Optional ``(template_name, output_path_template)`` for a
            tool-specific rules file in addition to the always-emitted
            ``AGENTS.md`` (``.mdc`` for Cursor, ``CLAUDE.md`` for Claude).
        graphify_installer: graphify ``<installer> install`` sub-command name
            for editors graphify can register with (``"cursor"``), else
            ``None`` to skip graphify registration entirely.
    """

    id: str
    name: str
    agent_dir: str
    commands_dir: str | None
    rules_extra: tuple[str, str] | None
    graphify_installer: str | None


# Registry of supported editors. ``cursor`` is first / default so existing
# installs are unchanged when no ``--editor`` is given.
EDITORS: dict[str, EditorProfile] = {
    "cursor": EditorProfile(
        id="cursor",
        name="Cursor",
        agent_dir=".cursor",
        commands_dir="commands",
        rules_extra=(
            "rules/issueflow-rules.mdc.j2",
            "{agent_dir}/rules/issueflow-rules.mdc",
        ),
        graphify_installer="cursor",
    ),
    "claude": EditorProfile(
        id="claude",
        name="Claude Code",
        agent_dir=".claude",
        commands_dir="commands",
        rules_extra=("rules/CLAUDE.md.j2", "CLAUDE.md"),
        graphify_installer=None,
    ),
    "opencode": EditorProfile(
        id="opencode",
        name="opencode",
        agent_dir=".opencode",
        # opencode accepts singular ``command/`` or plural ``commands/``; we
        # emit the singular form opencode documents as canonical.
        commands_dir="command",
        rules_extra=None,
        graphify_installer=None,
    ),
    "codex": EditorProfile(
        id="codex",
        name="Codex",
        agent_dir=".codex",
        # Codex CLI removed project-scoped slash commands in v0.117.0; users
        # invoke the mirrored skills instead. So: skills + AGENTS.md only.
        commands_dir=None,
        rules_extra=None,
        graphify_installer=None,
    ),
}

DEFAULT_EDITOR = "cursor"


def get_profile(editor_id: str) -> EditorProfile:
    """Return the :class:`EditorProfile` for ``editor_id``.

    Raises:
        ValueError: if ``editor_id`` is not a known editor.
    """
    try:
        return EDITORS[editor_id]
    except KeyError:
        known = ", ".join(sorted(EDITORS))
        raise ValueError(
            f"Unknown editor {editor_id!r}. Choose one of: {known} (or 'all')."
        ) from None


def resolve_editors(selected: list[str] | None) -> list[EditorProfile]:
    """Resolve a raw ``--editor`` selection into ordered, de-duplicated profiles.

    Accepts the literal ``"all"`` (expands to every registered editor in
    registry order), and de-duplicates while preserving first-seen order.
    ``None`` or an empty selection falls back to the default editor.

    Raises:
        ValueError: if any entry is neither ``"all"`` nor a known editor id.
    """
    if not selected:
        return [get_profile(DEFAULT_EDITOR)]

    ids: list[str] = []
    for raw in selected:
        entry = raw.strip().lower()
        if entry == "all":
            ids.extend(EDITORS.keys())
        else:
            # Validate eagerly so a typo fails fast with a helpful message.
            get_profile(entry)
            ids.append(entry)

    seen: set[str] = set()
    ordered: list[EditorProfile] = []
    for editor_id in ids:
        if editor_id not in seen:
            seen.add(editor_id)
            ordered.append(get_profile(editor_id))
    return ordered
