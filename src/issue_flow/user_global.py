"""User-global issue-flow config directory and ``config.toml``.

Path contract: `.issueflows/04-designs-and-guides/user-global-config.md`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

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
