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
    register_with_cursor,
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


def test_register_with_cursor_skips_when_graphify_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When graphify is not on PATH, register_with_cursor returns False, prints hints, and never calls subprocess."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)

    def fail_run(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("subprocess.run must not be called when graphify is missing")

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)
    console, buffer = _fake_console()

    result = register_with_cursor(tmp_path, console)

    assert result is False
    text = buffer.getvalue()
    assert "not on PATH" in text
    assert "graphifyy" in text  # install hint mentions the PyPI package


def test_register_with_cursor_runs_install_when_available(
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

    result = register_with_cursor(tmp_path, console)

    assert result is True
    assert captured["cmd"] == [GRAPHIFY_COMMAND, "cursor", "install"]
    assert captured["cwd"] == tmp_path
    assert "registered" in buffer.getvalue().lower()


def test_register_with_cursor_does_not_raise_on_nonzero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-zero exit from `graphify cursor install` must not break init/update."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    class _Result:
        returncode = 7
        stderr = "boom\n"

    monkeypatch.setattr(graphify_module.subprocess, "run", lambda *a, **kw: _Result())
    console, buffer = _fake_console()

    result = register_with_cursor(tmp_path, console)

    assert result is False
    text = buffer.getvalue()
    assert "code 7" in text
    assert "continuing" in text


def test_register_with_cursor_swallows_oserror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If subprocess raises OSError (e.g. binary unexpectedly missing), we recover."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    def boom(*_a: Any, **_kw: Any) -> Any:
        raise OSError("permission denied")

    monkeypatch.setattr(graphify_module.subprocess, "run", boom)
    console, buffer = _fake_console()

    result = register_with_cursor(tmp_path, console)

    assert result is False
    assert "permission denied" in buffer.getvalue()


def test_run_build_returns_2_and_prints_hints_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)

    def fail_run(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("subprocess.run must not be called when graphify is missing")

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)
    console, buffer = _fake_console()

    exit_code = run_build(tmp_path, [], console)

    assert exit_code == 2
    text = buffer.getvalue()
    assert "not installed" in text.lower() or "not found on PATH" in text
    assert "graphifyy" in text


def test_run_build_forwards_args_verbatim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Extra args must pass straight through to graphify."""
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

    exit_code = run_build(tmp_path, ["--update", "--no-viz", "--mode", "deep"], console)

    assert exit_code == 0
    assert captured["cmd"][0] == GRAPHIFY_COMMAND
    # No explicit path argument from the user → run_build inserts the project dir
    assert str(tmp_path) in captured["cmd"]
    assert "--update" in captured["cmd"]
    assert "--no-viz" in captured["cmd"]
    assert "--mode" in captured["cmd"]
    assert "deep" in captured["cmd"]
    assert captured["cwd"] == tmp_path


def test_run_build_does_not_inject_path_when_user_supplied_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the user passes ./subdir, do not also pass the project root."""
    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)
    console, _buffer = _fake_console()

    run_build(tmp_path, ["./docs", "--update"], console)

    # Only one positional arg: the user's "./docs" — not the project root.
    positional = [a for a in captured["cmd"][1:] if not a.startswith("-")]
    assert positional == ["./docs"]


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
