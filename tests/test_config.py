"""Tests for issue_flow.config."""

from __future__ import annotations

from pathlib import Path

from issue_flow.config import Settings, _detect_project_name


def test_default_settings() -> None:
    settings = Settings()
    assert settings.issueflows_dir == ".issueflows"
    assert settings.cursor_dir == ".cursor"
    assert settings.docs_dir == "docs"


def test_issueflows_subdirs() -> None:
    settings = Settings()
    subdirs = settings.issueflows_subdirs
    assert len(subdirs) == 4
    assert "00-tools" in subdirs
    assert "01-current-issues" in subdirs
    assert "02-partly-solved-issues" in subdirs
    assert "03-solved-issues" in subdirs


def test_template_context_keys(tmp_path: Path) -> None:
    settings = Settings()
    context = settings.template_context(tmp_path)
    expected_keys = {
        "issueflows_dir",
        "cursor_dir",
        "docs_dir",
        "tools_folder",
        "current_issues_folder",
        "partly_solved_folder",
        "solved_folder",
        "project_name",
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
