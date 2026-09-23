"""Tests for workspace status / doctor / dirty fan-out (#318)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
from rich.console import Console
from typer.testing import CliRunner

from issue_flow.agent import (
    run_workspace_dirty,
    run_workspace_doctor,
    run_workspace_status,
)
from issue_flow.cli import app
from issue_flow.project import WORKSPACE_FILENAME

pytestmark = pytest.mark.essential

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _json(output: str) -> Any:
    return json.loads(_plain(output))


def _make_members(
    tmp_path: Path,
    *,
    names: tuple[str, ...] = ("alpha", "beta"),
    lock: tuple[str, ...] = (),
) -> Path:
    for name in names:
        root = tmp_path / name
        base = root / ".issueflows"
        (base / "01-current-issues").mkdir(parents=True)
        (base / "02-partly-solved-issues").mkdir()
        (base / "03-solved-issues").mkdir()
        if name in lock:
            (base / "config.toml").write_text(
                "[issueflow]\nlocked = true\n", encoding="utf-8"
            )
    (tmp_path / WORKSPACE_FILENAME).write_text(
        f'[workspace]\ndefault = "alpha"\nmembers = {list(names)!r}\n'.replace(
            "'", '"'
        ),
        encoding="utf-8",
    )
    return tmp_path


def _git_init(path: Path) -> None:
    subprocess.run(
        ["git", "init"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def test_workspace_status_json_two_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ISSUEFLOW_LOCKED", raising=False)
    workspace = _make_members(tmp_path)
    console = Console(record=True)
    code = run_workspace_status(workspace, console, local=True, as_json=True)
    assert code == 0
    payload = _json(console.export_text())
    assert payload["ok"] is True
    assert payload["ok_count"] == 2
    assert payload["fail_count"] == 0
    names = [m["name"] for m in payload["members"]]
    assert names == ["alpha", "beta"]
    for member in payload["members"]:
        assert member["ok"] is True
        assert member["status"]["focus"] is None
        assert member["status"]["solved_count"] == 0


def test_workspace_status_missing_toml(tmp_path: Path) -> None:
    console = Console(record=True)
    code = run_workspace_status(tmp_path, console, local=True, as_json=True)
    assert code == 1
    payload = _json(console.export_text())
    assert payload["ok"] is False
    assert "issueflow-workspace.toml" in payload["error"]


def test_workspace_status_skips_locked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ISSUEFLOW_LOCKED", raising=False)
    workspace = _make_members(tmp_path, lock=("beta",))
    console = Console(record=True)
    code = run_workspace_status(workspace, console, local=True, as_json=True)
    assert code == 0
    payload = _json(console.export_text())
    by_name = {m["name"]: m for m in payload["members"]}
    assert by_name["alpha"]["ok"] is True
    assert "status" in by_name["alpha"]
    assert by_name["beta"]["skipped"] is True
    assert by_name["beta"]["reason"] == "locked"
    assert payload["skip_count"] == 1


def test_workspace_status_continues_on_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ISSUEFLOW_LOCKED", raising=False)
    workspace = _make_members(tmp_path)

    def boom(root: Path, local: bool) -> dict[str, Any]:
        if root.name == "beta":
            raise RuntimeError("status boom")
        return {
            "branch": None,
            "focus": None,
            "ambiguous_candidates": [],
            "parked": [],
            "solved_count": 0,
            "solved_recent": [],
            "cycle_active": False,
            "github": None,
        }

    monkeypatch.setattr("issue_flow.agent._status_payload", boom)
    console = Console(record=True)
    code = run_workspace_status(workspace, console, local=True, as_json=True)
    assert code == 1
    payload = _json(console.export_text())
    by_name = {m["name"]: m for m in payload["members"]}
    assert by_name["alpha"]["ok"] is True
    assert by_name["beta"]["ok"] is False
    assert "status boom" in by_name["beta"]["error"]
    assert payload["fail_count"] == 1


def test_workspace_doctor_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ISSUEFLOW_LOCKED", raising=False)
    workspace = _make_members(tmp_path)
    console = Console(record=True)
    code = run_workspace_doctor(workspace, console, as_json=True)
    assert code == 0
    payload = _json(console.export_text())
    assert payload["ok"] is True
    assert len(payload["members"]) == 2
    for member in payload["members"]:
        assert "audit" in member
        assert "findings" in member["audit"]


def test_workspace_dirty_classes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ISSUEFLOW_LOCKED", raising=False)
    workspace = _make_members(tmp_path)
    alpha = workspace / "alpha"
    beta = workspace / "beta"
    _git_init(alpha)
    _git_init(beta)
    (alpha / ".issueflows" / "note.md").write_text("tracking\n", encoding="utf-8")
    (beta / "src.py").write_text("print(1)\n", encoding="utf-8")

    console = Console(record=True)
    code = run_workspace_dirty(workspace, console, as_json=True)
    assert code == 0
    payload = _json(console.export_text())
    by_name = {m["name"]: m for m in payload["members"]}
    assert by_name["alpha"]["class"] == "issueflows_only"
    assert by_name["alpha"]["issueflows_only"] is True
    assert by_name["beta"]["class"] == "mixed"
    assert "src.py" in by_name["beta"]["dirty_paths"]


def test_workspace_cli_status_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ISSUEFLOW_LOCKED", raising=False)
    workspace = _make_members(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app, ["workspace", "status", str(workspace), "--local", "--json"]
    )
    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["ok"] is True
    assert payload["ok_count"] == 2
