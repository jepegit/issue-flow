"""Tests for the `issue-flow` Typer CLI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from issue_flow.cli import app

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    """Strip ANSI color/style codes so help text can be matched reliably.

    Rich colorizes ``--help`` output when it thinks it is talking to a
    terminal (as on CI), which splits literals like ``--editor`` across escape
    sequences. Stripping the codes makes the assertions environment-agnostic.
    """
    return _ANSI_RE.sub("", text)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_lists_graphify_command(runner: CliRunner) -> None:
    """`issue-flow --help` must mention the `graphify` command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "graphify" in result.stdout


def test_init_help_documents_editor_option(runner: CliRunner) -> None:
    """`issue-flow init --help` must advertise the --editor option."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "--editor" in _plain(result.stdout)


def test_init_editor_codex_scaffolds_skills_only(
    runner: CliRunner, tmp_path: Path
) -> None:
    """`issue-flow init --editor codex` writes the codex tree without commands."""
    result = runner.invoke(app, ["init", str(tmp_path), "--editor", "codex"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".codex" / "skills" / "iflow-iflow" / "SKILL.md").is_file()
    assert not (tmp_path / ".codex" / "commands").exists()
    assert (tmp_path / "AGENTS.md").is_file()


def test_init_unknown_editor_exits_with_code_2(
    runner: CliRunner, tmp_path: Path
) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--editor", "nano"])
    assert result.exit_code == 2


def test_graphify_help_describes_passthrough(runner: CliRunner) -> None:
    result = runner.invoke(app, ["graphify", "--help"])
    assert result.exit_code == 0
    assert "graphify" in result.stdout.lower()


def test_graphify_invokes_graphify_when_available(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`issue-flow graphify` should call subprocess.run with the graphify CLI."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)

    result = runner.invoke(app, ["graphify", "-C", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert captured["cmd"][0] == "graphify"
    # Default subcommand must be injected since graphify requires one.
    # We default to ``update`` (AST-only, no LLM API key required) so
    # ``issue-flow graphify`` works on a fresh machine with no backend
    # configured.
    assert captured["cmd"][1] == "update"


def test_graphify_forwards_extra_args(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leading subcommand and trailing flags must reach `graphify` verbatim."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)

    # `cluster-only` is a real graphify build subcommand; `--no-viz` is
    # one of its real flags. Both must reach graphify verbatim, and the
    # project root must be injected after the subcommand.
    result = runner.invoke(
        app, ["graphify", "-C", str(tmp_path), "cluster-only", "--no-viz"]
    )

    assert result.exit_code == 0, result.output
    assert captured["cmd"] == [
        "graphify",
        "cluster-only",
        str(tmp_path),
        "--no-viz",
    ]


def test_graphify_exits_nonzero_when_graphify_missing(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When graphify is not installed, `issue-flow graphify` exits with the error code from run_build."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    monkeypatch.setattr(graphify_module, "_candidate_install_locations", lambda: [])

    def fail_run(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("subprocess.run must not be called when graphify is missing")

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)

    result = runner.invoke(app, ["graphify", "-C", str(tmp_path)])

    assert result.exit_code == 2
    assert "graphifyy" in result.output


def test_graphify_propagates_graphify_exit_code(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    class _Result:
        returncode = 7

    monkeypatch.setattr(graphify_module.subprocess, "run", lambda *a, **kw: _Result())

    result = runner.invoke(app, ["graphify", "-C", str(tmp_path)])

    assert result.exit_code == 7
