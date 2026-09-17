"""Detect foreign skill dirs so ``update`` does not clobber user copies.

A packaged output path (e.g. ``.cursor/skills/iflow-plan``) is **ours** when
it looks like a previous issue-flow render. It is **foreign** when it is a
symlink, has unexpected extra files, drifted from the last-write stamp, or
(with no stamp yet) lacks ``issue-flow-version``.

Stamps live under ``.issueflows/agent/skill-stamps.json`` — never inside
editor skill folders.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

_VERSION_KEY = "issue-flow-version"
_STAMP_NAME = "skill-stamps.json"
_STAMP_FORMAT = "issueflow-skill-stamps-v1"
_ALLOWED_NAMES = frozenset({"SKILL.md"})


def hash_skill_text(text: str) -> str:
    """SHA-256 of LF-normalized skill file text."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return sha256(normalized.encode("utf-8")).hexdigest()


def stamp_store_path(project_root: Path, issueflows_dir: str) -> Path:
    return project_root / issueflows_dir / "agent" / _STAMP_NAME


def stamp_key(project_root: Path, skill_dir: Path) -> str:
    if not skill_dir.is_absolute():
        skill_dir = project_root / skill_dir
    return skill_dir.relative_to(project_root).as_posix()


def load_stamp_hashes(path: Path) -> dict[str, str]:
    """Read a skill-stamps.json file. Missing or invalid → empty."""
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    hashes = payload.get("hashes")
    if not isinstance(hashes, dict):
        return {}
    return {str(key): str(value) for key, value in hashes.items()}


def save_stamp_hash(path: Path, key: str, digest: str) -> None:
    hashes = load_stamp_hashes(path)
    hashes[key] = digest
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"format": _STAMP_FORMAT, "hashes": dict(sorted(hashes.items()))}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_stamps(project_root: Path, issueflows_dir: str) -> dict[str, str]:
    return load_stamp_hashes(stamp_store_path(project_root, issueflows_dir))


def save_stamp(
    project_root: Path,
    issueflows_dir: str,
    skill_dir: Path,
    digest: str,
) -> None:
    save_stamp_hash(
        stamp_store_path(project_root, issueflows_dir),
        stamp_key(project_root, skill_dir),
        digest,
    )


def user_global_stamp_key(editor_id: str, output_name: str) -> str:
    return f"{editor_id}/{output_name}"


def foreign_skill_reason(
    skill_dir: Path,
    *,
    stamp: str | None,
) -> str | None:
    """Return a short reason when ``skill_dir`` is not ours, else ``None``."""
    if not skill_dir.exists():
        return None
    if skill_dir.is_symlink():
        return "symlink"
    if not skill_dir.is_dir():
        return "not a directory"

    names = {entry.name for entry in skill_dir.iterdir()}
    extra = names - _ALLOWED_NAMES
    if extra:
        return f"unexpected extra files ({', '.join(sorted(extra))})"

    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_symlink():
        return "symlink"
    if not skill_md.is_file():
        return None

    text = skill_md.read_text(encoding="utf-8")
    if stamp is not None:
        if hash_skill_text(text) != stamp:
            return "content hash ≠ last render stamp"
        return None
    if f"{_VERSION_KEY}:" not in text:
        return "no issue-flow-version stamp"
    return None


def prepare_skill_dir_for_write(skill_dir: Path) -> None:
    """Make ``skill_dir`` a real directory, unlinking a symlink rather than following it."""
    if skill_dir.is_symlink():
        skill_dir.unlink()
    skill_dir.mkdir(parents=True, exist_ok=True)


def replace_skill_file(path: Path, content: str) -> None:
    """Write ``path`` without following a file symlink into a foreign target."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    path.write_text(content, encoding="utf-8")
