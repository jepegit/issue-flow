"""Tests for the ``novice`` scaffolding mode and its settings preset (#246)."""

from __future__ import annotations

import tomllib
from pathlib import Path

from issue_flow.init import run_init, run_update
from issue_flow.modes import (
    NOVICE_CONFIG,
    NOVICE_MODE,
    available_modes,
    resolve_mode,
    seed_novice_config,
)
from issue_flow.templating import COMMAND_NAMES, SKILL_DIRS


def _issueflow_table(config: Path) -> dict[str, object]:
    return dict(tomllib.loads(config.read_text(encoding="utf-8"))["issueflow"])


def test_novice_is_a_registered_mode() -> None:
    assert NOVICE_MODE in available_modes()


def test_novice_is_a_strict_subset_that_keeps_the_linear_lifecycle() -> None:
    mode = resolve_mode(NOVICE_MODE)

    assert mode.skills < frozenset(SKILL_DIRS)
    assert mode.commands < frozenset(COMMAND_NAMES)
    for stem in (
        "iflow_setup",
        "iflow_capture",
        "iflow_plan",
        "iflow_build",
        "iflow_close",
    ):
        assert stem in mode.skills
    # The hands-off, batch, and decomposition machinery is what novice drops.
    for stem in ("iflow_yolo", "iflow_cycle", "iflow_auto", "iflow_epic"):
        assert stem not in mode.skills


def test_novice_commands_and_skills_agree() -> None:
    """Every novice command has its mirrored skill (Codex-style editors need it)."""
    mode = resolve_mode(NOVICE_MODE)
    for command in mode.commands:
        assert command.replace("-", "_", 1) in mode.skills or command == "iflow"


def test_seed_novice_config_writes_the_preset(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"

    assert seed_novice_config(config) is True

    table = _issueflow_table(config)
    assert table["mode"] == NOVICE_MODE
    for key, value in NOVICE_CONFIG.items():
        assert table[key] == value


def test_seed_novice_config_never_overwrites(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[issueflow]\nauto_plan = true\n", encoding="utf-8")

    assert seed_novice_config(config) is False
    assert _issueflow_table(config)["auto_plan"] is True


def test_init_novice_scaffolds_only_the_novice_surface(tmp_path: Path) -> None:
    run_init(tmp_path, mode=NOVICE_MODE)

    skills = tmp_path / ".cursor" / "skills"
    assert (skills / "iflow-setup" / "SKILL.md").is_file()
    assert (skills / "iflow-plan" / "SKILL.md").is_file()
    assert not (skills / "iflow-yolo").exists()
    assert not (skills / "iflow-cycle").exists()
    assert not (skills / "caveman").exists()


def test_init_novice_seeds_the_settings_preset(tmp_path: Path) -> None:
    run_init(tmp_path, mode=NOVICE_MODE)

    table = _issueflow_table(tmp_path / ".issueflows" / "config.toml")
    assert table["mode"] == NOVICE_MODE
    assert table["auto_plan"] is False
    assert table["auto_build"] is False
    assert table["confirm_version_bump"] is True


def test_init_novice_implies_the_basic_skill_level(tmp_path: Path) -> None:
    run_init(tmp_path, mode=NOVICE_MODE)

    assert (
        _issueflow_table(tmp_path / ".issueflows" / "config.toml")["skill_level"]
        == "basic"
    )


def test_explicit_skill_level_beats_the_novice_implication(tmp_path: Path) -> None:
    run_init(tmp_path, mode=NOVICE_MODE, skill_level="advanced")

    table = _issueflow_table(tmp_path / ".issueflows" / "config.toml")
    assert table["skill_level"] == "advanced"
    quality_doc = (
        tmp_path / ".issueflows" / "04-designs-and-guides" / "python-quality-tools.md"
    )
    assert quality_doc.is_file()


def test_switching_to_novice_keeps_existing_settings(tmp_path: Path) -> None:
    """Re-running init on a configured project must not rewrite tuned knobs."""
    run_init(tmp_path)
    config = tmp_path / ".issueflows" / "config.toml"
    config.write_text(
        '[issueflow]\nmode = "standard"\nauto_plan = true\n', encoding="utf-8"
    )

    run_init(tmp_path, mode=NOVICE_MODE)

    table = _issueflow_table(config)
    assert table["mode"] == NOVICE_MODE
    assert table["auto_plan"] is True


def test_novice_rule_does_not_advertise_absent_commands(tmp_path: Path) -> None:
    run_init(tmp_path, mode=NOVICE_MODE)

    rule = (tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc").read_text(
        encoding="utf-8"
    )
    assert "/iflow-setup" in rule
    for absent in ("/iflow-yolo", "/iflow-cycle", "/iflow-auto", "/iflow-epic"):
        assert absent not in rule


def test_standard_rule_still_documents_the_full_surface(tmp_path: Path) -> None:
    run_init(tmp_path)

    rule = (tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc").read_text(
        encoding="utf-8"
    )
    for present in ("/iflow-setup", "/iflow-yolo", "/iflow-cycle", "/iflow-archive"):
        assert present in rule


def test_update_honours_the_persisted_novice_mode(tmp_path: Path) -> None:
    run_init(tmp_path, mode=NOVICE_MODE)
    yolo_skill = tmp_path / ".cursor" / "skills" / "iflow-yolo"

    run_update(tmp_path)

    assert (tmp_path / ".cursor" / "skills" / "iflow-setup" / "SKILL.md").is_file()
    assert not yolo_skill.exists()
