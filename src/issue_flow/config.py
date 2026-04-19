"""Configuration for issue-flow, backed by .env files and environment variables."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import os


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
    agent_dir: str = field(
        default_factory=lambda: os.getenv("ISSUEFLOW_AGENT_DIR", ".cursor")
    )
    docs_dir: str = field(
        default_factory=lambda: os.getenv("ISSUEFLOW_DOCS_DIR", "docs")
    )

    # Give a deprecation warning if the user is using the old ISSUEFLOW_CURSOR_DIR environment variable
    if os.getenv("ISSUEFLOW_CURSOR_DIR"):
        print("WARNING: The ISSUEFLOW_CURSOR_DIR environment variable is deprecated (replaced by ISSUEFLOW_AGENT_DIR).")

    # Subdirectory names inside .issueflows/
    tools_folder: str = "00-tools"
    current_issues_folder: str = "01-current-issues"
    partly_solved_folder: str = "02-partly-solved-issues"
    solved_folder: str = "03-solved-issues"

    @property
    def issueflows_subdirs(self) -> list[str]:
        return [
            self.tools_folder,
            self.current_issues_folder,
            self.partly_solved_folder,
            self.solved_folder,
        ]

    def template_context(self, project_root: Path) -> dict[str, str]:
        """Build the Jinja2 template context dictionary."""
        project_name = _detect_project_name(project_root)
        return {
            "issueflows_dir": self.issueflows_dir,
            "agent_dir": self.agent_dir,
            "docs_dir": self.docs_dir,
            "tools_folder": self.tools_folder,
            "current_issues_folder": self.current_issues_folder,
            "partly_solved_folder": self.partly_solved_folder,
            "solved_folder": self.solved_folder,
            "project_name": project_name,
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
