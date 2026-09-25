"""Tests for ``issue-flow agent self-update`` (issue #382)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from rich.console import Console

from issue_flow.self_update import (
    parse_version_text,
    receipt_is_local,
    run_self_update,
)


def test_parse_version_text() -> None:
    assert parse_version_text("0.5.12\n") == "0.5.12"
    assert parse_version_text("issue-flow, version 0.5.12") == "0.5.12"
    assert parse_version_text("") is None


def test_receipt_is_local_pypi() -> None:
    assert (
        receipt_is_local({"tool": {"requirements": [{"name": "issue-flow"}]}}) is False
    )


def test_receipt_is_local_editable() -> None:
    data = {
        "tool": {
            "requirements": [
                {
                    "name": "issue-flow",
                    "editable": True,
                    "directory": "/tmp/issue-flow",
                }
            ]
        }
    }
    assert receipt_is_local(data) is True
    assert receipt_is_local({"tool": {"requirements": []}}, "editable = true\n") is True
    assert (
        receipt_is_local(
            {"tool": {"requirements": [{"name": "issue-flow", "url": "file:///tmp/x"}]}}
        )
        is True
    )


class _Result:
    def __init__(self, code: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = code
        self.stdout = stdout
        self.stderr = stderr


def _runner(mapping: dict[tuple[str, ...], _Result]):
    def run(argv: list[str], **_kwargs: Any) -> _Result:
        key = tuple(argv)
        for prefix, result in mapping.items():
            if key[: len(prefix)] == prefix:
                return result
        raise AssertionError(f"unexpected argv: {argv}")

    return run


def test_self_update_skips_editable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    receipt = tmp_path / "issue-flow" / "uv-receipt.toml"
    receipt.parent.mkdir()
    receipt.write_text(
        '[tool]\nrequirements = [{ name = "issue-flow", editable = true, '
        'directory = "/tmp/issue-flow" }]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "issue_flow.self_update.shutil.which",
        lambda name: "/bin/true" if name in {"uv", "issue-flow"} else None,
    )
    runner = _runner(
        {
            ("uv", "tool", "dir"): _Result(0, str(tmp_path) + "\n"),
            ("issue-flow", "--version"): _Result(0, "0.5.12\n"),
        }
    )
    code = run_self_update(tmp_path, Console(), True, runner=runner)
    assert code == 0


def test_self_update_upgrades(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = tmp_path / "issue-flow" / "uv-receipt.toml"
    receipt.parent.mkdir()
    receipt.write_text(
        '[tool]\nrequirements = [{ name = "issue-flow" }]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "issue_flow.self_update.shutil.which",
        lambda name: "/bin/true" if name in {"uv", "issue-flow"} else None,
    )
    versions = iter(["0.5.12\n", "0.5.13\n"])
    mapping = {
        ("uv", "tool", "dir"): _Result(0, str(tmp_path) + "\n"),
        ("uv", "tool", "install"): _Result(0, "installed\n"),
        ("issue-flow", "update"): _Result(0, "updated\n"),
    }

    def run(argv: list[str], **_kwargs: Any) -> _Result:
        if tuple(argv[:2]) == ("issue-flow", "--version"):
            return _Result(0, next(versions))
        for prefix, result in mapping.items():
            if tuple(argv[: len(prefix)]) == prefix:
                return result
        raise AssertionError(f"unexpected argv: {argv}")

    code = run_self_update(tmp_path, Console(), True, runner=run)
    assert code == 0


def test_self_update_fails_without_uv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("issue_flow.self_update.shutil.which", lambda _name: None)
    code = run_self_update(tmp_path, Console(), True)
    assert code == 1


def test_self_update_fails_on_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    receipt = tmp_path / "issue-flow" / "uv-receipt.toml"
    receipt.parent.mkdir()
    receipt.write_text(
        '[tool]\nrequirements = [{ name = "issue-flow" }]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "issue_flow.self_update.shutil.which",
        lambda name: "/bin/true" if name in {"uv", "issue-flow"} else None,
    )
    runner = _runner(
        {
            ("uv", "tool", "dir"): _Result(0, str(tmp_path) + "\n"),
            ("issue-flow", "--version"): _Result(0, "0.5.12\n"),
            ("uv", "tool", "install"): _Result(1, "", "network down"),
        }
    )
    code = run_self_update(tmp_path, Console(), True, runner=runner)
    assert code == 1
