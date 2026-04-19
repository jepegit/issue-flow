"""Tests for issue_flow.dependencies (external CLI dependency check)."""

from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from issue_flow import dependencies as deps_module
from issue_flow.dependencies import (
    REQUIRED_DEPENDENCIES,
    Dependency,
    check_dependencies,
    format_missing_report,
    prompt_or_skip,
)


def _fake_console() -> tuple[Console, StringIO]:
    """A Console whose output is captured to a StringIO for assertion."""
    buffer = StringIO()
    return Console(file=buffer, width=120, force_terminal=False), buffer


def test_required_dependencies_are_git_and_gh() -> None:
    """The plan explicitly scopes the check to git + gh (no uv)."""
    commands = {dep.command for dep in REQUIRED_DEPENDENCIES}
    assert commands == {"git", "gh"}


def test_check_dependencies_returns_empty_when_all_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deps_module.shutil, "which", lambda _cmd: "/usr/bin/fake")

    assert check_dependencies() == []


def test_check_dependencies_returns_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def which(cmd: str) -> str | None:
        return None if cmd == "gh" else "/usr/bin/fake"

    monkeypatch.setattr(deps_module.shutil, "which", which)

    missing = check_dependencies()

    assert [dep.command for dep in missing] == ["gh"]


def test_check_dependencies_accepts_custom_dependency_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Caller-supplied dependency list is honored (useful for tests)."""
    monkeypatch.setattr(deps_module.shutil, "which", lambda _cmd: None)
    custom = (
        Dependency(
            name="Fake",
            command="fake-tool",
            purpose="test",
            docs_url="https://example.invalid",
            install_hints=(("any", "install fake-tool"),),
        ),
    )

    missing = check_dependencies(custom)

    assert [dep.command for dep in missing] == ["fake-tool"]


def test_format_missing_report_mentions_name_command_and_install_hints() -> None:
    console, buffer = _fake_console()
    dep = REQUIRED_DEPENDENCIES[-1]  # gh

    format_missing_report([dep], console)

    output = buffer.getvalue()
    assert dep.name in output
    assert dep.command in output
    assert dep.docs_url in output
    for label, snippet in dep.install_hints:
        assert label in output
        assert snippet in output


def test_format_missing_report_is_silent_when_nothing_missing() -> None:
    console, buffer = _fake_console()

    format_missing_report([], console)

    assert buffer.getvalue() == ""


def test_prompt_or_skip_returns_true_when_nothing_missing() -> None:
    console, buffer = _fake_console()

    assert prompt_or_skip([], console, skip=False, stdin_is_tty=True) is True
    assert buffer.getvalue() == ""


def test_prompt_or_skip_bypasses_prompt_when_skip_flag_set() -> None:
    console, buffer = _fake_console()
    dep = REQUIRED_DEPENDENCIES[0]

    result = prompt_or_skip([dep], console, skip=True, stdin_is_tty=True)

    assert result is True
    assert "bypassed" in buffer.getvalue()


def test_prompt_or_skip_bypasses_prompt_on_non_tty() -> None:
    console, buffer = _fake_console()
    dep = REQUIRED_DEPENDENCIES[0]

    result = prompt_or_skip([dep], console, skip=False, stdin_is_tty=False)

    assert result is True
    assert "Non-interactive" in buffer.getvalue()


def test_prompt_or_skip_calls_typer_confirm_on_tty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When stdin is a TTY and user declines, prompt_or_skip returns False."""
    console, _ = _fake_console()
    dep = REQUIRED_DEPENDENCIES[0]

    import typer

    calls: list[str] = []

    def fake_confirm(prompt: str, default: bool = False) -> bool:  # noqa: ARG001
        calls.append(prompt)
        return False

    monkeypatch.setattr(typer, "confirm", fake_confirm)

    result = prompt_or_skip([dep], console, skip=False, stdin_is_tty=True)

    assert result is False
    assert len(calls) == 1
    assert "Continue" in calls[0]


def test_prompt_or_skip_accepts_tty_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the user confirms at the prompt, proceed."""
    console, _ = _fake_console()
    dep = REQUIRED_DEPENDENCIES[0]

    import typer

    monkeypatch.setattr(typer, "confirm", lambda *_a, **_kw: True)

    assert prompt_or_skip([dep], console, skip=False, stdin_is_tty=True) is True
