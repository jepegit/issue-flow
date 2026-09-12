"""CLI helpers for viewing and editing ``.issueflows/config.toml``.

Owns the set of ``[issueflow]`` keys ``issue-flow config show|set|edit`` may
touch, value parsing, and tomlkit upserts. Resolution of effective values still
lives on :class:`issue_flow.config.Settings`.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import tomlkit
from tomlkit.items import Item

from issue_flow.modes import (
    ALLOWED_ESSENTIAL_REVIEWS,
    ALLOWED_PR_MERGE_METHODS,
    ALLOWED_TEST_RUNNERS,
    normalize_essential_review,
    normalize_pr_merge_method,
    normalize_pstack_skills,
    normalize_test_runner,
)

ConfigValueKind = Literal["bool", "int", "str", "str_list", "enum"]


@dataclass(frozen=True)
class ConfigKeySpec:
    """One ``[issueflow]`` key that ``config set`` / ``show`` may touch."""

    kind: ConfigValueKind
    allowed: frozenset[str] | None = None
    # When true, changing the key only takes effect in scaffolded skills/rules
    # after ``issue-flow update``.
    needs_update: bool = True


# Keys accepted by ``write_default_config`` / ``seed_config_values``. Keep in
# sync when adding knobs.
CONFIG_KEYS: dict[str, ConfigKeySpec] = {
    "mode": ConfigKeySpec("str", needs_update=True),
    "skill_level": ConfigKeySpec("str", needs_update=True),
    "caveman_default": ConfigKeySpec("bool"),
    "grill_me_default": ConfigKeySpec("bool"),
    "label_flows": ConfigKeySpec("bool"),
    "yolo_label": ConfigKeySpec("str"),
    "ops_label": ConfigKeySpec("str"),
    "checks_watch_minutes": ConfigKeySpec("int"),
    "step_directives": ConfigKeySpec("bool"),
    "model_label_flows": ConfigKeySpec("bool"),
    "deep_model_label": ConfigKeySpec("str"),
    "fast_model_label": ConfigKeySpec("str"),
    "linguist_attributes": ConfigKeySpec("bool", needs_update=True),
    "remind_cleanup": ConfigKeySpec("bool"),
    "cleanup_include_github": ConfigKeySpec("bool"),
    "suggest_graphify": ConfigKeySpec("bool"),
    "auto_graphify_on_plan": ConfigKeySpec("bool"),
    "auto_switchback": ConfigKeySpec("bool"),
    "pr_merge_method": ConfigKeySpec("enum", ALLOWED_PR_MERGE_METHODS),
    "cycle_max_issues": ConfigKeySpec("int", needs_update=False),
    "auto_adversarial_loops": ConfigKeySpec("int"),
    "confirm_version_bump": ConfigKeySpec("bool"),
    "ruff_autofix": ConfigKeySpec("bool"),
    "auto_close": ConfigKeySpec("bool"),
    "auto_plan": ConfigKeySpec("bool"),
    "auto_build": ConfigKeySpec("bool"),
    "early_pr": ConfigKeySpec("bool"),
    "fix_auto_name": ConfigKeySpec("bool"),
    "confirm_changelog_update": ConfigKeySpec("bool"),
    "essential_tests": ConfigKeySpec("bool"),
    "test_runner": ConfigKeySpec("enum", ALLOWED_TEST_RUNNERS),
    "essential_marker": ConfigKeySpec("str"),
    "essential_review": ConfigKeySpec("enum", ALLOWED_ESSENTIAL_REVIEWS),
    "pstack_skills": ConfigKeySpec("str_list"),
}


_TRUE = frozenset({"1", "true", "yes", "on"})
_FALSE = frozenset({"0", "false", "no", "off"})


def known_config_keys() -> list[str]:
    """Sorted list of keys ``config set`` accepts."""
    return sorted(CONFIG_KEYS)


def parse_config_value(key: str, raw: str) -> Any:
    """Parse a CLI string into a typed value for ``key``.

    Raises :class:`ValueError` with a short human message on bad input or an
    unknown key.
    """
    spec = CONFIG_KEYS.get(key)
    if spec is None:
        known = ", ".join(known_config_keys())
        raise ValueError(f"unknown key {key!r}; known keys: {known}")

    text = raw.strip()
    if spec.kind == "bool":
        low = text.lower()
        if low in _TRUE:
            return True
        if low in _FALSE:
            return False
        raise ValueError(f"{key} expects a boolean (true/false), got {raw!r}")

    if spec.kind == "int":
        try:
            value = int(text, 10)
        except ValueError as exc:
            raise ValueError(f"{key} expects an integer, got {raw!r}") from exc
        if value <= 0 and key in {
            "checks_watch_minutes",
            "cycle_max_issues",
            "auto_adversarial_loops",
        }:
            raise ValueError(f"{key} must be a positive integer, got {value}")
        return value

    if spec.kind == "str_list":
        if text.lower() in {"", "[]", "none", "null"}:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{key} expects a JSON array or comma-separated list"
                ) from exc
            if not isinstance(parsed, list):
                raise ValueError(f"{key} expects a JSON array of strings")
            return normalize_pstack_skills(parsed)
        if text.lower() == "all":
            return normalize_pstack_skills("all")
        parts = [p.strip() for p in text.split(",") if p.strip()]
        return normalize_pstack_skills(parts)

    if spec.kind == "enum":
        if key == "pr_merge_method":
            normalized = normalize_pr_merge_method(text)
        elif key == "test_runner":
            normalized = normalize_test_runner(text)
        elif key == "essential_review":
            normalized = normalize_essential_review(text)
        else:
            normalized = text.strip().lower() if text.strip() else None
        allowed = spec.allowed or frozenset()
        if normalized is None or normalized not in allowed:
            choices = ", ".join(sorted(allowed))
            raise ValueError(f"{key} must be one of: {choices}")
        return normalized

    # str
    if not text:
        raise ValueError(f"{key} expects a non-empty string")
    return text


def read_persisted_section(cfg_path: Path) -> dict[str, Any] | None:
    """Return the raw ``[issueflow]`` table, or ``None`` if missing/unset."""
    if not cfg_path.is_file():
        return None
    data = tomlkit.loads(cfg_path.read_text(encoding="utf-8"))
    section = data.get("issueflow")
    if not isinstance(section, dict):
        return None
    return {str(k): _plain_toml_value(v) for k, v in section.items()}


def _plain_toml_value(value: Any) -> Any:
    if isinstance(value, Item):
        return value.unwrap()
    if isinstance(value, list):
        return [_plain_toml_value(v) for v in value]
    return value


def upsert_config_value(cfg_path: Path, key: str, value: Any) -> None:
    """Write ``[issueflow].key = value``, creating the file/section if needed."""
    if key not in CONFIG_KEYS:
        known = ", ".join(known_config_keys())
        raise ValueError(f"unknown key {key!r}; known keys: {known}")

    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg_path.is_file():
        doc = tomlkit.parse(cfg_path.read_text(encoding="utf-8"))
    else:
        doc = tomlkit.document()
        doc.add(
            tomlkit.comment(
                "issue-flow project config. Created by 'issue-flow config set'."
            )
        )

    section = doc.get("issueflow")
    if not isinstance(section, dict):
        section = tomlkit.table()
        doc["issueflow"] = section

    if isinstance(value, list):
        section[key] = list(value)
    else:
        section[key] = value

    cfg_path.write_text(tomlkit.dumps(doc), encoding="utf-8")


def resolve_text_editor(explicit: str | None = None) -> list[str]:
    """Resolve an argv for opening a text file (``$VISUAL`` / ``$EDITOR``).

    Preference: explicit ``--editor`` string > ``VISUAL`` > ``EDITOR`` >
    ``nano`` > ``vi``. Raises :class:`RuntimeError` when nothing usable is found.
    """
    candidates: list[str] = []
    if explicit and explicit.strip():
        candidates.append(explicit.strip())
    for env_name in ("VISUAL", "EDITOR"):
        raw = os.getenv(env_name)
        if raw and raw.strip():
            candidates.append(raw.strip())
    candidates.extend(["nano", "vi"])

    for raw in candidates:
        parts = shlex.split(raw)
        if not parts:
            continue
        binary = parts[0]
        if shutil.which(binary) or Path(binary).is_file():
            return parts
    raise RuntimeError("no text editor found; set $VISUAL or $EDITOR, or pass --editor")


def open_in_editor(
    path: Path,
    *,
    editor: str | None = None,
    runner: Any = subprocess.call,
) -> int:
    """Open ``path`` in the resolved text editor; return the editor exit code."""
    argv = [*resolve_text_editor(editor), str(path)]
    return int(runner(argv))  # noqa: S603 — argv from env/explicit + path
