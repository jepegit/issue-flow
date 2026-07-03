"""Step execution profiles for issue-flow lifecycle skills.

Each lifecycle skill maps to ``economy`` (prioritize speed and token economy)
or ``reasoning`` (prioritize deep thinking). Packaged defaults ship in
``step_profiles.toml``; projects may override stems in
``.issueflows/config.toml`` under ``[issueflow.step_profiles]``.
"""

from __future__ import annotations

import re
import tomllib
from importlib import resources
from typing import Literal

from issue_flow.templating import COMMAND_NAMES, SKILL_DIRS

StepProfile = Literal["economy", "reasoning"]

_PROFILES_RESOURCE = "step_profiles.toml"
_VALID_PROFILES: frozenset[str] = frozenset({"economy", "reasoning"})

# Lifecycle skills that receive a MODEL & EXECUTION DIRECTIVE (excludes caveman/grill_me).
LIFECYCLE_SKILL_STEMS: frozenset[str] = frozenset(
    stem for stem in SKILL_DIRS if stem not in {"caveman", "grill_me"}
)

_COMMAND_TO_SKILL: dict[str, str] = {
    "iflow": "iflow_iflow",
    **{name: name.replace("-", "_") for name in COMMAND_NAMES if name != "iflow"},
}


def _load_packaged_defaults() -> dict[str, StepProfile]:
    ref = resources.files("issue_flow").joinpath(_PROFILES_RESOURCE)
    data = tomllib.loads(ref.read_text(encoding="utf-8"))
    raw = data.get("defaults", {})
    result: dict[str, StepProfile] = {}
    for stem, value in raw.items():
        profile = str(value).strip().lower()
        if profile not in _VALID_PROFILES:
            raise ValueError(
                f"Invalid step profile {profile!r} for {stem!r} in {_PROFILES_RESOURCE}"
            )
        if stem not in LIFECYCLE_SKILL_STEMS:
            raise ValueError(f"Unknown skill stem {stem!r} in {_PROFILES_RESOURCE}")
        result[stem] = profile  # type: ignore[assignment]
    missing = LIFECYCLE_SKILL_STEMS - set(result)
    if missing:
        raise ValueError(
            f"{_PROFILES_RESOURCE} is missing defaults for: {sorted(missing)}"
        )
    return result


PACKAGED_DEFAULTS: dict[str, StepProfile] = _load_packaged_defaults()


def read_project_overrides(cfg_path) -> dict[str, StepProfile]:
    """Return ``[issueflow.step_profiles]`` overrides from ``config.toml``."""
    from pathlib import Path

    path = Path(cfg_path)
    if not path.is_file():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if not isinstance(section, dict):
        return {}
    raw = section.get("step_profiles")
    if not isinstance(raw, dict):
        return {}
    overrides: dict[str, StepProfile] = {}
    for stem, value in raw.items():
        profile = str(value).strip().lower()
        if profile not in _VALID_PROFILES:
            raise ValueError(f"Invalid step profile {profile!r} for {stem!r} in {path}")
        if stem not in LIFECYCLE_SKILL_STEMS:
            raise ValueError(
                f"Unknown skill stem {stem!r} in [issueflow.step_profiles] ({path})"
            )
        overrides[stem] = profile  # type: ignore[assignment]
    return overrides


def resolve_all(cfg_path) -> dict[str, StepProfile]:
    """Merge packaged defaults with project overrides (project wins)."""
    merged = dict(PACKAGED_DEFAULTS)
    merged.update(read_project_overrides(cfg_path))
    return merged


def resolve_for_stem(cfg_path, stem: str) -> StepProfile | None:
    """Return the profile for ``stem``, or ``None`` when not a lifecycle skill."""
    if stem not in LIFECYCLE_SKILL_STEMS:
        return None
    return resolve_all(cfg_path)[stem]


def skill_stem_for_template(template_name: str) -> str | None:
    """Map a manifest template path to a lifecycle skill stem, if any."""
    if template_name.startswith("skills/") and template_name.endswith("/SKILL.md.j2"):
        stem = template_name.removeprefix("skills/").removesuffix("/SKILL.md.j2")
        if stem in LIFECYCLE_SKILL_STEMS:
            return stem
        return None
    match = re.fullmatch(r"commands/(.+)\.md\.j2", template_name)
    if match:
        command = match.group(1)
        stem = _COMMAND_TO_SKILL.get(command)
        if stem in LIFECYCLE_SKILL_STEMS:
            return stem
    return None


def enrich_render_context(
    context: dict[str, object], template_name: str
) -> dict[str, object]:
    """Copy ``context`` and set ``step_profile`` when rendering a lifecycle surface."""
    render_context = dict(context)
    stem = skill_stem_for_template(template_name)
    if stem is not None:
        profiles = context.get("step_profiles")
        if isinstance(profiles, dict) and stem in profiles:
            render_context["step_profile"] = profiles[stem]
    return render_context
