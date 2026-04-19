"""External CLI dependency detection for issue-flow.

The scaffolded workflow shells out to ``git`` and ``gh`` (GitHub CLI) via
slash commands. We detect missing tools at ``issue-flow init`` /
``issue-flow update`` time so users get a clear install hint rather than a
confusing failure later from inside a Cursor command.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass

from rich.console import Console


@dataclass(frozen=True)
class Dependency:
    """A single external CLI tool issue-flow's workflow depends on."""

    name: str
    command: str
    purpose: str
    docs_url: str
    # Platform hint → short install snippet. Keys are free-form labels
    # shown verbatim (e.g. "macOS (Homebrew)", "Windows (winget)", "Linux
    # (Debian/Ubuntu)"). Values are one-line commands.
    install_hints: tuple[tuple[str, str], ...]


# The scaffolded slash commands (see
# ``src/issue_flow/templates/commands/*.md.j2``) invoke these tools. ``uv``
# is intentionally *not* listed here: it is an install-time prerequisite
# for issue-flow itself, not something the scaffold calls at runtime, so
# it belongs in the README only.
REQUIRED_DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency(
        name="Git",
        command="git",
        purpose=(
            "Used by every slash command for branch, fetch, status, "
            "commit, and push operations."
        ),
        docs_url="https://git-scm.com/downloads",
        install_hints=(
            ("macOS (Homebrew)", "brew install git"),
            ("Windows (winget)", "winget install --id Git.Git -e"),
            ("Linux (Debian/Ubuntu)", "sudo apt install git"),
        ),
    ),
    Dependency(
        name="GitHub CLI",
        command="gh",
        purpose=(
            "Used by /issue-init to fetch issues, /issue-close to open "
            "PRs, and /issue-cleanup to check PR merge status. Remember "
            "to run `gh auth login` once after installing."
        ),
        docs_url="https://cli.github.com/",
        install_hints=(
            ("macOS (Homebrew)", "brew install gh"),
            ("Windows (winget)", "winget install --id GitHub.cli -e"),
            (
                "Linux (Debian/Ubuntu)",
                "sudo apt install gh  # or see https://cli.github.com/ for the official repo",
            ),
        ),
    ),
)


def check_dependencies(
    dependencies: tuple[Dependency, ...] = REQUIRED_DEPENDENCIES,
) -> list[Dependency]:
    """Return the subset of ``dependencies`` whose ``command`` is not on ``PATH``.

    Uses :func:`shutil.which` only — no subprocess invocations — so it is
    safe to call on any platform without risk of hanging or prompting.
    """
    return [dep for dep in dependencies if shutil.which(dep.command) is None]


def format_missing_report(
    missing: list[Dependency],
    console: Console,
) -> None:
    """Print a human-readable report listing missing dependencies.

    The output is intentionally compact and uses only ``rich`` markup so
    it blends with the rest of the ``init`` output.
    """
    if not missing:
        return

    count = len(missing)
    noun = "dependency" if count == 1 else "dependencies"
    console.print(
        f"[bold yellow]Missing {count} external {noun}:[/bold yellow]"
    )
    for dep in missing:
        console.print(
            f"\n  [bold]{dep.name}[/bold]  "
            f"([cyan]{dep.command}[/cyan] not found on PATH)"
        )
        console.print(f"    [dim]{dep.purpose}[/dim]")
        console.print(f"    Docs: [blue]{dep.docs_url}[/blue]")
        console.print("    Install:")
        for label, snippet in dep.install_hints:
            console.print(f"      - {label}: [green]{snippet}[/green]")
    console.print()


def prompt_or_skip(
    missing: list[Dependency],
    console: Console,
    *,
    skip: bool,
    stdin_is_tty: bool | None = None,
) -> bool:
    """Decide whether to proceed despite missing deps.

    Returns ``True`` to continue, ``False`` if the user declined.

    - If ``missing`` is empty, returns ``True``.
    - If ``skip`` is ``True``, prints a one-line note and returns ``True``
      without prompting.
    - If stdin is not a TTY (e.g. CI, piped input), prints a one-line
      note and returns ``True`` without prompting so automation doesn't
      hang.
    - Otherwise asks the user with :func:`typer.confirm`.
    """
    if not missing:
        return True

    format_missing_report(missing, console)

    if skip:
        console.print(
            "[dim]Dependency check bypassed via --skip-dep-check; "
            "continuing anyway.[/dim]\n"
        )
        return True

    if stdin_is_tty is None:
        stdin_is_tty = sys.stdin.isatty()

    if not stdin_is_tty:
        console.print(
            "[dim]Non-interactive session (stdin is not a TTY); "
            "continuing without prompting. "
            "Install the tools above before running the slash commands.[/dim]\n"
        )
        return True

    # Imported lazily to keep this module importable in environments
    # that only need check_dependencies (e.g. tests or custom scripts).
    import typer

    return typer.confirm(
        "Continue with issue-flow setup anyway?", default=False
    )
