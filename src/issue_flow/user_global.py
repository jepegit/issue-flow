"""User-global issue-flow config directory, ``config.toml``, and registry.

Path contract: `.issueflows/04-designs-and-guides/user-global-config.md`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import tomllib
import tomlkit

from issue_flow import config_ops

USER_GLOBAL_FORBIDDEN_KEYS = frozenset({"mode", "locked"})


def user_config_dir() -> Path:
    """Return the OS user-global issue-flow directory (not a project path).

    Linux/macOS/WSL: ``$XDG_CONFIG_HOME/issue-flow`` or ``~/.config/issue-flow``.
    Native Windows: ``%APPDATA%\\issue-flow``.
    """
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if appdata and appdata.strip():
            return Path(appdata) / "issue-flow"
        return Path.home() / "AppData" / "Roaming" / "issue-flow"
    xdg = os.getenv("XDG_CONFIG_HOME")
    if xdg and xdg.strip():
        return Path(xdg) / "issue-flow"
    return Path.home() / ".config" / "issue-flow"


def user_global_config_path() -> Path:
    return user_config_dir() / "config.toml"


def read_user_global_section() -> dict[str, Any] | None:
    """Raw ``[issueflow]`` table from the user-global file, if present."""
    return config_ops.read_persisted_section(user_global_config_path())


def user_global_value(key: str) -> Any | None:
    """Return a user-global preference, or ``None`` if missing or forbidden."""
    if key in USER_GLOBAL_FORBIDDEN_KEYS:
        return None
    section = read_user_global_section()
    if not section or key not in section:
        return None
    return section[key]


def upsert_user_global_value(key: str, value: Any) -> Path:
    """Write ``[issueflow].key`` in the user-global file. Refuses forbidden keys."""
    if key in USER_GLOBAL_FORBIDDEN_KEYS:
        raise ValueError(
            f"{key} is not a user-global key (project-only; see user-global-config.md)"
        )
    path = user_global_config_path()
    config_ops.upsert_config_value(
        path,
        key,
        value,
        created_comment=(
            "issue-flow user-global config. Created by "
            "'issue-flow config set --global'."
        ),
    )
    return path


def user_global_registry_path() -> Path:
    return user_config_dir() / "registry.toml"


def read_registry_roots() -> list[Path]:
    """Absolute roots listed in ``registry.toml``. Missing file → empty."""
    path = user_global_registry_path()
    if not path.is_file():
        return []
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    raw = data.get("roots")
    if not isinstance(raw, list):
        return []
    roots: list[Path] = []
    seen: set[Path] = set()
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            continue
        candidate = Path(item)
        if not candidate.is_absolute():
            continue
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        roots.append(resolved)
    return roots


def register_root(project_root: Path) -> bool:
    """Add ``project_root`` to the registry. Idempotent. Returns True if added.

    Raises :class:`ValueError` when ``project_root`` is relative.
    """
    if not project_root.is_absolute():
        raise ValueError(
            f"registry roots must be absolute; got {str(project_root)!r}"
        )
    resolved = project_root.resolve()
    roots = read_registry_roots()
    if resolved in roots:
        return False
    roots.append(resolved)
    _write_registry_roots(roots)
    return True


def unregister_root(project_root: Path) -> bool:
    """Remove ``project_root`` from the registry. Idempotent. Returns True if removed.

    Raises :class:`ValueError` when ``project_root`` is relative.
    """
    if not project_root.is_absolute():
        raise ValueError(
            f"registry roots must be absolute; got {str(project_root)!r}"
        )
    resolved = project_root.resolve()
    roots = read_registry_roots()
    if resolved not in roots:
        return False
    _write_registry_roots([root for root in roots if root != resolved])
    return True


def _write_registry_roots(roots: list[Path]) -> Path:
    path = user_global_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = tomlkit.document()
    doc.add(
        tomlkit.comment(
            "issue-flow project registry. Created by "
            "'issue-flow register' / 'issue-flow init'."
        )
    )
    doc.add(
        tomlkit.comment(
            "Absolute roots that 'issue-flow update --all' walks. "
            "Locked roots are listed and skipped."
        )
    )
    doc["roots"] = [str(root) for root in roots]
    path.write_text(tomlkit.dumps(doc), encoding="utf-8")
    return path
