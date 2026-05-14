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

    result = runner.invoke(app, ["build", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert captured["cmd"][0] == "graphify"


def test_build_forwards_extra_args(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Extra args after the project dir must reach `graphify` verbatim."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)

    result = runner.invoke(
        app, ["build", str(tmp_path), "--update", "--no-viz"]
    )

    assert result.exit_code == 0, result.output
    assert "--update" in captured["cmd"]
    assert "--no-viz" in captured["cmd"]


def test_build_exits_nonzero_when_graphify_missing(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When graphify is not installed, `issue-flow build` exits with the error code from run_build."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)

    def fail_run(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("subprocess.run must not be called when graphify is missing")

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)

    result = runner.invoke(app, ["build", str(tmp_path)])

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

    result = runner.invoke(app, ["build", str(tmp_path)])

    assert result.exit_code == 7
