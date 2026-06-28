"""Configuration for issue-flow, backed by .env files and environment variables."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import os

from issue_flow import modes as modes_module
from issue_flow.editors import DEFAULT_EDITOR, EditorProfile, get_profile
from issue_flow.modes import DEFAULT_MODE, Mode


# Load .env from the current working directory (the user's project root).
# This runs at import time so that all downstream code sees the env vars.
load_dotenv(override=False)


@dataclass
class Settings:
    """Runtime settings for issue-flow.

    Values come from environment variables (prefixed with ISSUEFLOW_) with
    sensible defaults.  A .env file in the project root is loaded automatically.
    """

    issueflows_dir: str = field(
        default_factory=lambda: os.getenv("ISSUEFLOW_DIR", ".issueflows")
    )
    editor: str = field(
        default_factory=lambda: os.getenv("ISSUEFLOW_EDITOR", DEFAULT_EDITOR)
    )
    # Explicit ``ISSUEFLOW_AGENT_DIR`` override. When unset (``None``) the agent
    # directory is derived from the selected editor profile instead.
    agent_dir_override: str | None = field(
        default_factory=lambda: os.getenv("ISSUEFLOW_AGENT_DIR")
    )
    docs_dir: str = field(
        default_factory=lambda: os.getenv("ISSUEFLOW_DOCS_DIR", "docs")
    )
    history_file: str = field(
        default_factory=lambda: os.getenv("ISSUEFLOW_HISTORY_FILE", "HISTORY.md")
    )

    # Give a deprecation warning if the user is using the old ISSUEFLOW_CURSOR_DIR environment variable
    if os.getenv("ISSUEFLOW_CURSOR_DIR"):
        print("WARNING: The ISSUEFLOW_CURSOR_DIR environment variable is deprecated (replaced by ISSUEFLOW_AGENT_DIR).")

    # Subdirectory names inside .issueflows/
    tools_folder: str = "00-tools"
    current_issues_folder: str = "01-current-issues"
    partly_solved_folder: str = "02-partly-solved-issues"
    solved_folder: str = "03-solved-issues"
    designs_folder: str = "04-designs-and-guides"

    @property
    def issueflows_subdirs(self) -> list[str]:
        return [
            self.tools_folder,
            self.current_issues_folder,
            self.partly_solved_folder,
            self.solved_folder,
            self.designs_folder,
        ]

    def agent_dir_for(self, profile: EditorProfile) -> str:
        """Agent directory for ``profile``: explicit override wins, else profile default."""
        return self.agent_dir_override or profile.agent_dir

    @property
    def agent_dir(self) -> str:
        """Agent directory for the default/selected editor (back-compat helper)."""
        return self.agent_dir_for(get_profile(self.editor))

    def config_path(self, project_root: Path) -> Path:
        """Path to the project's ``.issueflows/config.toml``."""
        return modes_module.config_path(project_root, self.issueflows_dir)

    def resolve_active_mode_id(self, project_root: Path) -> str:
        """Resolve the active mode id for ``project_root`` (no CLI ``--mode``).

        The CLI ``--mode`` argument takes precedence over everything and is
        applied by ``run_init`` before this fallback is consulted. Here the order
        is: persisted ``.issueflows/config.toml [issueflow].mode`` >
        ``ISSUEFLOW_MODE`` env/``.env`` > :data:`DEFAULT_MODE`.

        The persisted (init-chosen) mode deliberately beats the environment so a
        stray ``ISSUEFLOW_MODE`` cannot silently override the project's mode on
        ``update`` — switching modes is an ``init --mode`` action.
        """
        persisted = modes_module.read_active_mode(self.config_path(project_root))
        if persisted:
            return persisted
        env = os.getenv("ISSUEFLOW_MODE")
        if env and env.strip():
            return env.strip()
        return DEFAULT_MODE

    def resolve_mode(self, project_root: Path) -> Mode:
        """Resolve the active :class:`Mode` (built-ins + project overrides)."""
        return modes_module.resolve_mode(
            self.resolve_active_mode_id(project_root),
            self.config_path(project_root),
        )

    def resolve_caveman_default(self, project_root: Path) -> bool:
        """Resolve whether the caveman style is on by default for ``project_root``.

        Order: persisted ``.issueflows/config.toml [issueflow].caveman_default`` >
        ``ISSUEFLOW_CAVEMAN_DEFAULT`` env/``.env`` > ``False``. As with the active
        mode, the persisted value deliberately beats the environment so a stray
        env var cannot silently flip the behavior on ``update``.

        Only meaningful when the ``caveman`` skill is part of the active mode; the
        rule template gates the always-on pointer on skill membership too.
        """
        persisted = modes_module.read_caveman_default(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_CAVEMAN_DEFAULT")

    def template_context(
        self,
        project_root: Path,
        profile: EditorProfile | None = None,
        mode: Mode | None = None,
    ) -> dict[str, object]:
        """Build the Jinja2 template context dictionary for ``profile``.

        When ``profile`` is omitted, the context targets the editor configured
        via ``ISSUEFLOW_EDITOR`` (default ``cursor``). When ``mode`` is omitted,
        the active mode is resolved from env / persisted config / default.

        Templates can branch on the resolved mode via ``mode`` / ``mode_name``
        and, more robustly, on surface membership via ``included_skills`` /
        ``included_commands`` (so new modes and surfaces need no per-mode
        conditionals).
        """
        profile = profile or get_profile(self.editor)
        mode = mode or self.resolve_mode(project_root)
        project_name = _detect_project_name(project_root)
        return {
            "issueflows_dir": self.issueflows_dir,
            "agent_dir": self.agent_dir_for(profile),
            "docs_dir": self.docs_dir,
            "history_file": self.history_file,
            "tools_folder": self.tools_folder,
            "current_issues_folder": self.current_issues_folder,
            "partly_solved_folder": self.partly_solved_folder,
            "solved_folder": self.solved_folder,
            "designs_folder": self.designs_folder,
            "project_name": project_name,
            "editor": profile.id,
            "editor_name": profile.name,
            "commands_dir": profile.commands_dir or "commands",
            "commands_supported": profile.commands_dir is not None,
            "graphify_installer": profile.graphify_installer or "",
            "mode": mode.id,
            "mode_name": mode.name,
            "included_skills": sorted(mode.skills),
            "included_commands": sorted(mode.commands),
            "caveman_default": self.resolve_caveman_default(project_root),
        }


def _env_flag(name: str) -> bool:
    """Interpret an environment variable as a boolean flag (default ``False``)."""
    value = os.getenv(name)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _detect_project_name(project_root: Path) -> str:
    """Try to read the project name from pyproject.toml, fall back to dir name."""
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("name") and "=" in stripped:
                # e.g.  name = "my-project"
                value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value
    return project_root.resolve().name
