"""Tests for skill level feature in issue_flow.init."""

from __future__ import annotations

from pathlib import Path

from issue_flow.init import run_init
from issue_flow.modes import DEFAULT_SKILL_LEVEL, SKILL_LEVELS


def test_skill_level_constants() -> None:
    """The skill-level contract: default is 'standard', set is ordered low->high."""
    assert DEFAULT_SKILL_LEVEL == "standard"
    assert SKILL_LEVELS == ("basic", "standard", "advanced")
    assert DEFAULT_SKILL_LEVEL in SKILL_LEVELS


def test_init_advanced_skill_level_creates_quality_doc(tmp_path: Path) -> None:
    """init --skill-level advanced creates python-quality-tools.md design doc."""
    run_init(tmp_path, skill_level="advanced")

    doc = tmp_path / ".issueflows" / "04-designs-and-guides" / "python-quality-tools.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "mypy" in text
    assert "ruff" in text
    assert "ruff check --fix" in text
    assert "pre-commit" in text
    assert "pytest" in text
    assert "Type checking" in text


def test_init_standard_skill_level_omits_quality_doc(tmp_path: Path) -> None:
    """init (default) does not create python-quality-tools.md."""
    run_init(tmp_path)

    doc = tmp_path / ".issueflows" / "04-designs-and-guides" / "python-quality-tools.md"
    assert not doc.exists()


def test_init_basic_skill_level_omits_quality_doc(tmp_path: Path) -> None:
    """init --skill-level basic does not create python-quality-tools.md."""
    run_init(tmp_path, skill_level="basic")

    doc = tmp_path / ".issueflows" / "04-designs-and-guides" / "python-quality-tools.md"
    assert not doc.exists()


def test_init_skill_level_persisted_in_config(tmp_path: Path) -> None:
    """init --skill-level advanced persists skill_level in config.toml."""
    run_init(tmp_path, skill_level="advanced")

    config = tmp_path / ".issueflows" / "config.toml"
    assert config.is_file()
    text = config.read_text(encoding="utf-8")
    assert 'skill_level = "advanced"' in text


def test_init_dotenv_includes_skill_level_key(tmp_path: Path) -> None:
    """.env created by init includes commented ISSUEFLOW_SKILL_LEVEL line."""
    run_init(tmp_path)

    env_file = tmp_path / ".env"
    assert env_file.is_file()
    text = env_file.read_text(encoding="utf-8")
    assert "# ISSUEFLOW_SKILL_LEVEL=standard" in text


def test_init_update_honours_persisted_skill_level(tmp_path: Path) -> None:
    """update re-creates the quality doc when skill_level=advanced is persisted."""
    run_init(tmp_path, skill_level="advanced")

    doc = tmp_path / ".issueflows" / "04-designs-and-guides" / "python-quality-tools.md"
    assert doc.is_file()
    doc.unlink()
    assert not doc.exists()

    from issue_flow.init import run_update

    run_update(tmp_path)

    assert doc.is_file()


def test_init_invalid_skill_level_aborts(tmp_path: Path) -> None:
    """init --skill-level unknown raises typer.Exit."""
    import pytest
    import typer

    with pytest.raises(typer.Exit) as exc_info:
        run_init(tmp_path, skill_level="unknown")

    assert exc_info.value.exit_code == 2
    assert not (tmp_path / ".issueflows").exists()
