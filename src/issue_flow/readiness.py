"""Project readiness probing for ``/iflow-setup`` (issue #246).

Answers one question deterministically: *is this directory ready to run the
issue-flow workflow, and if not, what is missing and in what order?*

Everything here is **read-only** — file probes, ``shutil.which``, and git/gh
commands that never prompt. Nothing is created, no command is suggested to the
shell, and a completely bare directory is a valid input. The guided remediation
(asking the user, running ``uv init`` / ``git init`` / ``gh repo create``) lives
in the ``iflow-setup`` skill, not here: this module supplies the facts it acts on.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from issue_flow import gitutils, modes
from issue_flow.config import Settings

# Directory entries that do not make a folder count as an "existing project":
# issue-flow's own scaffold output, plus the paperwork a freshly created GitHub
# repository arrives with. Anything starting with "." is ignored too.
_IGNORED_ENTRIES = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "LICENSE",
        "LICENSE.md",
        "LICENSE.txt",
        "README.md",
        "__pycache__",
        "docs",
    }
)

# Install hints for the two tools issue-flow cannot install on the user's
# behalf. Keyed by command; each value is (label, snippet) pairs.
INSTALL_HINTS: dict[str, tuple[tuple[str, str], ...]] = {
    "uv": (
        ("macOS / Linux", "curl -LsSf https://astral.sh/uv/install.sh | sh"),
        ("Windows (winget)", "winget install --id=astral-sh.uv -e"),
        ("pipx", "pipx install uv"),
    ),
    "git": (
        ("macOS (Homebrew)", "brew install git"),
        ("Windows (winget)", "winget install --id Git.Git -e"),
        ("Linux (Debian/Ubuntu)", "sudo apt install git"),
    ),
    "gh": (
        ("macOS (Homebrew)", "brew install gh"),
        ("Windows (winget)", "winget install --id GitHub.cli -e"),
        ("Linux (Debian/Ubuntu)", "sudo apt install gh"),
    ),
}


@dataclass(frozen=True)
class Blocker:
    """One thing standing between the project and a working issue-flow setup.

    ``agent_may_run`` marks the fixes the ``iflow-setup`` skill is allowed to
    execute itself (behind a confirmation). The rest — installing a package
    manager, ``gh auth login``'s interactive browser flow — must be done by the
    user, so the skill prints the command and stops that branch.
    """

    id: str
    summary: str
    fix: str
    agent_may_run: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "summary": self.summary,
            "fix": self.fix,
            "agent_may_run": self.agent_may_run,
        }


@dataclass(frozen=True)
class Readiness:
    """The full readiness picture for one directory."""

    project_root: Path
    tools: dict[str, bool]
    git: dict[str, object]
    github: dict[str, object]
    python: dict[str, object]
    issueflow: dict[str, object]
    project_kind: str
    blockers: list[Blocker] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return "ready" if not self.blockers else "needs_setup"

    def as_dict(self) -> dict[str, object]:
        return {
            "project_root": str(self.project_root),
            "verdict": self.verdict,
            "project_kind": self.project_kind,
            "tools": self.tools,
            "git": self.git,
            "github": self.github,
            "python": self.python,
            "issueflow": self.issueflow,
            "blockers": [b.as_dict() for b in self.blockers],
        }


def _looks_populated(project_root: Path) -> bool:
    """True when the directory holds files beyond tooling scaffolding."""
    try:
        entries = list(project_root.iterdir())
    except OSError:
        return False
    return any(
        not entry.name.startswith(".") and entry.name not in _IGNORED_ENTRIES
        for entry in entries
    )


def _classify_project(
    *, has_pyproject: bool, has_commits: bool, populated: bool
) -> str:
    """Guess whether this is a new or an existing project.

    Deliberately conservative: anything that looks like real content reads as
    ``existing`` so the skill never runs ``uv init`` over someone's code. The
    skill still confirms the guess with the user before acting on it.
    """
    if has_pyproject or has_commits or populated:
        return "existing"
    return "new"


def probe(project_root: Path, settings: Settings | None = None) -> Readiness:
    """Collect the readiness picture for ``project_root``.

    Never raises for a missing tool, a non-repo directory, or an empty folder:
    every absent capability becomes a ``False`` field and, where it matters, an
    entry in ``blockers`` (ordered so fixing them front to back works).
    """
    settings = settings or Settings()
    root = project_root.resolve()

    tools = {
        "uv": shutil.which("uv") is not None,
        "git": gitutils.git_available(),
        "gh": gitutils.gh_available(),
    }

    # `git rev-parse` answers for the *enclosing* work tree, which may be a
    # parent directory. A folder that merely sits inside someone else's repo is
    # not a repo for our purposes, and its commits/remote are not ours either.
    toplevel = gitutils.repo_root(root) if tools["git"] else None
    is_repo = toplevel is not None and toplevel.resolve() == root
    enclosing = str(toplevel) if toplevel is not None and not is_repo else None
    commits = is_repo and gitutils.has_commits(root)
    origin = gitutils.remote_owner_repo(root) if is_repo else None
    git_info: dict[str, object] = {
        "is_repo": is_repo,
        "repo_root": str(toplevel) if toplevel is not None else None,
        "enclosing_repo": enclosing,
        "has_commits": commits,
        "has_origin": origin is not None,
        "origin": f"{origin[0]}/{origin[1]}" if origin else None,
        "current_branch": gitutils.current_branch(root) if is_repo else None,
    }

    authenticated = tools["gh"] and gitutils.gh_authenticated(root)
    github_info: dict[str, object] = {
        "authenticated": authenticated,
        "account": gitutils.gh_account(root) if authenticated else None,
    }

    pyproject = root / "pyproject.toml"
    python_info: dict[str, object] = {
        "has_pyproject": pyproject.is_file(),
        "has_venv": (root / ".venv").is_dir(),
        "python_version_pin": _read_pin(root / ".python-version"),
    }

    cfg_path = settings.config_path(root)
    scaffolded = (root / settings.issueflows_dir).is_dir()
    issueflow_info: dict[str, object] = {
        "scaffolded": scaffolded,
        "mode": modes.read_active_mode(cfg_path),
        "skill_level": modes.read_skill_level(cfg_path),
        "editor": modes.read_persisted_editor(cfg_path),
    }

    project_kind = _classify_project(
        has_pyproject=bool(python_info["has_pyproject"]),
        has_commits=bool(commits),
        populated=_looks_populated(root),
    )

    return Readiness(
        project_root=root,
        tools=tools,
        git=git_info,
        github=github_info,
        python=python_info,
        issueflow=issueflow_info,
        project_kind=project_kind,
        blockers=_blockers(
            tools=tools,
            git_info=git_info,
            github_info=github_info,
            python_info=python_info,
            issueflow_info=issueflow_info,
            project_kind=project_kind,
            root=root,
        ),
    )


def _read_pin(path: Path) -> str | None:
    """First line of ``.python-version``, or ``None``."""
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def _blockers(
    *,
    tools: dict[str, bool],
    git_info: dict[str, object],
    github_info: dict[str, object],
    python_info: dict[str, object],
    issueflow_info: dict[str, object],
    project_kind: str,
    root: Path,
) -> list[Blocker]:
    """Ordered list of what is missing; empty means ready.

    Order is the order a user should fix them in — tools before the things that
    need those tools, authentication before the remote that needs it.
    """
    found: list[Blocker] = []

    if not tools["uv"]:
        found.append(
            Blocker(
                id="uv_missing",
                summary="uv is not installed (issue-flow's default Python toolchain).",
                fix=INSTALL_HINTS["uv"][0][1],
                agent_may_run=False,
            )
        )
    if not tools["git"]:
        found.append(
            Blocker(
                id="git_missing",
                summary="git is not installed.",
                fix=INSTALL_HINTS["git"][0][1],
                agent_may_run=False,
            )
        )
    if not tools["gh"]:
        found.append(
            Blocker(
                id="gh_missing",
                summary="the GitHub CLI (gh) is not installed.",
                fix=INSTALL_HINTS["gh"][0][1],
                agent_may_run=False,
            )
        )

    if not python_info["has_pyproject"]:
        # Only a genuinely new project may be initialised automatically; an
        # existing tree without a pyproject.toml probably uses another
        # toolchain, and issue-flow defers to whatever the project documents.
        new_project = project_kind == "new"
        found.append(
            Blocker(
                id="python_project_missing",
                summary=(
                    "no pyproject.toml — this folder is not a Python project yet."
                    if new_project
                    else "no pyproject.toml; confirm which toolchain this project "
                    "uses before assuming uv."
                ),
                fix=f"uv init {root.name}" if new_project else "ask the user",
                agent_may_run=new_project,
            )
        )

    if not git_info["is_repo"]:
        enclosing = git_info["enclosing_repo"]
        found.append(
            Blocker(
                id="git_repo_missing",
                summary=(
                    "this folder is not a git repository."
                    if not enclosing
                    else "this folder is not a git repository of its own — it "
                    f"sits inside the one at {enclosing}. Running 'git init' "
                    "here would nest a second repo."
                ),
                fix="git init",
                # Nesting a repo inside another is a decision for the user, not
                # something to confirm away in passing.
                agent_may_run=tools["git"] and not enclosing,
            )
        )
    elif not git_info["has_commits"]:
        found.append(
            Blocker(
                id="git_commits_missing",
                summary="the repository has no commits yet.",
                fix='git add -A && git commit -m "Initial commit"',
                agent_may_run=True,
            )
        )

    if tools["gh"] and not github_info["authenticated"]:
        found.append(
            Blocker(
                id="gh_unauthenticated",
                summary="the GitHub CLI is not signed in.",
                fix="gh auth login",
                agent_may_run=False,
            )
        )

    if not git_info["has_origin"]:
        found.append(
            Blocker(
                id="git_remote_missing",
                summary="no 'origin' remote — there is no GitHub repository to "
                "track issues in.",
                fix=(
                    f"gh repo create {root.name} --source=. --private "
                    "--remote=origin --push"
                ),
                agent_may_run=bool(github_info["authenticated"]),
            )
        )

    if not issueflow_info["scaffolded"]:
        found.append(
            Blocker(
                id="scaffold_missing",
                summary="issue-flow has not been scaffolded here yet.",
                fix=f"issue-flow init --mode {modes.NOVICE_MODE}",
                agent_may_run=True,
            )
        )

    return found
