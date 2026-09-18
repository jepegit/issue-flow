"""Tests for the user-global project registry and ``update --all``."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from issue_flow.cli import app
from issue_flow.init import run_init
from issue_flow.user_global import (
    read_registry_roots,
    register_root,
    unregister_root,
    user_global_registry_path,
)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _json(output: str) -> Any:
    return json.loads(_plain(output))


def test_register_rejects_relative(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="absolute"):
        register_root(Path("relative/repo"))


def test_register_and_unregister_roundtrip(tmp_path: Path) -> None:
    root = (tmp_path / "proj").resolve()
    root.mkdir()
    assert register_root(root) is True
    assert register_root(root) is False
    assert read_registry_roots() == [root]
    assert user_global_registry_path().is_file()
    assert unregister_root(root) is True
    assert unregister_root(root) is False
    assert read_registry_roots() == []


def test_init_registers_root(tmp_path: Path) -> None:
    project = tmp_path / "seeded"
    run_init(project, skip_dep_check=True)
    assert project.resolve() in read_registry_roots()


def test_register_unregister_cli(tmp_path: Path) -> None:
    runner = CliRunner()
    project = tmp_path / "cli-proj"
    project.mkdir()

    add = runner.invoke(app, ["register", str(project), "--json"])
    assert add.exit_code == 0, add.output
    added = _json(add.stdout)
    assert added["ok"] is True
    assert added["added"] is True
    assert Path(added["path"]) == project.resolve()

    again = runner.invoke(app, ["register", str(project), "--json"])
    assert again.exit_code == 0, again.output
    assert _json(again.stdout)["added"] is False

    drop = runner.invoke(app, ["unregister", str(project), "--json"])
    assert drop.exit_code == 0, drop.output
    removed = _json(drop.stdout)
    assert removed["ok"] is True
    assert removed["removed"] is True
    assert read_registry_roots() == []


def test_update_all_skips_locked_and_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ISSUEFLOW_LOCKED", raising=False)
    unlocked = tmp_path / "unlocked"
    locked = tmp_path / "locked"
    run_init(unlocked, skip_dep_check=True)
    run_init(locked, skip_dep_check=True)
    (locked / ".issueflows" / "config.toml").write_text(
        '[issueflow]\nlocked = true\nmode = "standard"\n',
        encoding="utf-8",
    )
    missing = tmp_path / "gone"
    missing.mkdir()
    register_root(missing.resolve())
    missing.rmdir()

    unlocked_rule = unlocked / ".cursor" / "rules" / "issueflow-rules.mdc"
    unlocked_rule.write_text("STALE_UNLOCKED", encoding="utf-8")
    locked_rule = locked / ".cursor" / "rules" / "issueflow-rules.mdc"
    locked_before = locked_rule.read_text(encoding="utf-8")
    locked_rule.write_text("STALE_LOCKED", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["update", "--all", "--skip-dep-check", "--json"])
    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["ok"] is True
    assert payload["ok_count"] == 1
    assert payload["skip_count"] == 2
    assert payload["fail_count"] == 0
    by_path = {m["path"]: m for m in payload["members"]}
    assert by_path[str(unlocked.resolve())]["skipped"] is False
    assert by_path[str(locked.resolve())]["reason"] == "locked"
    assert by_path[str(missing.resolve())]["reason"] == "missing"
    assert "STALE_UNLOCKED" not in unlocked_rule.read_text(encoding="utf-8")
    assert locked_rule.read_text(encoding="utf-8") == "STALE_LOCKED"
    assert locked_before != "STALE_LOCKED"


def test_register_discover_yes_registers_scaffolds_only(tmp_path: Path) -> None:
    start = tmp_path / "tree"
    one = start / "one"
    two = start / "nested" / "two"
    decoy = start / "decoy"
    too_deep = start / "a" / "b" / "c" / "d" / "e" / "deep"
    one.mkdir(parents=True)
    two.mkdir(parents=True)
    decoy.mkdir(parents=True)
    too_deep.mkdir(parents=True)
    run_init(one, skip_dep_check=True)
    run_init(two, skip_dep_check=True)
    run_init(too_deep, skip_dep_check=True)
    (decoy / "README.md").write_text("not a scaffold\n", encoding="utf-8")

    for root in list(read_registry_roots()):
        unregister_root(root)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["register", str(start), "--discover", "--yes", "--max-depth", "4", "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["ok"] is True
    assert payload["discover"] is True
    added = {Path(p) for p in payload["added"]}
    assert one.resolve() in added
    assert two.resolve() in added
    assert too_deep.resolve() not in added
    assert decoy.resolve() not in {Path(p) for p in payload["candidates"]}
    assert set(read_registry_roots()) == {one.resolve(), two.resolve()}


def test_register_discover_empty_is_ok(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    runner = CliRunner()
    result = runner.invoke(
        app, ["register", str(empty), "--discover", "--yes", "--json"]
    )
    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["candidates"] == []
    assert payload["added"] == []


def test_update_help_lists_all() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["update", "--help"])
    assert result.exit_code == 0
    plain = _plain(result.stdout)
    assert "--all" in plain
    assert "--workspace" in plain
    assert "--force" in plain
    assert "--mode" not in plain


def test_update_workspace_without_all_errors(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["update", str(tmp_path), "--workspace"])
    assert result.exit_code == 2
    assert "--workspace requires --all" in _plain(result.stdout)


def test_update_all_workspace_unions_overlapping_root_once(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "ws"
    alpha = workspace / "alpha"
    beta = workspace / "beta"
    workspace.mkdir()
    run_init(alpha, skip_dep_check=True)
    run_init(beta, skip_dep_check=True)
    (workspace / "issueflow-workspace.toml").write_text(
        '[workspace]\nmembers = ["alpha", "beta", "alpha"]\n',
        encoding="utf-8",
    )

    for root in list(read_registry_roots()):
        unregister_root(root)
    register_root(alpha.resolve())

    runner = CliRunner()
    registry_only = runner.invoke(
        app, ["update", str(workspace), "--all", "--skip-dep-check", "--json"]
    )
    assert registry_only.exit_code == 0, registry_only.output
    registry_payload = _json(registry_only.stdout)
    assert registry_payload["ok_count"] == 1
    assert registry_payload["workspace_root"] is None
    assert {m["path"] for m in registry_payload["members"]} == {str(alpha.resolve())}

    union = runner.invoke(
        app,
        [
            "update",
            str(workspace),
            "--all",
            "--workspace",
            "--skip-dep-check",
            "--json",
        ],
    )
    assert union.exit_code == 0, union.output
    union_payload = _json(union.stdout)
    assert union_payload["ok_count"] == 2
    assert Path(union_payload["workspace_root"]) == workspace.resolve()
    assert [m["path"] for m in union_payload["members"]] == [
        str(alpha.resolve()),
        str(beta.resolve()),
    ]
