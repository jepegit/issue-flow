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

# Skill levels gate complexity-based scaffolding (e.g. quality-tooling docs).
# Ordered low → high. ``advanced`` adds opinionated quality-tooling guidance.
SKILL_LEVELS: tuple[str, ...] = ("basic", "standard", "advanced")
DEFAULT_SKILL_LEVEL = "standard"

# Label-driven flow selection: allowed by default, "yolo" label triggers yolo.
DEFAULT_LABEL_FLOWS = True
DEFAULT_YOLO_LABEL = "yolo"

# Hard wall-clock budget for `gh pr checks --watch` during /iflow-close yolo.
DEFAULT_CHECKS_WATCH_MINUTES = 15

# Step model/execution directives baked into lifecycle skills at render time.
DEFAULT_STEP_DIRECTIVES = True
DEFAULT_MODEL_LABEL_FLOWS = False
DEFAULT_DEEP_MODEL_LABEL = "deep"
DEFAULT_FAST_MODEL_LABEL = "fast"

# Optional managed `.gitattributes` for GitHub Linguist (opt-in; default off).
DEFAULT_LINGUIST_ATTRIBUTES = False

# Skill-behaviour knobs (baked into templates on ``issue-flow update``).
DEFAULT_REMIND_CLEANUP = True
DEFAULT_SUGGEST_GRAPHIFY = True
DEFAULT_AUTO_SWITCHBACK = True
DEFAULT_PR_MERGE_METHOD = "squash"
ALLOWED_PR_MERGE_METHODS = frozenset({"squash", "merge", "rebase"})
DEFAULT_CYCLE_MAX_ISSUES = 10
DEFAULT_AUTO_ADVERSARIAL_LOOPS = 2
DEFAULT_CONFIRM_VERSION_BUMP = False
DEFAULT_RUFF_AUTOFIX = True
DEFAULT_AUTO_CLOSE = False
DEFAULT_EARLY_PR = False
DEFAULT_CONFIRM_CHANGELOG_UPDATE = False

# GitHub sync defaults (``.issueflows/`` folder → labels / milestones).
DEFAULT_SYNC_ENABLED = True
DEFAULT_SYNC_LABEL_PREFIX = "status:"
DEFAULT_SYNC_LABELS = True
DEFAULT_SYNC_MILESTONES = False
DEFAULT_SYNC_CLOSE_ON_SOLVED = False
DEFAULT_SYNC_BOOTSTRAP_LABELS = True
DEFAULT_SYNC_MILESTONE_MAP: dict[str, str] = {
    "current": "",
    "parked": "",
    "solved": "",
}

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
    raise ValueError(f'mode field must be "all" or a list of stems, got {value!r}')


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


def read_grill_me_default(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].grill_me_default`` flag.

    Returns ``None`` when the file is missing or the key is unset, so callers can
    distinguish "not configured" (fall through to env / default) from an explicit
    ``false``.
    """
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "grill_me_default" in section:
        return bool(section.get("grill_me_default"))
    return None


def read_label_flows(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].label_flows`` flag.

    Returns ``None`` when the file is missing or the key is unset, so callers can
    distinguish "not configured" (fall through to env / default) from an explicit
    ``false``.
    """
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "label_flows" in section:
        return bool(section.get("label_flows"))
    return None


def read_linguist_attributes(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].linguist_attributes`` flag.

    Returns ``None`` when the file is missing or the key is unset, so callers can
    distinguish "not configured" (fall through to env / default) from an explicit
    ``false``.
    """
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "linguist_attributes" in section:
        return bool(section.get("linguist_attributes"))
    return None


def read_yolo_label(cfg_path: Path) -> str | None:
    """Return the persisted ``[issueflow].yolo_label`` value, or ``None`` if unset."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict):
        value = section.get("yolo_label")
        if value:
            return str(value)
    return None


def read_checks_watch_minutes(cfg_path: Path) -> int | None:
    """Return persisted ``[issueflow].checks_watch_minutes``, or ``None`` if unset.

    Returns the raw integer when present (including non-positive values) so
    callers can clamp. Non-integer values are treated as unset.
    """
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if not isinstance(section, dict) or "checks_watch_minutes" not in section:
        return None
    value = section.get("checks_watch_minutes")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def read_step_directives(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].step_directives`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "step_directives" in section:
        return bool(section.get("step_directives"))
    return None


def read_model_label_flows(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].model_label_flows`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "model_label_flows" in section:
        return bool(section.get("model_label_flows"))
    return None


def read_deep_model_label(cfg_path: Path) -> str | None:
    """Return the persisted ``[issueflow].deep_model_label`` value."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict):
        value = section.get("deep_model_label")
        if value:
            return str(value)
    return None


def read_fast_model_label(cfg_path: Path) -> str | None:
    """Return the persisted ``[issueflow].fast_model_label`` value."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict):
        value = section.get("fast_model_label")
        if value:
            return str(value)
    return None


def normalize_pr_merge_method(value: str | None) -> str | None:
    """Return a canonical merge method, or ``None`` when unset/invalid."""
    if value is None:
        return None
    cleaned = str(value).strip().lower()
    if cleaned in ALLOWED_PR_MERGE_METHODS:
        return cleaned
    return None


def read_remind_cleanup(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].remind_cleanup`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "remind_cleanup" in section:
        return bool(section.get("remind_cleanup"))
    return None


def read_suggest_graphify(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].suggest_graphify`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "suggest_graphify" in section:
        return bool(section.get("suggest_graphify"))
    return None


def read_auto_switchback(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].auto_switchback`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "auto_switchback" in section:
        return bool(section.get("auto_switchback"))
    return None


def read_pr_merge_method(cfg_path: Path) -> str | None:
    """Return persisted ``[issueflow].pr_merge_method``, or ``None`` if unset/invalid."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict):
        return normalize_pr_merge_method(
            str(section["pr_merge_method"])
            if "pr_merge_method" in section
            and section.get("pr_merge_method") is not None
            else None
        )
    return None


def read_cycle_max_issues(cfg_path: Path) -> int | None:
    """Return persisted ``[issueflow].cycle_max_issues``, or ``None`` if unset.

    Returns the raw integer when present (including non-positive values) so
    callers can clamp. Non-integer values are treated as unset.
    """
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if not isinstance(section, dict) or "cycle_max_issues" not in section:
        return None
    value = section.get("cycle_max_issues")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def read_auto_adversarial_loops(cfg_path: Path) -> int | None:
    """Return persisted ``[issueflow].auto_adversarial_loops``, or ``None``.

    Returns the raw integer when present (including non-positive values) so
    callers can clamp. Non-integer values are treated as unset.
    """
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if not isinstance(section, dict) or "auto_adversarial_loops" not in section:
        return None
    value = section.get("auto_adversarial_loops")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def read_confirm_version_bump(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].confirm_version_bump`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "confirm_version_bump" in section:
        return bool(section.get("confirm_version_bump"))
    return None


def read_ruff_autofix(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].ruff_autofix`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "ruff_autofix" in section:
        return bool(section.get("ruff_autofix"))
    return None


def read_auto_close(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].auto_close`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "auto_close" in section:
        return bool(section.get("auto_close"))
    return None


def read_early_pr(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].early_pr`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "early_pr" in section:
        return bool(section.get("early_pr"))
    return None


def read_confirm_changelog_update(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].confirm_changelog_update`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "confirm_changelog_update" in section:
        return bool(section.get("confirm_changelog_update"))
    return None


def read_sync_settings(cfg_path: Path) -> dict[str, object] | None:
    """Return ``[issueflow.sync]`` from ``config.toml``, or ``None`` if unset."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if not isinstance(section, dict):
        return None
    raw = section.get("sync")
    if not isinstance(raw, dict):
        return None
    return dict(raw)


def read_skill_level(cfg_path: Path) -> str | None:
    """Return the persisted ``[issueflow].skill_level`` value, or ``None`` if unset."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict):
        value = section.get("skill_level")
        if value:
            return str(value)
    return None


def read_canonical_format(cfg_path: Path) -> bool | None:
    """Return the persisted ``[issueflow].canonical_format`` flag."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict) and "canonical_format" in section:
        return bool(section.get("canonical_format"))
    return None


def read_persisted_editor(cfg_path: Path) -> str | None:
    """Return the persisted ``[issueflow].editor`` value."""
    if not cfg_path.is_file():
        return None
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if isinstance(section, dict):
        value = section.get("editor")
        if value:
            return str(value)
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


def write_skill_level(cfg_path: Path, skill_level: str) -> None:
    """Persist ``[issueflow].skill_level`` while preserving other content.

    Creates ``config.toml`` (and parent dirs) when missing; otherwise updates
    only the ``[issueflow].skill_level`` key, leaving user comments and
    formatting intact.
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
    section["skill_level"] = skill_level

    cfg_path.write_text(tomlkit.dumps(doc), encoding="utf-8")


def write_canonical_format(cfg_path: Path, enabled: bool) -> None:
    """Persist ``[issueflow].canonical_format`` while preserving other content."""
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg_path.is_file():
        doc = tomlkit.parse(cfg_path.read_text(encoding="utf-8"))
    else:
        doc = tomlkit.document()

    section = doc.get("issueflow")
    if not isinstance(section, dict):
        section = tomlkit.table()
        doc["issueflow"] = section
    section["canonical_format"] = enabled
    cfg_path.write_text(tomlkit.dumps(doc), encoding="utf-8")


def write_persisted_editor(cfg_path: Path, editor_id: str) -> None:
    """Persist ``[issueflow].editor`` while preserving other content."""
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg_path.is_file():
        doc = tomlkit.parse(cfg_path.read_text(encoding="utf-8"))
    else:
        doc = tomlkit.document()

    section = doc.get("issueflow")
    if not isinstance(section, dict):
        section = tomlkit.table()
        doc["issueflow"] = section
    section["editor"] = editor_id
    cfg_path.write_text(tomlkit.dumps(doc), encoding="utf-8")


def write_default_config(
    cfg_path: Path,
    *,
    mode: str,
    skill_level: str,
    caveman_default: bool,
    grill_me_default: bool,
    label_flows: bool = DEFAULT_LABEL_FLOWS,
    yolo_label: str = DEFAULT_YOLO_LABEL,
    checks_watch_minutes: int = DEFAULT_CHECKS_WATCH_MINUTES,
    step_directives: bool = DEFAULT_STEP_DIRECTIVES,
    model_label_flows: bool = DEFAULT_MODEL_LABEL_FLOWS,
    deep_model_label: str = DEFAULT_DEEP_MODEL_LABEL,
    fast_model_label: str = DEFAULT_FAST_MODEL_LABEL,
    linguist_attributes: bool = DEFAULT_LINGUIST_ATTRIBUTES,
    remind_cleanup: bool = DEFAULT_REMIND_CLEANUP,
    suggest_graphify: bool = DEFAULT_SUGGEST_GRAPHIFY,
    auto_switchback: bool = DEFAULT_AUTO_SWITCHBACK,
    pr_merge_method: str = DEFAULT_PR_MERGE_METHOD,
    cycle_max_issues: int = DEFAULT_CYCLE_MAX_ISSUES,
    auto_adversarial_loops: int = DEFAULT_AUTO_ADVERSARIAL_LOOPS,
    confirm_version_bump: bool = DEFAULT_CONFIRM_VERSION_BUMP,
    ruff_autofix: bool = DEFAULT_RUFF_AUTOFIX,
    auto_close: bool = DEFAULT_AUTO_CLOSE,
    early_pr: bool = DEFAULT_EARLY_PR,
    confirm_changelog_update: bool = DEFAULT_CONFIRM_CHANGELOG_UPDATE,
    overwrite: bool = False,
) -> bool:
    """Create (or, with ``overwrite``, refresh) the project's ``config.toml``.

    Writes the ``[issueflow]`` keys issue-flow reads from ``config.toml`` using
    the supplied values. Other ``ISSUEFLOW_*`` settings are env-only and are
    deliberately not written here.

    Behaviour:

    - File missing → create it with a commented ``[issueflow]`` table.
    - File present and ``overwrite`` is ``False`` → write nothing, return ``False``.
    - File present and ``overwrite`` is ``True`` → upsert the keys via tomlkit,
      leaving user comments, ``[modes.*]`` / ``[issueflow.step_profiles]``
      tables, and formatting intact.

    Returns ``True`` when the file was written, ``False`` when it already existed
    and ``overwrite`` was not set.
    """
    existed = cfg_path.is_file()
    if existed and not overwrite:
        return False

    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if existed:
        doc = tomlkit.parse(cfg_path.read_text(encoding="utf-8"))
        section = doc.get("issueflow")
        if not isinstance(section, dict):
            section = tomlkit.table()
            doc["issueflow"] = section
        section["mode"] = mode
        section["skill_level"] = skill_level
        section["caveman_default"] = caveman_default
        section["grill_me_default"] = grill_me_default
        section["label_flows"] = label_flows
        section["yolo_label"] = yolo_label
        section["checks_watch_minutes"] = checks_watch_minutes
        section["step_directives"] = step_directives
        section["model_label_flows"] = model_label_flows
        section["deep_model_label"] = deep_model_label
        section["fast_model_label"] = fast_model_label
        section["linguist_attributes"] = linguist_attributes
        section["remind_cleanup"] = remind_cleanup
        section["suggest_graphify"] = suggest_graphify
        section["auto_switchback"] = auto_switchback
        section["pr_merge_method"] = pr_merge_method
        section["cycle_max_issues"] = cycle_max_issues
        section["auto_adversarial_loops"] = auto_adversarial_loops
        section["confirm_version_bump"] = confirm_version_bump
        section["ruff_autofix"] = ruff_autofix
        section["auto_close"] = auto_close
        section["early_pr"] = early_pr
        section["confirm_changelog_update"] = confirm_changelog_update
    else:
        doc = tomlkit.document()
        doc.add(
            tomlkit.comment(
                "issue-flow project config. Created by 'issue-flow config add'."
            )
        )
        doc.add(
            tomlkit.comment(
                "Only these keys are read from config.toml; other ISSUEFLOW_* "
                "settings are environment-only (see 'issue-flow config add --help')."
            )
        )
        doc["issueflow"] = _commented_issueflow_table(
            mode,
            skill_level,
            caveman_default,
            grill_me_default,
            label_flows,
            yolo_label,
            checks_watch_minutes,
            step_directives,
            model_label_flows,
            deep_model_label,
            fast_model_label,
            linguist_attributes,
            remind_cleanup,
            suggest_graphify,
            auto_switchback,
            pr_merge_method,
            cycle_max_issues,
            auto_adversarial_loops,
            confirm_version_bump,
            ruff_autofix,
            auto_close,
            early_pr,
            confirm_changelog_update,
        )

    cfg_path.write_text(tomlkit.dumps(doc), encoding="utf-8")
    return True


def _commented_issueflow_table(
    mode: str,
    skill_level: str,
    caveman_default: bool,
    grill_me_default: bool,
    label_flows: bool,
    yolo_label: str,
    checks_watch_minutes: int,
    step_directives: bool,
    model_label_flows: bool,
    deep_model_label: str,
    fast_model_label: str,
    linguist_attributes: bool,
    remind_cleanup: bool,
    suggest_graphify: bool,
    auto_switchback: bool,
    pr_merge_method: str,
    cycle_max_issues: int,
    auto_adversarial_loops: int,
    confirm_version_bump: bool,
    ruff_autofix: bool,
    auto_close: bool,
    early_pr: bool,
    confirm_changelog_update: bool,
) -> tomlkit.items.Table:
    """Build a fresh ``[issueflow]`` table with explanatory comments per key."""
    table = tomlkit.table()
    table.add(
        tomlkit.comment(
            "Scaffolding mode: 'standard' (full workflow) or 'simple' "
            "(markdown-only). Switch by re-running 'issue-flow init --mode <id>'."
        )
    )
    table["mode"] = mode
    table.add(tomlkit.nl())
    table.add(
        tomlkit.comment(
            "Skill level: 'basic' (minimal), 'standard', 'advanced' (opinionated "
            "quality tooling). Switch by re-running 'issue-flow init --skill-level <id>'."
        )
    )
    table["skill_level"] = skill_level
    table.add(tomlkit.nl())
    table.add(
        tomlkit.comment(
            "Reply in the terse caveman style by default (true/false). "
            "Re-run 'issue-flow update' after changing so the rule re-renders."
        )
    )
    table["caveman_default"] = caveman_default
    table.add(tomlkit.nl())
    table.add(
        tomlkit.comment(
            "Run the grill-me planning interview by default (true/false). "
            "Re-run 'issue-flow update' after changing so the rule re-renders."
        )
    )
    table["grill_me_default"] = grill_me_default
    table.add(tomlkit.nl())
    table.add(
        tomlkit.comment(
            "Let issue labels select the flow (true/false): an issue carrying "
            "the yolo label is run through /iflow-yolo when picked. Re-run "
            "'issue-flow update' after changing so the commands re-render."
        )
    )
    table["label_flows"] = label_flows
    table.add(tomlkit.comment("The GitHub label that triggers the yolo flow."))
    table["yolo_label"] = yolo_label
    table.add(tomlkit.nl())
    table.add(
        tomlkit.comment(
            "Hard wall-clock budget (minutes) for `gh pr checks --watch` during "
            "/iflow-close yolo when checks are pending. Re-run 'issue-flow update' "
            "after changing so close/yolo skills re-render with the new budget."
        )
    )
    table["checks_watch_minutes"] = checks_watch_minutes
    table.add(tomlkit.nl())
    table.add(
        tomlkit.comment(
            "Bake MODEL & EXECUTION DIRECTIVE sections into lifecycle skills "
            "(true/false). Re-run 'issue-flow update' after changing."
        )
    )
    table["step_directives"] = step_directives
    table.add(tomlkit.nl())
    table.add(
        tomlkit.comment(
            "Let issue labels hint the session profile during /iflow-pick "
            "(true/false). Uses deep_model_label / fast_model_label below."
        )
    )
    table["model_label_flows"] = model_label_flows
    table.add(
        tomlkit.comment(
            "GitHub labels that bump the session toward reasoning or economy."
        )
    )
    table["deep_model_label"] = deep_model_label
    table["fast_model_label"] = fast_model_label
    table.add(tomlkit.nl())
    table.add(
        tomlkit.comment(
            "Write a managed .gitattributes block that keeps GitHub Linguist "
            "focused on library source (true/false; default false / opt-in). "
            "Re-run 'issue-flow update' after enabling."
        )
    )
    table["linguist_attributes"] = linguist_attributes
    table.add(tomlkit.nl())
    table.add(
        tomlkit.comment(
            "Remind the user to run /iflow-cleanup after close / cycle "
            "(true/false). Re-run 'issue-flow update' after changing."
        )
    )
    table["remind_cleanup"] = remind_cleanup
    table.add(
        tomlkit.comment(
            "Soft-suggest skimming GRAPH_REPORT.md / rebuilding graphify "
            "(true/false). Never auto-runs graphify. Re-run 'issue-flow update'."
        )
    )
    table["suggest_graphify"] = suggest_graphify
    table.add(
        tomlkit.comment(
            "After /iflow-close opens a PR, switch back to the default branch "
            "when the tree is clean (true/false). false ≈ always 'stay'."
        )
    )
    table["auto_switchback"] = auto_switchback
    table.add(
        tomlkit.comment(
            "gh pr merge method for yolo close: 'squash', 'merge', or 'rebase'."
        )
    )
    table["pr_merge_method"] = pr_merge_method
    table.add(
        tomlkit.comment(
            "Default /iflow-cycle queue safety cap (raise per run with max:<n>)."
        )
    )
    table["cycle_max_issues"] = cycle_max_issues
    table.add(
        tomlkit.comment(
            "Default /iflow-auto inter-epoch adversarial loop budget "
            "(override per run with loops:<n>). Re-run 'issue-flow update'."
        )
    )
    table["auto_adversarial_loops"] = auto_adversarial_loops
    table.add(
        tomlkit.comment(
            "When true, /iflow-build (and /iflow-fix end) chain into "
            "/iflow-close automatically once work is ready to ship "
            "(default false). Close keeps its own confirms."
        )
    )
    table["auto_close"] = auto_close
    table.add(
        tomlkit.comment(
            "When true, /iflow-build opens a draft PR after the first push "
            "(default false). Trailing early/pr force on; noearly forces off. "
            "Re-run 'issue-flow update' after changing."
        )
    )
    table["early_pr"] = early_pr
    table.add(
        tomlkit.comment(
            "When true, non-yolo /iflow-close confirms once about a version "
            "bump if the user did not pass a bump token (default false)."
        )
    )
    table["confirm_version_bump"] = confirm_version_bump
    table.add(
        tomlkit.comment(
            "When true, /iflow-close shows the changelog diff and confirms "
            "once before writing (default false). false = write without "
            "asking so the bullet lands in the PR (same as yolo's history "
            "behaviour). nohistory still skips."
        )
    )
    table["confirm_changelog_update"] = confirm_changelog_update
    table.add(
        tomlkit.comment(
            "When ruff is present, run ruff check --fix + ruff format from "
            "/iflow-build and /iflow-close (true/false)."
        )
    )
    table["ruff_autofix"] = ruff_autofix
    return table
