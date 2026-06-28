"""Tests for issue_flow.config."""

from __future__ import annotations

from pathlib import Path

from issue_flow.config import Settings, _detect_project_name


def test_default_settings() -> None:
    settings = Settings()
    assert settings.issueflows_dir == ".issueflows"
    assert settings.agent_dir == ".cursor"
    assert settings.docs_dir == "docs"
    assert settings.history_file == "HISTORY.md"


def test_issueflows_subdirs() -> None:
    settings = Settings()
    subdirs = settings.issueflows_subdirs
    assert len(subdirs) == 5
    assert "00-tools" in subdirs
    assert "01-current-issues" in subdirs
    assert "02-partly-solved-issues" in subdirs
    assert "03-solved-issues" in subdirs
    assert "04-designs-and-guides" in subdirs


def test_template_context_keys(tmp_path: Path) -> None:
    settings = Settings()
    context = settings.template_context(tmp_path)
    expected_keys = {
        "issueflows_dir",
        "agent_dir",
        "docs_dir",
        "history_file",
        "tools_folder",
        "current_issues_folder",
        "partly_solved_folder",
        "solved_folder",
        "designs_folder",
        "project_name",
        "editor",
        "editor_name",
        "commands_dir",
        "commands_supported",
        "graphify_installer",
        "mode",
        "mode_name",
        "included_skills",
        "included_commands",
        "caveman_default",
        "grill_me_default",
    }
    assert set(context.keys()) == expected_keys


def test_detect_project_name_from_pyproject(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "my-cool-project"\nversion = "1.0"\n')
    assert _detect_project_name(tmp_path) == "my-cool-project"


def test_detect_project_name_fallback(tmp_path: Path) -> None:
    # No pyproject.toml -> falls back to directory name
    name = _detect_project_name(tmp_path)
    assert name == tmp_path.resolve().name


def test_settings_from_env(tmp_path: Path, monkeypatch: "pytest.MonkeyPatch") -> None:  # noqa: F821
    monkeypatch.setenv("ISSUEFLOW_DIR", "custom-dir")
    settings = Settings()
    assert settings.issueflows_dir == "custom-dir"


def test_history_file_override_from_env(monkeypatch: "pytest.MonkeyPatch") -> None:  # noqa: F821
    """ISSUEFLOW_HISTORY_FILE should override the default changelog filename."""
    monkeypatch.setenv("ISSUEFLOW_HISTORY_FILE", "CHANGELOG.md")
    settings = Settings()
    assert settings.history_file == "CHANGELOG.md"


def _write_config(tmp_path: Path, body: str) -> None:
    cfg = tmp_path / ".issueflows" / "config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(body, encoding="utf-8")


def test_caveman_default_off_by_default(
    tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"  # noqa: F821
) -> None:
    """With no config and no env, caveman is not on by default."""
    monkeypatch.delenv("ISSUEFLOW_CAVEMAN_DEFAULT", raising=False)
    settings = Settings()
    assert settings.resolve_caveman_default(tmp_path) is False
    context = settings.template_context(tmp_path)
    assert context["caveman_default"] is False


def test_caveman_default_from_config(tmp_path: Path) -> None:
    """A persisted [issueflow].caveman_default=true is honored."""
    _write_config(tmp_path, "[issueflow]\ncaveman_default = true\n")
    settings = Settings()
    assert settings.resolve_caveman_default(tmp_path) is True


def test_caveman_default_from_env(
    tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"  # noqa: F821
) -> None:
    """ISSUEFLOW_CAVEMAN_DEFAULT is used when config does not set the key."""
    monkeypatch.setenv("ISSUEFLOW_CAVEMAN_DEFAULT", "true")
    settings = Settings()
    assert settings.resolve_caveman_default(tmp_path) is True


def test_caveman_default_config_beats_env(
    tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"  # noqa: F821
) -> None:
    """The persisted config value wins over a conflicting env var."""
    _write_config(tmp_path, "[issueflow]\ncaveman_default = false\n")
    monkeypatch.setenv("ISSUEFLOW_CAVEMAN_DEFAULT", "true")
    settings = Settings()
    assert settings.resolve_caveman_default(tmp_path) is False


def test_grill_me_default_off_by_default(
    tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"  # noqa: F821
) -> None:
    """With no config and no env, grill-me is not on by default."""
    monkeypatch.delenv("ISSUEFLOW_GRILL_ME_DEFAULT", raising=False)
    settings = Settings()
    assert settings.resolve_grill_me_default(tmp_path) is False
    context = settings.template_context(tmp_path)
    assert context["grill_me_default"] is False


def test_grill_me_default_from_config(tmp_path: Path) -> None:
    """A persisted [issueflow].grill_me_default=true is honored."""
    _write_config(tmp_path, "[issueflow]\ngrill_me_default = true\n")
    settings = Settings()
    assert settings.resolve_grill_me_default(tmp_path) is True


def test_grill_me_default_from_env(
    tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"  # noqa: F821
) -> None:
    """ISSUEFLOW_GRILL_ME_DEFAULT is used when config does not set the key."""
    monkeypatch.setenv("ISSUEFLOW_GRILL_ME_DEFAULT", "true")
    settings = Settings()
    assert settings.resolve_grill_me_default(tmp_path) is True


def test_grill_me_default_config_beats_env(
    tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"  # noqa: F821
) -> None:
    """The persisted config value wins over a conflicting env var."""
    _write_config(tmp_path, "[issueflow]\ngrill_me_default = false\n")
    monkeypatch.setenv("ISSUEFLOW_GRILL_ME_DEFAULT", "true")
    settings = Settings()
    assert settings.resolve_grill_me_default(tmp_path) is False
