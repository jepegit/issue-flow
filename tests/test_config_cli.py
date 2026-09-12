"""Tests for issue-flow config show / set / edit helpers and CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from issue_flow.cli import app
from issue_flow import config_ops
from issue_flow.config import Settings


def _plain(text: str) -> str:
    # Match test_cli helper: strip rich markup if present in captured output.
    return text


def _json(output: str) -> Any:
    return json.loads(_plain(output))


def test_parse_config_value_bool_and_int() -> None:
    assert config_ops.parse_config_value("fix_auto_name", "true") is True
    assert config_ops.parse_config_value("fix_auto_name", "off") is False
    assert config_ops.parse_config_value("cycle_max_issues", "12") == 12
    with pytest.raises(ValueError, match="positive"):
        config_ops.parse_config_value("cycle_max_issues", "0")
    with pytest.raises(ValueError, match="unknown key"):
        config_ops.parse_config_value("not_a_key", "1")


def test_parse_config_value_list_and_enum() -> None:
    assert config_ops.parse_config_value("pstack_skills", "unslop, tdd") == [
        "unslop",
        "tdd",
    ]
    assert config_ops.parse_config_value("pstack_skills", '["unslop"]') == ["unslop"]
    assert config_ops.parse_config_value("pr_merge_method", "rebase") == "rebase"
    with pytest.raises(ValueError, match="one of"):
        config_ops.parse_config_value("pr_merge_method", "fast-forward")


def test_upsert_and_read_persisted(tmp_path: Path) -> None:
    cfg = tmp_path / ".issueflows" / "config.toml"
    config_ops.upsert_config_value(cfg, "fix_auto_name", True)
    config_ops.upsert_config_value(cfg, "yolo_label", "speedy")
    section = config_ops.read_persisted_section(cfg)
    assert section is not None
    assert section["fix_auto_name"] is True
    assert section["yolo_label"] == "speedy"
    # Second write preserves the other key.
    config_ops.upsert_config_value(cfg, "fix_auto_name", False)
    section2 = config_ops.read_persisted_section(cfg)
    assert section2 is not None
    assert section2["fix_auto_name"] is False
    assert section2["yolo_label"] == "speedy"


def test_resolve_text_editor_prefers_explicit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake = tmp_path / "myed"
    fake.write_text("#!/bin/sh\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.delenv("EDITOR", raising=False)
    argv = config_ops.resolve_text_editor(str(fake))
    assert argv == [str(fake)]


def test_config_show_and_set_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ISSUEFLOW_FIX_AUTO_NAME", raising=False)
    runner = CliRunner()

    show = runner.invoke(
        app, ["config", "show", "fix_auto_name", "-C", str(tmp_path), "--json"]
    )
    assert show.exit_code == 0, show.output
    payload = _json(show.stdout)
    assert payload["value"] is False
    assert payload["set"] is False

    set_result = runner.invoke(
        app,
        ["config", "set", "fix_auto_name", "true", "-C", str(tmp_path), "--json"],
    )
    assert set_result.exit_code == 0, set_result.output
    set_payload = _json(set_result.stdout)
    assert set_payload["ok"] is True
    assert set_payload["value"] is True
    assert set_payload["needs_update"] is True

    settings = Settings()
    assert settings.resolve_fix_auto_name(tmp_path) is True

    show2 = runner.invoke(app, ["config", "show", "-C", str(tmp_path), "--json"])
    assert show2.exit_code == 0, show2.output
    all_payload = _json(show2.stdout)
    assert all_payload["values"]["fix_auto_name"] is True
    assert "fix_auto_name" in all_payload["persisted_keys"]

    persisted = runner.invoke(
        app,
        ["config", "show", "-C", str(tmp_path), "--persisted", "--json"],
    )
    assert persisted.exit_code == 0, persisted.output
    pers = _json(persisted.stdout)
    assert pers["values"] == {"fix_auto_name": True}


def test_config_set_rejects_unknown(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app, ["config", "set", "nope", "1", "-C", str(tmp_path), "--json"]
    )
    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["ok"] is False
    assert "unknown key" in payload["error"]


def test_config_edit_json_does_not_open_editor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = tmp_path / "ed"
    fake.write_text("#!/bin/sh\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("EDITOR", str(fake))

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "config",
            "edit",
            "-C",
            str(tmp_path),
            "--create",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["ok"] is True
    assert payload["created"] is True
    assert payload["opened"] is False
    assert (tmp_path / ".issueflows" / "config.toml").is_file()


def test_config_edit_opens_editor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_open(path: Path, *, editor: str | None = None) -> int:
        calls.append([*(config_ops.resolve_text_editor(editor)), str(path)])
        return 0

    monkeypatch.setattr(config_ops, "open_in_editor", fake_open)

    cfg = tmp_path / ".issueflows" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('[issueflow]\nmode = "standard"\n', encoding="utf-8")

    fake = tmp_path / "ed"
    fake.write_text("#!/bin/sh\n", encoding="utf-8")
    fake.chmod(0o755)

    from issue_flow.agent import run_config_edit
    from rich.console import Console

    code = run_config_edit(
        tmp_path, Console(), editor=str(fake), create=False, as_json=False
    )
    assert code == 0
    assert calls == [[str(fake), str(cfg)]]


def test_config_help_lists_show_set_edit() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    out = result.stdout
    assert "show" in out
    assert "set" in out
    assert "edit" in out
