"""Graphify integration for issue-flow.

Graphify (PyPI: ``graphifyy``, CLI: ``graphify``) turns a project folder
into a queryable knowledge graph that AI coding assistants can read
instead of grepping through files. issue-flow does **not** bundle
graphify and does not declare it as a Python dependency — neither hard
nor optional-extra. Users install ``graphifyy`` as its own standalone
tool (``uv tool install graphifyy``), the same way they install
issue-flow. The wiring here is **best-effort**: if ``graphify`` is on
``PATH``, ``init``/``update`` register it with Cursor; otherwise we
just print a hint and continue.

This module owns three small responsibilities:

* :func:`is_available` — cheap PATH lookup, no subprocess.
* :func:`register_with_editor` — runs ``graphify <installer> install`` from
  ``init``/``update`` (only ``cursor`` exists today). Never raises; failures
  are logged and ignored.
* :func:`run_build` — backs the ``issue-flow graphify`` CLI command and
  the ``/graphify`` slash command. Forwards every extra arg verbatim so
  the upstream graphify flag set is the source of truth.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from rich.console import Console

from issue_flow.dependencies import RECOMMENDED_DEPENDENCIES

GRAPHIFY_COMMAND = "graphify"
GRAPHIFY_PYPI = "graphifyy"

# Graphify is a multi-subcommand CLI. The subcommands below all take a
# project path as their first positional argument and are the ones that
# fit the "build / refresh the graph" surface ``issue-flow graphify``
# exposes. Anything else (``query``, ``explain``, ``cursor install``,
# …) is out of scope for ``graphify``; users invoke ``graphify`` directly
# for those.
_GRAPHIFY_BUILD_SUBCOMMANDS: frozenset[str] = frozenset(
    {"extract", "update", "watch", "cluster-only", "check-update"}
)
# Default subcommand when the user runs ``issue-flow graphify`` without
# specifying one. ``update`` is the AST-only build: it produces the
# full ``graphify-out/`` (``graph.json``, ``graph.html``,
# ``GRAPH_REPORT.md``) and crucially does **not** need an LLM API key,
# so the no-arg case "just works" for first-time users. Power users
# pick ``extract`` explicitly when they want the slower semantic LLM
# pass that surfaces richer cross-file relationships.
_DEFAULT_BUILD_SUBCOMMAND: str = "update"


def _build_graphify_argv(
    project_root: Path, extra_args: Sequence[str]
) -> list[str]:
    """Translate ``issue-flow graphify`` arguments into a ``graphify`` argv.

    ``graphify`` is subcommand-based — there is no top-level "scan this
    folder" mode — so every invocation needs an explicit subcommand.
    Behavior:

    * No extra args → ``graphify update <project_root>``. ``update``
      is AST-only and needs no LLM API key, so the no-arg case "just
      works" for users who have not configured a backend yet.
    * First arg is a recognized build subcommand (``extract``,
      ``update``, ``watch``, ``cluster-only``, ``check-update``) → use
      it. If a positional path follows, trust it; otherwise inject
      ``project_root`` so graphify scans the right tree even when the
      agent's cwd differs from the project root.
    * First arg is anything else → assume the default subcommand
      (``update``) and treat the args as positional/flag tail. A
      first arg that does not start with ``-`` is taken as the path
      the user wants graphify to scan (e.g. ``issue-flow graphify ./docs``
      → ``graphify update ./docs``).
    """
    args = list(extra_args)

    if args and args[0] in _GRAPHIFY_BUILD_SUBCOMMANDS:
        subcommand = args[0]
        rest = args[1:]
    else:
        subcommand = _DEFAULT_BUILD_SUBCOMMAND
        rest = args

    has_explicit_path = bool(rest) and not rest[0].startswith("-")
    if has_explicit_path:
        positional_tail = rest
    else:
        positional_tail = [str(project_root), *rest]

    return [GRAPHIFY_COMMAND, subcommand, *positional_tail]


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


def _candidate_install_locations() -> list[Path]:
    """Well-known install locations to probe when ``graphify`` is missing from PATH.

    Covers the common case where the user did install ``graphifyy`` but
    the install directory was never added to ``PATH`` (e.g. fresh
    ``uv tool install`` followed by no ``uv tool update-shell`` and no
    shell restart).

    The list is best-effort and intentionally short. We do not try to
    enumerate every Python user-base layout — ``uv tool`` and modern
    ``pipx`` both default to ``~/.local/bin``, which catches the vast
    majority of installs across Linux, macOS, and Windows.
    """
    home = Path.home()
    exe = ".exe" if sys.platform == "win32" else ""
    binary = f"{GRAPHIFY_COMMAND}{exe}"

    candidates: list[Path] = [
        home / ".local" / "bin" / binary,
    ]

    if sys.platform == "win32":
        # pipx default on Windows historically used %USERPROFILE%\AppData\Roaming\Python\Scripts.
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "Python" / "Scripts" / binary)
        # pip --user fallback.
        candidates.append(home / "AppData" / "Roaming" / "Python" / "Scripts" / binary)

    return candidates


def find_orphan_install() -> Path | None:
    """Return the path of an installed-but-not-on-PATH ``graphify`` binary, if any.

    ``None`` if no candidate location contains a ``graphify`` executable
    or if ``graphify`` is already on PATH (in which case this question
    is moot).
    """
    if is_available():
        return None
    for path in _candidate_install_locations():
        try:
            if path.is_file():
                return path
        except OSError:
            # Permission errors or weird filesystem states — keep looking.
            continue
    return None


def _print_install_hints(console: Console) -> None:
    """Print the install / not-on-PATH hint block.

    Two flavors:

    * **Not installed** — print the normal install snippets.
    * **Installed but not on PATH** — point at the orphan binary and
      tell the user to run ``uv tool update-shell`` (or restart their
      shell / Cursor) so the new directory becomes visible.
    """
    dep = _graphify_dependency()

    orphan = find_orphan_install()
    if orphan is not None:
        console.print(
            f"  [yellow]Found[/yellow] [cyan]{orphan}[/cyan] but its directory is not on [bold]PATH[/bold]."
        )
        console.print(
            f"  [dim]Fix:[/dim] add [cyan]{orphan.parent}[/cyan] to PATH, "
            "then restart your shell (and Cursor)."
        )
        console.print(
            "  [dim]With uv:[/dim] [green]uv tool update-shell[/green] "
            "(refreshes the shell rc files; restart afterwards)."
        )
        console.print(f"  [dim]Docs:[/dim] [blue]{dep.docs_url}[/blue]")
        return

    console.print(
        f"  [dim]Install graphify to enable:[/dim] "
        f"[bold]{dep.command}[/bold] not found on PATH."
    )
    for label, snippet in dep.install_hints:
        console.print(f"    - {label}: [green]{snippet}[/green]")
    console.print(
        "  [dim]Already installed?[/dim] If you just ran "
        "[green]uv tool install graphifyy[/green], make sure uv's bin "
        "directory is on PATH ([green]uv tool update-shell[/green]) and "
        "restart your shell (and Cursor) so the new tool is picked up."
    )
    console.print(f"  [dim]Docs:[/dim] [blue]{dep.docs_url}[/blue]")


def register_with_editor(
    project_root: Path, console: Console, installer: str = "cursor"
) -> bool:
    """Best-effort ``graphify <installer> install`` in ``project_root``.

    ``installer`` is the graphify integration sub-command for the target
    editor (only ``"cursor"`` exists today). Returns ``True`` when the install
    command was attempted and exited cleanly, ``False`` otherwise. Never
    raises — graphify is optional, so a failure here must not break
    ``issue-flow init`` / ``update``.
    """
    if not is_available():
        console.print(
            f"  [dim]skip[/dim]  graphify integration "
            f"([cyan]{GRAPHIFY_COMMAND}[/cyan] not on PATH)"
        )
        _print_install_hints(console)
        return False

    console.print(
        f"  [green]run[/green]   {GRAPHIFY_COMMAND} {installer} install"
    )
    try:
        result = subprocess.run(
            [GRAPHIFY_COMMAND, installer, "install"],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        console.print(
            f"  [yellow]warn[/yellow]  could not run "
            f"[cyan]{GRAPHIFY_COMMAND} {installer} install[/cyan]: {exc}"
        )
        return False

    if result.returncode != 0:
        console.print(
            f"  [yellow]warn[/yellow]  "
            f"[cyan]{GRAPHIFY_COMMAND} {installer} install[/cyan] exited with "
            f"code {result.returncode}; continuing."
        )
        if result.stderr:
            # Indent stderr so it visually nests under the warning.
            for line in result.stderr.strip().splitlines()[:5]:
                console.print(f"    [dim]{line}[/dim]")
        return False

    console.print(
        f"  [green]ok[/green]    graphify {installer} skill registered"
    )
    return True


def run_build(
    project_root: Path,
    extra_args: Sequence[str],
    console: Console,
) -> int:
    """Run ``graphify <subcommand> <path> [extra_args...]`` and return its exit code.

    See :func:`_build_graphify_argv` for the argv-construction rules.
    The short version: ``issue-flow graphify`` with no args invokes
    ``graphify update <project_root>`` (AST-only, no LLM API key
    required, produces the full ``graphify-out/`` directory). Users
    who want the deeper semantic LLM pass run
    ``issue-flow graphify extract`` and configure a backend
    (``GEMINI_API_KEY`` / ``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY`` /
    ``MOONSHOT_API_KEY`` env var, or ``--backend ollama`` for a local
    LLM).

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

    cmd = _build_graphify_argv(project_root, extra_args)

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
