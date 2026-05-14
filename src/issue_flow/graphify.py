"""Graphify integration for issue-flow.

Graphify (PyPI: ``graphifyy``, CLI: ``graphify``) turns a project folder
into a queryable knowledge graph that AI coding assistants can read
instead of grepping through files. issue-flow does not bundle graphify
as a hard dependency; it is offered as an optional Python extra
(``issue-flow[graphify]``) and the wiring here is **best-effort**: if
``graphify`` is on ``PATH``, ``init``/``update`` register it with
Cursor; otherwise we just print a hint.

This module owns three small responsibilities:

* :func:`is_available` — cheap PATH lookup, no subprocess.
* :func:`register_with_cursor` — runs ``graphify cursor install`` from
  ``init``/``update``. Never raises; failures are logged and ignored.
* :func:`run_build` — backs the ``issue-flow build`` CLI command and the
  ``/build`` slash command. Forwards every extra arg verbatim so the
  upstream graphify flag set is the source of truth.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from rich.console import Console

from issue_flow.dependencies import RECOMMENDED_DEPENDENCIES

GRAPHIFY_COMMAND = "graphify"
GRAPHIFY_PYPI = "graphifyy"


def _graphify_dependency():
    """Return the ``Dependency`` entry for graphify from the recommended list."""
    for dep in RECOMMENDED_DEPENDENCIES:
        if dep.command == GRAPHIFY_COMMAND:
            return dep
    raise RuntimeError(
        "graphify is missing from RECOMMENDED_DEPENDENCIES; "
        "this should never happen."
    )


def is_available() -> bool:
    """True iff the ``graphify`` CLI is on the user's ``PATH``."""
    return shutil.which(GRAPHIFY_COMMAND) is not None


def _print_install_hints(console: Console) -> None:
    dep = _graphify_dependency()
    console.print(
        f"  [dim]Install graphify to enable:[/dim] "
        f"[bold]{dep.command}[/bold] not found on PATH."
    )
    for label, snippet in dep.install_hints:
        console.print(f"    - {label}: [green]{snippet}[/green]")
    console.print(f"  [dim]Docs:[/dim] [blue]{dep.docs_url}[/blue]")


def register_with_cursor(project_root: Path, console: Console) -> bool:
    """Best-effort ``graphify cursor install`` in ``project_root``.

    Returns ``True`` when the install command was attempted and exited
    cleanly, ``False`` otherwise. Never raises — graphify is optional,
    so a failure here must not break ``issue-flow init`` / ``update``.
    """
    if not is_available():
        console.print(
            f"  [dim]skip[/dim]  graphify integration "
            f"([cyan]{GRAPHIFY_COMMAND}[/cyan] not on PATH)"
        )
        _print_install_hints(console)
        return False

    console.print(
        f"  [green]run[/green]   {GRAPHIFY_COMMAND} cursor install"
    )
    try:
        result = subprocess.run(
            [GRAPHIFY_COMMAND, "cursor", "install"],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        console.print(
            f"  [yellow]warn[/yellow]  could not run "
            f"[cyan]{GRAPHIFY_COMMAND} cursor install[/cyan]: {exc}"
        )
        return False

    if result.returncode != 0:
        console.print(
            f"  [yellow]warn[/yellow]  "
            f"[cyan]{GRAPHIFY_COMMAND} cursor install[/cyan] exited with "
            f"code {result.returncode}; continuing."
        )
        if result.stderr:
            # Indent stderr so it visually nests under the warning.
            for line in result.stderr.strip().splitlines()[:5]:
                console.print(f"    [dim]{line}[/dim]")
        return False

    console.print(
        "  [green]ok[/green]    graphify Cursor skill registered"
    )
    return True


def run_build(
    project_root: Path,
    extra_args: Sequence[str],
    console: Console,
) -> int:
    """Run ``graphify <project_root> [extra_args...]`` and return its exit code.

    When the user supplies an explicit path in ``extra_args`` (e.g.
    ``issue-flow build ./docs``), it is forwarded as-is and we do not
    inject the project root. Otherwise the project root is passed
    explicitly so graphify knows what to scan even if the agent's CWD
    differs from the project root.

    Returns ``2`` and prints install hints when graphify is missing.
    Re-raises ``KeyboardInterrupt`` so users can ^C a long build.
    """
    if not is_available():
        console.print(
            "[bold yellow]Graphify is not installed.[/bold yellow] "
            f"The [cyan]{GRAPHIFY_COMMAND}[/cyan] CLI was not found on PATH."
        )
        _print_install_hints(console)
        return 2

    cmd: list[str] = [GRAPHIFY_COMMAND]
    args_list = list(extra_args)
    # Only inject the project root when the user did not supply a leading
    # positional argument. We use a deliberately narrow rule (first token
    # is a flag, or there are no tokens) so we do not misclassify a flag
    # value like ``deep`` after ``--mode`` as a path.
    has_explicit_path = bool(args_list) and not args_list[0].startswith("-")
    if not has_explicit_path:
        cmd.append(str(project_root))
    cmd.extend(args_list)

    console.print(
        "[dim]running:[/dim] [bold]"
        + " ".join(cmd)
        + "[/bold]\n"
    )
    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
    except OSError as exc:
        console.print(
            f"[red]error[/red]  could not invoke [cyan]{GRAPHIFY_COMMAND}[/cyan]: {exc}"
        )
        return 1

    return result.returncode
