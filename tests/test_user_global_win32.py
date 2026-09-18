"""Native Windows user-global paths (monkeypatched ``win32``, no WSL bridge)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from issue_flow import user_global
from issue_flow.user_global import (
    editor_user_global_skills_root,
    os_config_home,
    user_config_dir,
    user_global_skill_stamp_path,
)


@pytest.fixture
def win32_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Force the win32 branch without reading ``/mnt/c``."""
    appdata = tmp_path / "AppData" / "Roaming"
    appdata.mkdir(parents=True)
    home = tmp_path / "Users" / "pat"
    home.mkdir(parents=True)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    return appdata


def test_win32_os_config_home_uses_appdata(win32_env: Path) -> None:
    assert sys.platform == "win32"
    assert os_config_home() == win32_env
    assert user_config_dir() == win32_env / "issue-flow"
    assert (
        user_global_skill_stamp_path() == win32_env / "issue-flow" / "skill-stamps.json"
    )
    assert "/mnt/c" not in os_config_home().as_posix()


def test_win32_os_config_home_falls_back_without_appdata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "Users" / "pat"
    home.mkdir(parents=True)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert os_config_home() == Path.home() / "AppData" / "Roaming"
    assert "/mnt/c" not in os_config_home().as_posix()


def test_win32_editor_globals_use_home_and_appdata(win32_env: Path) -> None:
    home = Path.home()
    assert editor_user_global_skills_root("cursor") == home / ".cursor" / "skills"
    assert editor_user_global_skills_root("claude") == home / ".claude" / "skills"
    assert editor_user_global_skills_root("codex") == home / ".agents" / "skills"
    assert (
        editor_user_global_skills_root("opencode") == win32_env / "opencode" / "skills"
    )
    assert "/mnt/c" not in str(editor_user_global_skills_root("cursor"))
    assert "/mnt/c" not in str(editor_user_global_skills_root("opencode"))


def test_linux_wsl_ignores_windows_appdata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Non-win32 keeps XDG/home; APPDATA must not win (no WSL bridge)."""
    xdg = tmp_path / "xdg"
    xdg.mkdir()
    monkeypatch.setattr(user_global.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    monkeypatch.setenv("APPDATA", str(tmp_path / "WindowsRoaming"))
    assert os_config_home() == xdg
    assert user_config_dir() == xdg / "issue-flow"
    assert editor_user_global_skills_root("opencode") == xdg / "opencode" / "skills"
