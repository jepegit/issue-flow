"""One-shot migrations that ``issue-flow update`` applies to older scaffolds.

Issue #406 merged 30 lifecycle skills into 11 commands with modes. A project
scaffolded by an older release still carries the retired skill folders,
command files, canonical snapshots, user-global copies, and config stems. The
helpers here bring such a project up to date in a single ``update`` run:

* :func:`migrate_config_stems` rewrites retired stems in ``config.toml``
  (``[modes.*]`` lists and ``[issueflow.step_profiles]`` keys).
* :func:`prune_retired_canonical_skills` removes retired folders from the
  canonical store under ``.issueflows/agent/skills/``.
* :func:`prune_retired_user_global_skills` removes retired user-global copies
  that issue-flow itself wrote (stamp matches).
* :func:`drop_stale_stamps` forgets stamps for skill folders that are gone.

Every helper leaves foreign content alone: a folder whose content no longer
matches issue-flow's last write is reported and kept.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import tomlkit
from rich.markup import escape

import issue_flow.console_io as console_io
from issue_flow.editors import EDITORS
from issue_flow.skill_ownership import (
    foreign_skill_reason,
    load_stamp_hashes,
    stamp_store_path,
    user_global_stamp_key,
    write_stamp_hashes,
)
from issue_flow.templating import RETIRED_SKILLS, rename_removed_stems, rename_stem
from issue_flow.user_global import (
    editor_user_global_skills_root,
    user_global_skill_stamp_path,
)

_MODE_LIST_KEYS = ("skills", "commands", "add", "remove")


def _rename_list(values: list[object], *, removing: bool) -> list[str] | None:
    """Return ``values`` with retired stems mapped and de-duplicated, or ``None``."""
    original = [str(value) for value in values]
    if removing:
        renamed = rename_removed_stems(original)
    else:
        renamed = []
        for value in original:
            stem = rename_stem(value)
            if stem not in renamed:
                renamed.append(stem)
    if renamed == original:
        return None
    return renamed


def migrate_config_stems(cfg_path: Path) -> list[str]:
    """Rewrite retired skill/command stems in ``config.toml``.

    Returns a list of human-readable changes (empty when nothing changed).
    Comments and formatting outside the rewritten values are preserved.
    """
    if not cfg_path.is_file():
        return []
    doc = tomlkit.parse(cfg_path.read_text(encoding="utf-8"))
    changes: list[str] = []

    modes = doc.get("modes")
    if isinstance(modes, dict):
        for mode_id, table in modes.items():
            if not isinstance(table, dict):
                continue
            for key in _MODE_LIST_KEYS:
                value = table.get(key)
                if not isinstance(value, list):
                    continue
                renamed = _rename_list(list(value), removing=key == "remove")
                if renamed is None:
                    continue
                array = tomlkit.array()
                array.extend(renamed)
                table[key] = array
                changes.append(f"[modes.{mode_id}].{key}")

    section = doc.get("issueflow")
    profiles = section.get("step_profiles") if isinstance(section, dict) else None
    if isinstance(profiles, dict):
        for old in list(profiles.keys()):
            new = rename_stem(str(old))
            if new == old:
                continue
            value = profiles[old]
            del profiles[old]
            if new not in profiles:
                profiles[new] = value
            changes.append(f"[issueflow.step_profiles].{old} -> {new}")

    if changes:
        cfg_path.write_text(tomlkit.dumps(doc), encoding="utf-8")
        for change in changes:
            console_io.console.print(
                f"  [green]migrate[/green] {cfg_path.name}  {escape(change)}"
            )
    return changes


def _remove_dir(path: Path, label: str) -> None:
    shutil.rmtree(path)
    console_io.console.print(f"  [yellow]prune[/yellow]  {label}")


def prune_retired_canonical_skills(project_root: Path, issueflows_dir: str) -> int:
    """Remove retired skill folders from the canonical store, if one exists."""
    skills_dir = project_root / issueflows_dir / "agent" / "skills"
    if not skills_dir.is_dir():
        return 0
    stamps = load_stamp_hashes(stamp_store_path(project_root, issueflows_dir))
    pruned = 0
    for name in RETIRED_SKILLS:
        folder = skills_dir / name
        if not folder.exists():
            continue
        key = folder.relative_to(project_root).as_posix()
        reason = foreign_skill_reason(folder, stamp=stamps.get(key))
        if reason:
            console_io.console.print(
                f"  [yellow]skip[/yellow]  {key}  (foreign skill: {reason}; not pruning)"
            )
            continue
        _remove_dir(folder, key)
        pruned += 1
    return pruned


def prune_retired_user_global_skills() -> int:
    """Remove retired user-global skill copies that issue-flow wrote.

    Only folders with a matching stamp in the user-global stamp store are
    removed; anything without a stamp, or edited since, is left alone.
    """
    stamp_path = user_global_skill_stamp_path()
    stamps = load_stamp_hashes(stamp_path)
    if not stamps:
        return 0
    pruned = 0
    for profile in EDITORS.values():
        root = editor_user_global_skills_root(profile.id)
        if root is None:
            continue
        for name in RETIRED_SKILLS:
            folder = root / name
            stamp = stamps.get(user_global_stamp_key(profile.id, name))
            if stamp is None or not folder.exists():
                continue
            if foreign_skill_reason(folder, stamp=stamp):
                continue
            _remove_dir(folder, f"{profile.id}:{folder}")
            pruned += 1
    return pruned


def drop_stale_stamps(project_root: Path, issueflows_dir: str) -> int:
    """Forget project stamps whose skill folder no longer exists."""
    path = stamp_store_path(project_root, issueflows_dir)
    stamps = load_stamp_hashes(path)
    if not stamps:
        return 0
    kept = {
        key: digest
        for key, digest in stamps.items()
        if (project_root / key).is_dir()
    }
    dropped = len(stamps) - len(kept)
    if dropped:
        write_stamp_hashes(path, kept)
    return dropped
