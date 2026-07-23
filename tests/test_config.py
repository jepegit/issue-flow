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
    assert len(subdirs) == 6
    assert "00-tools" in subdirs
    assert "01-current-issues" in subdirs
    assert "02-partly-solved-issues" in subdirs
    assert "03-solved-issues" in subdirs
    assert "04-designs-and-guides" in subdirs
    assert "05-epics" in subdirs


def test_template_context_keys(tmp_path: Path) -> None:
    settings = Settings()
    context = settings.template_context(tmp_path)
    expected_keys = {
        "issue_flow_version",
        "issueflows_dir",
        "agent_dir",
        "docs_dir",
        "history_file",
        "tools_folder",
        "current_issues_folder",
        "partly_solved_folder",
        "solved_folder",
        "designs_folder",
        "epics_folder",
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
        "label_flows",
        "yolo_label",
        "checks_watch_minutes",
        "step_directives",
        "model_label_flows",
        "deep_model_label",
        "fast_model_label",
        "step_profiles",
        "skill_level",
        "remind_cleanup",
        "suggest_graphify",
        "auto_switchback",
        "pr_merge_method",
        "cycle_max_issues",
        "auto_adversarial_loops",
        "confirm_version_bump",
        "ruff_autofix",
        "auto_close",
        "early_pr",
        "confirm_changelog_update",
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
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
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
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """ISSUEFLOW_CAVEMAN_DEFAULT is used when config does not set the key."""
    monkeypatch.setenv("ISSUEFLOW_CAVEMAN_DEFAULT", "true")
    settings = Settings()
    assert settings.resolve_caveman_default(tmp_path) is True


def test_caveman_default_config_beats_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """The persisted config value wins over a conflicting env var."""
    _write_config(tmp_path, "[issueflow]\ncaveman_default = false\n")
    monkeypatch.setenv("ISSUEFLOW_CAVEMAN_DEFAULT", "true")
    settings = Settings()
    assert settings.resolve_caveman_default(tmp_path) is False


def test_grill_me_default_off_by_default(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
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
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """ISSUEFLOW_GRILL_ME_DEFAULT is used when config does not set the key."""
    monkeypatch.setenv("ISSUEFLOW_GRILL_ME_DEFAULT", "true")
    settings = Settings()
    assert settings.resolve_grill_me_default(tmp_path) is True


def test_grill_me_default_config_beats_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """The persisted config value wins over a conflicting env var."""
    _write_config(tmp_path, "[issueflow]\ngrill_me_default = false\n")
    monkeypatch.setenv("ISSUEFLOW_GRILL_ME_DEFAULT", "true")
    settings = Settings()
    assert settings.resolve_grill_me_default(tmp_path) is False


def test_label_flows_on_by_default(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """With no config and no env, label-driven flows are allowed (default True)."""
    monkeypatch.delenv("ISSUEFLOW_LABEL_FLOWS", raising=False)
    settings = Settings()
    assert settings.resolve_label_flows(tmp_path) is True
    context = settings.template_context(tmp_path)
    assert context["label_flows"] is True


def test_label_flows_from_config(tmp_path: Path) -> None:
    """A persisted [issueflow].label_flows=false is honored."""
    _write_config(tmp_path, "[issueflow]\nlabel_flows = false\n")
    settings = Settings()
    assert settings.resolve_label_flows(tmp_path) is False


def test_label_flows_from_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """ISSUEFLOW_LABEL_FLOWS is used when config does not set the key."""
    monkeypatch.setenv("ISSUEFLOW_LABEL_FLOWS", "false")
    settings = Settings()
    assert settings.resolve_label_flows(tmp_path) is False


def test_label_flows_config_beats_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """The persisted config value wins over a conflicting env var."""
    _write_config(tmp_path, "[issueflow]\nlabel_flows = true\n")
    monkeypatch.setenv("ISSUEFLOW_LABEL_FLOWS", "false")
    settings = Settings()
    assert settings.resolve_label_flows(tmp_path) is True


def test_linguist_attributes_off_by_default(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """With no config and no env, linguist_attributes is off (opt-in)."""
    monkeypatch.delenv("ISSUEFLOW_LINGUIST_ATTRIBUTES", raising=False)
    settings = Settings()
    assert settings.resolve_linguist_attributes(tmp_path) is False


def test_linguist_attributes_from_config(tmp_path: Path) -> None:
    """A persisted [issueflow].linguist_attributes=true is honored."""
    _write_config(tmp_path, "[issueflow]\nlinguist_attributes = true\n")
    settings = Settings()
    assert settings.resolve_linguist_attributes(tmp_path) is True


def test_linguist_attributes_from_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """ISSUEFLOW_LINGUIST_ATTRIBUTES is used when config does not set the key."""
    monkeypatch.setenv("ISSUEFLOW_LINGUIST_ATTRIBUTES", "true")
    settings = Settings()
    assert settings.resolve_linguist_attributes(tmp_path) is True


def test_linguist_attributes_config_beats_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """The persisted config value wins over a conflicting env var."""
    _write_config(tmp_path, "[issueflow]\nlinguist_attributes = false\n")
    monkeypatch.setenv("ISSUEFLOW_LINGUIST_ATTRIBUTES", "true")
    settings = Settings()
    assert settings.resolve_linguist_attributes(tmp_path) is False


def test_yolo_label_default(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """With no config and no env, the yolo trigger label is 'yolo'."""
    monkeypatch.delenv("ISSUEFLOW_YOLO_LABEL", raising=False)
    settings = Settings()
    assert settings.resolve_yolo_label(tmp_path) == "yolo"
    context = settings.template_context(tmp_path)
    assert context["yolo_label"] == "yolo"


def test_yolo_label_from_config(tmp_path: Path) -> None:
    """A persisted [issueflow].yolo_label is honored."""
    _write_config(tmp_path, '[issueflow]\nyolo_label = "fast-track"\n')
    settings = Settings()
    assert settings.resolve_yolo_label(tmp_path) == "fast-track"


def test_yolo_label_from_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """ISSUEFLOW_YOLO_LABEL is used when config does not set the key."""
    monkeypatch.setenv("ISSUEFLOW_YOLO_LABEL", "speedy")
    settings = Settings()
    assert settings.resolve_yolo_label(tmp_path) == "speedy"


def test_yolo_label_config_beats_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """The persisted config value wins over a conflicting env var."""
    _write_config(tmp_path, '[issueflow]\nyolo_label = "fast-track"\n')
    monkeypatch.setenv("ISSUEFLOW_YOLO_LABEL", "speedy")
    settings = Settings()
    assert settings.resolve_yolo_label(tmp_path) == "fast-track"


def test_checks_watch_minutes_default(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    """With no config and no env, the watch budget is 15 minutes."""
    monkeypatch.delenv("ISSUEFLOW_CHECKS_WATCH_MINUTES", raising=False)
    settings = Settings()
    assert settings.resolve_checks_watch_minutes(tmp_path) == 15
    assert settings.template_context(tmp_path)["checks_watch_minutes"] == 15


def test_checks_watch_minutes_from_config(tmp_path: Path) -> None:
    _write_config(tmp_path, "[issueflow]\nchecks_watch_minutes = 30\n")
    settings = Settings()
    assert settings.resolve_checks_watch_minutes(tmp_path) == 30


def test_checks_watch_minutes_from_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    monkeypatch.setenv("ISSUEFLOW_CHECKS_WATCH_MINUTES", "45")
    settings = Settings()
    assert settings.resolve_checks_watch_minutes(tmp_path) == 45


def test_checks_watch_minutes_config_beats_env(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    _write_config(tmp_path, "[issueflow]\nchecks_watch_minutes = 20\n")
    monkeypatch.setenv("ISSUEFLOW_CHECKS_WATCH_MINUTES", "45")
    settings = Settings()
    assert settings.resolve_checks_watch_minutes(tmp_path) == 20


def test_checks_watch_minutes_nonpositive_falls_back(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    _write_config(tmp_path, "[issueflow]\nchecks_watch_minutes = 0\n")
    monkeypatch.setenv("ISSUEFLOW_CHECKS_WATCH_MINUTES", "-3")
    settings = Settings()
    assert settings.resolve_checks_watch_minutes(tmp_path) == 15


def test_skill_behaviour_knob_defaults(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    for key in (
        "ISSUEFLOW_REMIND_CLEANUP",
        "ISSUEFLOW_SUGGEST_GRAPHIFY",
        "ISSUEFLOW_AUTO_SWITCHBACK",
        "ISSUEFLOW_PR_MERGE_METHOD",
        "ISSUEFLOW_CYCLE_MAX_ISSUES",
        "ISSUEFLOW_AUTO_ADVERSARIAL_LOOPS",
        "ISSUEFLOW_CONFIRM_VERSION_BUMP",
        "ISSUEFLOW_RUFF_AUTOFIX",
        "ISSUEFLOW_AUTO_CLOSE",
        "ISSUEFLOW_EARLY_PR",
        "ISSUEFLOW_CONFIRM_CHANGELOG_UPDATE",
    ):
        monkeypatch.delenv(key, raising=False)
    settings = Settings()
    assert settings.resolve_remind_cleanup(tmp_path) is True
    assert settings.resolve_suggest_graphify(tmp_path) is True
    assert settings.resolve_auto_switchback(tmp_path) is True
    assert settings.resolve_pr_merge_method(tmp_path) == "squash"
    assert settings.resolve_cycle_max_issues(tmp_path) == 10
    assert settings.resolve_auto_adversarial_loops(tmp_path) == 2
    assert settings.resolve_confirm_version_bump(tmp_path) is False
    assert settings.resolve_ruff_autofix(tmp_path) is True
    assert settings.resolve_auto_close(tmp_path) is False
    assert settings.resolve_early_pr(tmp_path) is False
    assert settings.resolve_confirm_changelog_update(tmp_path) is False


def test_skill_behaviour_knobs_from_config(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        "[issueflow]\n"
        "remind_cleanup = false\n"
        "suggest_graphify = false\n"
        "auto_switchback = false\n"
        'pr_merge_method = "rebase"\n'
        "cycle_max_issues = 25\n"
        "auto_adversarial_loops = 4\n"
        "confirm_version_bump = true\n"
        "ruff_autofix = false\n"
        "auto_close = true\n"
        "early_pr = true\n"
        "confirm_changelog_update = false\n",
    )
    settings = Settings()
    assert settings.resolve_remind_cleanup(tmp_path) is False
    assert settings.resolve_suggest_graphify(tmp_path) is False
    assert settings.resolve_auto_switchback(tmp_path) is False
    assert settings.resolve_pr_merge_method(tmp_path) == "rebase"
    assert settings.resolve_cycle_max_issues(tmp_path) == 25
    assert settings.resolve_auto_adversarial_loops(tmp_path) == 4
    assert settings.resolve_confirm_version_bump(tmp_path) is True
    assert settings.resolve_ruff_autofix(tmp_path) is False
    assert settings.resolve_auto_close(tmp_path) is True
    assert settings.resolve_early_pr(tmp_path) is True
    assert settings.resolve_confirm_changelog_update(tmp_path) is False


def test_pr_merge_method_invalid_falls_back(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    _write_config(tmp_path, '[issueflow]\npr_merge_method = "fast-forward"\n')
    monkeypatch.setenv("ISSUEFLOW_PR_MERGE_METHOD", "nope")
    settings = Settings()
    assert settings.resolve_pr_merge_method(tmp_path) == "squash"


def test_cycle_max_issues_nonpositive_falls_back(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    _write_config(tmp_path, "[issueflow]\ncycle_max_issues = 0\n")
    monkeypatch.setenv("ISSUEFLOW_CYCLE_MAX_ISSUES", "-1")
    settings = Settings()
    assert settings.resolve_cycle_max_issues(tmp_path) == 10


def test_step_directives_on_by_default(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    monkeypatch.delenv("ISSUEFLOW_STEP_DIRECTIVES", raising=False)
    settings = Settings()
    assert settings.resolve_step_directives(tmp_path) is True


def test_step_directives_from_config(tmp_path: Path) -> None:
    _write_config(tmp_path, "[issueflow]\nstep_directives = false\n")
    settings = Settings()
    assert settings.resolve_step_directives(tmp_path) is False


def test_model_label_flows_off_by_default(
    tmp_path: Path,
    monkeypatch: "pytest.MonkeyPatch",  # noqa: F821
) -> None:
    monkeypatch.delenv("ISSUEFLOW_MODEL_LABEL_FLOWS", raising=False)
    settings = Settings()
    assert settings.resolve_model_label_flows(tmp_path) is False


def test_step_profiles_override_in_context(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        '[issueflow]\n\n[issueflow.step_profiles]\niflow_init = "reasoning"\n',
    )
    settings = Settings()
    profiles = settings.template_context(tmp_path)["step_profiles"]
    assert profiles["iflow_init"] == "reasoning"
    assert profiles["iflow_plan"] == "reasoning"
