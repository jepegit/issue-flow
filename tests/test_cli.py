"""Tests for the `issue-flow` Typer CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from issue_flow.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_lists_build_command(runner: CliRunner) -> None:
    """`issue-flow --help` must mention the new `build` command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "build" in result.stdout


def test_build_help_describes_passthrough(runner: CliRunner) -> None:
    result = runner.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "graphify" in result.stdout.lower()


def test_build_invokes_graphify_when_available(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`issue-flow build` should call subprocess.run with the graphify CLI."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)

    result = runner.invoke(app, ["build", "-C", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert captured["cmd"][0] == "graphify"
    # Default subcommand must be injected since graphify requires one.
    # We default to ``update`` (AST-only, no LLM API key required) so
    # ``issue-flow build`` works on a fresh machine with no backend
    # configured.
    assert captured["cmd"][1] == "update"


def test_build_forwards_extra_args(
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
        app, ["build", "-C", str(tmp_path), "cluster-only", "--no-viz"]
    )

    assert result.exit_code == 0, result.output
    assert captured["cmd"] == [
        "graphify",
        "cluster-only",
        str(tmp_path),
        "--no-viz",
    ]


def test_build_exits_nonzero_when_graphify_missing(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When graphify is not installed, `issue-flow build` exits with the error code from run_build."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    monkeypatch.setattr(graphify_module, "_candidate_install_locations", lambda: [])

    def fail_run(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("subprocess.run must not be called when graphify is missing")

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)

    result = runner.invoke(app, ["build", "-C", str(tmp_path)])

    assert result.exit_code == 2
    assert "graphifyy" in result.output


def test_build_propagates_graphify_exit_code(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    class _Result:
        returncode = 7

    monkeypatch.setattr(graphify_module.subprocess, "run", lambda *a, **kw: _Result())

    result = runner.invoke(app, ["build", "-C", str(tmp_path)])

    assert result.exit_code == 7
