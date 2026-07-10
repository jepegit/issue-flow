"""Cross-checks between scaffolded templates and the real CLI surface.

The skills and commands that issue-flow scaffolds tell agents to run
``issue-flow agent <subcommand>`` as a deterministic fast path. Nothing else
ties those strings to the Typer app, so a renamed or removed subcommand would
leave templates pointing at a command that no longer exists — and agents
following the instructions would fail at runtime. These tests pin that
contract by parsing every packaged template and asserting each referenced
command really exists.
"""

from __future__ import annotations

import re
from pathlib import Path

import typer

import issue_flow
from issue_flow.cli import agent_app, app

TEMPLATES_DIR = Path(issue_flow.__file__).parent / "templates"

# ``issue-flow agent <token>`` anywhere in template text. The ``agent`` word
# anchors the match, so prose like "the issue-flow package" cannot trip it.
_AGENT_REF_RE = re.compile(r"issue-flow agent ([a-z][a-z-]*)")

# ``issue-flow <token>`` immediately after a backtick, i.e. the start of an
# inline code span such as `` `issue-flow update` ``. Restricting to code
# spans keeps prose ("the issue-flow workflow") out of scope.
_TOP_REF_RE = re.compile(r"`issue-flow ([a-z][a-z-]*)")


def _template_files() -> list[Path]:
    files = sorted(TEMPLATES_DIR.rglob("*.j2"))
    assert files, "no packaged templates found — did the package layout change?"
    return files


def _command_names(cli: typer.Typer) -> set[str]:
    """Names of the commands registered on a Typer app.

    Commands registered without an explicit name derive it from the callback
    function name, mirroring Typer's own behaviour.
    """
    names: set[str] = set()
    for info in cli.registered_commands:
        name = info.name
        if name is None and info.callback is not None:
            name = info.callback.__name__.replace("_", "-")
        if name:
            names.add(name)
    return names


def _group_names(cli: typer.Typer) -> set[str]:
    """Names of the sub-apps (e.g. ``agent``, ``config``) added to an app.

    Typer wraps unset values in a ``DefaultPlaceholder`` rather than ``None``,
    so pick the first candidate that is a real string: the ``add_typer``
    override first, then the sub-app's own ``Typer(name=...)``.
    """
    names: set[str] = set()
    for group in cli.registered_groups:
        candidates = [group.name]
        if group.typer_instance is not None:
            candidates.append(group.typer_instance.info.name)
        for candidate in candidates:
            if isinstance(candidate, str) and candidate:
                names.add(candidate)
                break
    return names


def test_cli_introspection_sees_expected_surface() -> None:
    """Sanity-check the introspection itself so the other tests can't pass
    vacuously against an empty command set."""
    assert "state" in _command_names(agent_app)
    assert "init" in _command_names(app)
    assert "agent" in _group_names(app)


def test_agent_subcommand_references_exist() -> None:
    """Every `issue-flow agent <cmd>` in the templates is a real subcommand."""
    real = _command_names(agent_app)
    for template in _template_files():
        text = template.read_text(encoding="utf-8")
        for ref in _AGENT_REF_RE.findall(text):
            assert ref in real, (
                f"{template.relative_to(TEMPLATES_DIR)} tells agents to run "
                f"'issue-flow agent {ref}', but the agent app has no such "
                f"subcommand (available: {sorted(real)})"
            )


def test_top_level_command_references_exist() -> None:
    """Every backticked `issue-flow <cmd>` in the templates is a real command."""
    real = _command_names(app) | _group_names(app)
    for template in _template_files():
        text = template.read_text(encoding="utf-8")
        for ref in _TOP_REF_RE.findall(text):
            assert ref in real, (
                f"{template.relative_to(TEMPLATES_DIR)} references "
                f"'issue-flow {ref}', but the CLI has no such command "
                f"(available: {sorted(real)})"
            )
