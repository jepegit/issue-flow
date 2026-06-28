"""Workflow *modes* for issue-flow scaffolding.

A *mode* selects which workflow surfaces (skills / slash commands) `issue-flow
init` scaffolds into a project. Modes are **data-driven**: the built-in set ships
as the packaged ``modes.toml`` and a project may add or override modes in its own
``.issueflows/config.toml`` using the same ``[modes.<id>]`` grammar. The active
mode for a project is persisted in ``.issueflows/config.toml`` under
``[issueflow].mode`` so ``issue-flow update`` honours it; switching mode is an
``issue-flow init --mode <id>`` action.

This mirrors the :mod:`issue_flow.editors` registry pattern: a small frozen
dataclass plus a resolver. The resolver expands the ``all`` sentinel and the
``extends`` / ``add`` / ``remove`` composition keys into concrete, validated sets
of surface stems.

Surface stems come from :mod:`issue_flow.templating` (``SKILL_DIRS`` underscore
stems, ``COMMAND_NAMES`` hyphen stems). A mode may only reference stems that ship
as packaged templates; unknown stems raise :class:`ValueError`.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import tomlkit

from issue_flow.templating import COMMAND_NAMES, SKILL_DIRS

DEFAULT_MODE = "standard"

# Packaged data file holding the built-in modes (sibling of this module).
_MODES_RESOURCE = "modes.toml"
# Per-project config file (relative to the issueflows dir).
_CONFIG_FILE = "config.toml"

_SKILL_SET: frozenset[str] = frozenset(SKILL_DIRS)
_COMMAND_SET: frozenset[str] = frozenset(COMMAND_NAMES)


@dataclass(frozen=True)
class Mode:
    """A resolved scaffolding mode.

    Attributes:
        id: Stable identifier used by ``--mode`` / ``ISSUEFLOW_MODE`` /
            ``[issueflow].mode``.
        name: Human-readable display name (surfaced to templates as ``mode_name``).
        description: One-line summary.
        skills: Concrete set of skill stems (subset of ``SKILL_DIRS``).
        commands: Concrete set of command stems (subset of ``COMMAND_NAMES``).
    """

    id: str
    name: str
    description: str
    skills: frozenset[str]
    commands: frozenset[str]


def config_path(project_root: Path, issueflows_dir: str) -> Path:
    """Return the path to the project's ``.issueflows/config.toml``."""
    return project_root / issueflows_dir / _CONFIG_FILE


# ---------------------------------------------------------------------------
# Raw table loading (built-in + project overrides)
# ---------------------------------------------------------------------------


def _load_builtin_raw() -> dict[str, dict]:
    """Load the ``[modes.*]`` tables from the packaged ``modes.toml``."""
    ref = resources.files("issue_flow").joinpath(_MODES_RESOURCE)
    data = tomllib.loads(ref.read_text(encoding="utf-8"))
    return dict(data.get("modes", {}))


def _load_project_raw(cfg_path: Path) -> dict[str, dict]:
    """Load any project-defined ``[modes.*]`` tables from ``config.toml``.

    Returns an empty mapping when the file is missing or has no ``[modes]``
    table. Malformed TOML raises (surfaced to the caller as a hard error).
    """
    if not cfg_path.is_file():
        return {}
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    return dict(data.get("modes", {}))


def _merged_raw(cfg_path: Path | None) -> dict[str, dict]:
    """Built-in mode tables overlaid with project-defined ones (project wins)."""
    raw = _load_builtin_raw()
    if cfg_path is not None:
        raw.update(_load_project_raw(cfg_path))
    return raw


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def _expand(value: object, universe: frozenset[str]) -> set[str]:
    """Expand a ``skills``/``commands`` value into a concrete set.

    ``"all"`` (or ``None``) expands to the whole universe; a list is taken
    verbatim (validated later).
    """
    if value is None or value == "all":
        return set(universe)
    if isinstance(value, list):
        return {str(item) for item in value}
    raise ValueError(
        f"mode field must be \"all\" or a list of stems, got {value!r}"
    )


def _route(stems: object) -> tuple[set[str], set[str]]:
    """Split an ``add``/``remove`` stem list into (skill stems, command stems)."""
    if not stems:
        return set(), set()
    if not isinstance(stems, list):
        raise ValueError(f"'add'/'remove' must be a list of stems, got {stems!r}")
    skills = {str(s) for s in stems if s in _SKILL_SET}
    commands = {str(s) for s in stems if s in _COMMAND_SET}
    unknown = {str(s) for s in stems} - skills - commands
    if unknown:
        raise ValueError(
            f"unknown surface stem(s) {sorted(unknown)}; "
            f"valid skills: {sorted(_SKILL_SET)}; valid commands: {sorted(_COMMAND_SET)}"
        )
    return skills, commands


def _resolve_sets(
    mode_id: str,
    raw: dict[str, dict],
    _seen: tuple[str, ...] = (),
) -> tuple[set[str], set[str]]:
    """Resolve a mode's concrete (skills, commands) sets, following ``extends``."""
    if mode_id in _seen:
        chain = " -> ".join((*_seen, mode_id))
        raise ValueError(f"circular mode 'extends' chain: {chain}")
    if mode_id not in raw:
        known = ", ".join(sorted(raw))
        raise ValueError(f"Unknown mode {mode_id!r}. Choose one of: {known}.")

    table = raw[mode_id]

    base_id = table.get("extends")
    if base_id is not None:
        skills, commands = _resolve_sets(str(base_id), raw, (*_seen, mode_id))
    elif "skills" in table or "commands" in table:
        skills = _expand(table.get("skills"), _SKILL_SET)
        commands = _expand(table.get("commands"), _COMMAND_SET)
    else:
        # A mode that only lists add/remove starts from the full set.
        skills, commands = set(_SKILL_SET), set(_COMMAND_SET)

    # An explicit skills/commands list alongside extends replaces the base.
    if base_id is not None:
        if "skills" in table:
            skills = _expand(table.get("skills"), _SKILL_SET)
        if "commands" in table:
            commands = _expand(table.get("commands"), _COMMAND_SET)

    add_skills, add_commands = _route(table.get("add"))
    rem_skills, rem_commands = _route(table.get("remove"))
    skills = (skills | add_skills) - rem_skills
    commands = (commands | add_commands) - rem_commands

    _validate(mode_id, skills, commands)
    return skills, commands


def _validate(mode_id: str, skills: set[str], commands: set[str]) -> None:
    bad_skills = skills - _SKILL_SET
    if bad_skills:
        raise ValueError(
            f"mode {mode_id!r} references unknown skill stem(s) {sorted(bad_skills)}; "
            f"valid skills: {sorted(_SKILL_SET)}"
        )
    bad_commands = commands - _COMMAND_SET
    if bad_commands:
        raise ValueError(
            f"mode {mode_id!r} references unknown command stem(s) {sorted(bad_commands)}; "
            f"valid commands: {sorted(_COMMAND_SET)}"
        )


def available_modes(cfg_path: Path | None = None) -> list[str]:
    """Return the ids of all modes available (built-in + project overrides)."""
    return sorted(_merged_raw(cfg_path))


def resolve_mode(mode_id: str, cfg_path: Path | None = None) -> Mode:
    """Resolve ``mode_id`` into a concrete :class:`Mode`.

    Merges built-in modes with any project ``[modes.*]`` tables found at
    ``cfg_path`` (project wins on id clash). Raises :class:`ValueError` for an
    unknown mode id or a mode referencing unknown surface stems.
    """
    raw = _merged_raw(cfg_path)
    if mode_id not in raw:
        known = ", ".join(sorted(raw))
        raise ValueError(f"Unknown mode {mode_id!r}. Choose one of: {known}.")
    skills, commands = _resolve_sets(mode_id, raw)
    table = raw[mode_id]
    return Mode(
        id=mode_id,
        name=str(table.get("name", mode_id)),
        description=str(table.get("description", "")),
        skills=frozenset(skills),
        commands=frozenset(commands),
    )


# ---------------------------------------------------------------------------
# Active-mode persistence (round-trips user content via tomlkit)
# ---------------------------------------------------------------------------


def read_active_mode(cfg_path: Path) -> str | None:
    """Return the persisted ``[issueflow].mode`` value, or ``None`` if unset."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict):
        value = section.get("mode")
        if value:
            return str(value)
    return None


def read_caveman_default(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].caveman_default`` flag.

    Returns ``None`` when the file is missing or the key is unset, so callers can
    distinguish "not configured" (fall through to env / default) from an explicit
    ``false``.
    """
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "caveman_default" in section:
        return bool(section.get("caveman_default"))
    return None


def write_active_mode(cfg_path: Path, mode_id: str) -> None:
    """Persist ``[issueflow].mode = mode_id`` while preserving other content.

    Creates ``config.toml`` (and parent dirs) when missing; otherwise updates
    only the ``[issueflow].mode`` key, leaving user comments, ``[modes.*]``
    tables, and formatting intact.
    """
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg_path.is_file():
        doc = tomlkit.parse(cfg_path.read_text(encoding="utf-8"))
    else:
        doc = tomlkit.document()
        doc.add(
            tomlkit.comment(
                "issue-flow project config. 'mode' is managed by 'issue-flow init'."
            )
        )

    section = doc.get("issueflow")
    if not isinstance(section, dict):
        section = tomlkit.table()
        doc["issueflow"] = section
    section["mode"] = mode_id

    cfg_path.write_text(tomlkit.dumps(doc), encoding="utf-8")
