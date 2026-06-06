"""Tests for issue_flow.graphify (graphify CLI integration helpers)."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from rich.console import Console

from issue_flow import graphify as graphify_module
from issue_flow.graphify import (
    GRAPHIFY_COMMAND,
    find_orphan_install,
    is_available,
    register_with_editor,
    run_build,
)


def _fake_console() -> tuple[Console, StringIO]:
    """A Console whose output is captured to a StringIO for assertion."""
    buffer = StringIO()
    return Console(file=buffer, width=120, force_terminal=False), buffer


def test_is_available_returns_true_when_graphify_on_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(graphify_module.shutil, "which", lambda cmd: "/usr/bin/graphify" if cmd == GRAPHIFY_COMMAND else None)
    assert is_available() is True


def test_is_available_returns_false_when_graphify_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    assert is_available() is False


def test_register_with_editor_skips_when_graphify_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When graphify is not on PATH, register_with_editor returns False, prints hints, and never calls subprocess."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    # Isolate from any real graphify install on the dev machine; we want
    # the "not installed at all" hint branch here, not the orphan branch.
    monkeypatch.setattr(graphify_module, "_candidate_install_locations", lambda: [])

    def fail_run(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("subprocess.run must not be called when graphify is missing")

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)
    console, buffer = _fake_console()

    result = register_with_editor(tmp_path, console)

    assert result is False
    text = buffer.getvalue()
    assert "not on PATH" in text
    assert "graphifyy" in text  # install hint mentions the PyPI package


def test_register_with_editor_runs_install_when_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        graphify_module.shutil, "which", lambda cmd: "/usr/bin/graphify" if cmd == GRAPHIFY_COMMAND else None
    )

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0
        stderr = ""

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)
    console, buffer = _fake_console()

    result = register_with_editor(tmp_path, console)

    assert result is True
    assert captured["cmd"] == [GRAPHIFY_COMMAND, "cursor", "install"]
    assert captured["cwd"] == tmp_path
    assert "registered" in buffer.getvalue().lower()


def test_register_with_editor_does_not_raise_on_nonzero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-zero exit from `graphify cursor install` must not break init/update."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    class _Result:
        returncode = 7
        stderr = "boom\n"

    monkeypatch.setattr(graphify_module.subprocess, "run", lambda *a, **kw: _Result())
    console, buffer = _fake_console()

    result = register_with_editor(tmp_path, console)

    assert result is False
    text = buffer.getvalue()
    assert "code 7" in text
    assert "continuing" in text


def test_register_with_editor_swallows_oserror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If subprocess raises OSError (e.g. binary unexpectedly missing), we recover."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    def boom(*_a: Any, **_kw: Any) -> Any:
        raise OSError("permission denied")

    monkeypatch.setattr(graphify_module.subprocess, "run", boom)
    console, buffer = _fake_console()

    result = register_with_editor(tmp_path, console)

    assert result is False
    assert "permission denied" in buffer.getvalue()


def test_run_build_returns_2_and_prints_hints_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    monkeypatch.setattr(graphify_module, "_candidate_install_locations", lambda: [])

    def fail_run(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("subprocess.run must not be called when graphify is missing")

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)
    console, buffer = _fake_console()

    exit_code = run_build(tmp_path, [], console)

    assert exit_code == 2
    text = buffer.getvalue()
    assert "not installed" in text.lower() or "not found on PATH" in text
    assert "graphifyy" in text


def test_run_build_no_args_uses_default_update_subcommand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`issue-flow graphify` with no args must invoke `graphify update <root>`.

    graphify is subcommand-based — `graphify <path>` alone fails with
    `unknown command`. The default action for a "build" is `update`
    (AST-only, no LLM API key required) so first-time builds work
    without configuration. Users opt into the semantic LLM pass via
    ``issue-flow graphify extract``.
    """
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)
    console, _buffer = _fake_console()

    exit_code = run_build(tmp_path, [], console)

    assert exit_code == 0
    assert captured["cmd"] == [GRAPHIFY_COMMAND, "update", str(tmp_path)]
    assert captured["cwd"] == tmp_path


def test_run_build_respects_explicit_subcommand_and_forwards_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leading build subcommand picks the action; trailing flags forward verbatim."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)
    console, _buffer = _fake_console()

    exit_code = run_build(
        tmp_path, ["cluster-only", "--no-viz"], console
    )

    assert exit_code == 0
    # Project root must still be injected after the subcommand because
    # the user did not pass an explicit path.
    assert captured["cmd"] == [
        GRAPHIFY_COMMAND,
        "cluster-only",
        str(tmp_path),
        "--no-viz",
    ]


def test_run_build_update_subcommand_injects_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`issue-flow graphify update` → `graphify update <project_root>`."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)
    console, _buffer = _fake_console()

    run_build(tmp_path, ["update"], console)

    assert captured["cmd"] == [GRAPHIFY_COMMAND, "update", str(tmp_path)]


def test_run_build_subcommand_with_explicit_path_is_trusted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the user supplies both subcommand and path, do not double-add."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)
    console, _buffer = _fake_console()

    run_build(tmp_path, ["extract", "./docs", "--no-cluster"], console)

    assert captured["cmd"] == [
        GRAPHIFY_COMMAND,
        "extract",
        "./docs",
        "--no-cluster",
    ]


def test_run_build_does_not_inject_path_when_user_supplied_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`issue-flow graphify ./docs` → `graphify update ./docs` (no double path)."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)
    console, _buffer = _fake_console()

    run_build(tmp_path, ["./docs"], console)

    # Subcommand defaulted to update; the only positional after it is
    # the user's "./docs" — not the project root.
    assert captured["cmd"] == [GRAPHIFY_COMMAND, "update", "./docs"]


def test_run_build_leading_flag_falls_back_to_default_subcommand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leading flag (no subcommand, no path) → `update <project_root> <flag>`."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)
    console, _buffer = _fake_console()

    run_build(tmp_path, ["--force"], console)

    assert captured["cmd"] == [
        GRAPHIFY_COMMAND,
        "update",
        str(tmp_path),
        "--force",
    ]


def test_run_build_propagates_nonzero_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    class _Result:
        returncode = 5

    monkeypatch.setattr(graphify_module.subprocess, "run", lambda *a, **kw: _Result())
    console, _buffer = _fake_console()

    assert run_build(tmp_path, [], console) == 5


def test_run_build_returns_1_on_oserror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    def boom(*_a: Any, **_kw: Any) -> Any:
        raise OSError("exec format error")

    monkeypatch.setattr(graphify_module.subprocess, "run", boom)
    console, buffer = _fake_console()

    exit_code = run_build(tmp_path, [], console)

    assert exit_code == 1
    assert "exec format error" in buffer.getvalue()


def test_find_orphan_install_returns_none_when_on_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If graphify is already on PATH, the orphan question is moot."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")
    assert find_orphan_install() is None


def test_find_orphan_install_returns_none_when_no_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No graphify on PATH and no candidate install path → no orphan."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    monkeypatch.setattr(graphify_module, "_candidate_install_locations", lambda: [])
    assert find_orphan_install() is None


def test_find_orphan_install_returns_path_when_unreachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A graphify binary in a candidate dir that is not on PATH counts as an orphan."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    fake_bin = tmp_path / "graphify"
    fake_bin.write_text("#!/usr/bin/env python3\n")
    monkeypatch.setattr(
        graphify_module, "_candidate_install_locations", lambda: [fake_bin]
    )

    result = find_orphan_install()

    assert result == fake_bin


def test_install_hints_include_orphan_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When an orphan binary exists, hints must point at it and recommend update-shell."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    fake_bin = tmp_path / "fake_local_bin" / "graphify"
    fake_bin.parent.mkdir()
    fake_bin.write_text("shim")
    monkeypatch.setattr(
        graphify_module, "_candidate_install_locations", lambda: [fake_bin]
    )
    console, buffer = _fake_console()

    graphify_module._print_install_hints(console)

    text = buffer.getvalue()
    assert str(fake_bin) in text
    assert "PATH" in text
    assert "uv tool update-shell" in text


def test_install_hints_include_path_advice_when_no_orphan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When graphify is plainly missing, hints still mention the update-shell escape hatch."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    monkeypatch.setattr(graphify_module, "_candidate_install_locations", lambda: [])
    console, buffer = _fake_console()

    graphify_module._print_install_hints(console)

    text = buffer.getvalue()
    assert "graphifyy" in text
    assert "update-shell" in text
    # And the standard install snippets are still printed.
    assert "uv tool install" in text
