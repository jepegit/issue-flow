"""Tests for the optional managed Linguist .gitattributes block."""

from __future__ import annotations

from pathlib import Path

from issue_flow.config import Settings
from issue_flow.init import run_init, run_update
from issue_flow.surfaces import (
    ensure_linguist_gitattributes,
    maybe_ensure_linguist_gitattributes,
)

_BEGIN = "# BEGIN issue-flow linguist (generated; do not edit)"
_END = "# END issue-flow linguist"


def test_ensure_linguist_gitattributes_creates_file(tmp_path: Path) -> None:
    assert ensure_linguist_gitattributes(tmp_path) is True
    path = tmp_path / ".gitattributes"
    text = path.read_text(encoding="utf-8")
    assert _BEGIN in text
    assert _END in text
    assert "graphify-out/** linguist-generated" in text
    assert "tests/** linguist-documentation" in text


def test_ensure_linguist_gitattributes_appends_without_clobber(tmp_path: Path) -> None:
    existing = tmp_path / ".gitattributes"
    existing.write_text("*.py text\n", encoding="utf-8")

    assert ensure_linguist_gitattributes(tmp_path) is True
    text = existing.read_text(encoding="utf-8")
    assert text.startswith("*.py text\n")
    assert _BEGIN in text


def test_ensure_linguist_gitattributes_skips_when_markers_present(
    tmp_path: Path,
) -> None:
    path = tmp_path / ".gitattributes"
    path.write_text(f"{_BEGIN}\nold\n{_END}\n", encoding="utf-8")

    assert ensure_linguist_gitattributes(tmp_path) is False
    assert path.read_text(encoding="utf-8") == f"{_BEGIN}\nold\n{_END}\n"


def test_maybe_ensure_respects_flag_off(tmp_path: Path) -> None:
    settings = Settings()
    assert maybe_ensure_linguist_gitattributes(tmp_path, settings) is False
    assert not (tmp_path / ".gitattributes").exists()


def test_maybe_ensure_writes_when_flag_on(tmp_path: Path) -> None:
    cfg = tmp_path / ".issueflows" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("[issueflow]\nlinguist_attributes = true\n", encoding="utf-8")

    settings = Settings()
    assert maybe_ensure_linguist_gitattributes(tmp_path, settings) is True
    assert _BEGIN in (tmp_path / ".gitattributes").read_text(encoding="utf-8")


def test_init_writes_gitattributes_when_enabled(tmp_path: Path) -> None:
    cfg = tmp_path / ".issueflows" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        '[issueflow]\nmode = "standard"\nlinguist_attributes = true\n',
        encoding="utf-8",
    )

    run_init(tmp_path, skip_dep_check=True)

    text = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
    assert _BEGIN in text
    assert "graphify-out/** linguist-generated" in text


def test_init_skips_gitattributes_when_disabled(tmp_path: Path) -> None:
    run_init(tmp_path, skip_dep_check=True)
    assert not (tmp_path / ".gitattributes").exists()


def test_update_writes_gitattributes_when_enabled(tmp_path: Path) -> None:
    run_init(tmp_path, skip_dep_check=True)
    assert not (tmp_path / ".gitattributes").exists()

    cfg = tmp_path / ".issueflows" / "config.toml"
    cfg.write_text(
        '[issueflow]\nmode = "standard"\nlinguist_attributes = true\n',
        encoding="utf-8",
    )

    run_update(tmp_path, skip_dep_check=True)

    text = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
    assert _BEGIN in text
