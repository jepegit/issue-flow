"""Configuration for issue-flow, backed by .env files and environment variables."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import os

from issue_flow.editors import DEFAULT_EDITOR, EditorProfile, get_profile


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

    def template_context(
        self, project_root: Path, profile: EditorProfile | None = None
    ) -> dict[str, str]:
        """Build the Jinja2 template context dictionary for ``profile``.

        When ``profile`` is omitted, the context targets the editor configured
        via ``ISSUEFLOW_EDITOR`` (default ``cursor``).
        """
        profile = profile or get_profile(self.editor)
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
            "graphify_installer": profile.graphify_installer or "",
        }


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
