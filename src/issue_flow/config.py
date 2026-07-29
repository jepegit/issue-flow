"""Configuration for issue-flow, backed by .env files and environment variables."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import os

from issue_flow import modes as modes_module
from issue_flow.editors import DEFAULT_EDITOR, EditorProfile, get_profile
from issue_flow.modes import (
    DEFAULT_CONFIRM_VERSION_BUMP,
    DEFAULT_AUTO_BUILD,
    DEFAULT_AUTO_CLOSE,
    DEFAULT_AUTO_PLAN,
    DEFAULT_CHECKS_WATCH_MINUTES,
    DEFAULT_CONFIRM_CHANGELOG_UPDATE,
    DEFAULT_EARLY_PR,
    DEFAULT_AUTO_GRAPHIFY_ON_PLAN,
    DEFAULT_AUTO_SWITCHBACK,
    DEFAULT_AUTO_ADVERSARIAL_LOOPS,
    DEFAULT_CYCLE_MAX_ISSUES,
    DEFAULT_DEEP_MODEL_LABEL,
    DEFAULT_FAST_MODEL_LABEL,
    DEFAULT_LABEL_FLOWS,
    DEFAULT_LINGUIST_ATTRIBUTES,
    DEFAULT_MODE,
    DEFAULT_MODEL_LABEL_FLOWS,
    DEFAULT_PR_MERGE_METHOD,
    DEFAULT_REMIND_CLEANUP,
    DEFAULT_RUFF_AUTOFIX,
    DEFAULT_SKILL_LEVEL,
    DEFAULT_STEP_DIRECTIVES,
    DEFAULT_SUGGEST_GRAPHIFY,
    DEFAULT_YOLO_LABEL,
    Mode,
    normalize_pr_merge_method,
)
from issue_flow import step_profiles as step_profiles_module


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
        print(
            "WARNING: The ISSUEFLOW_CURSOR_DIR environment variable is deprecated (replaced by ISSUEFLOW_AGENT_DIR)."
        )

    # Subdirectory names inside .issueflows/
    tools_folder: str = "00-tools"
    current_issues_folder: str = "01-current-issues"
    partly_solved_folder: str = "02-partly-solved-issues"
    solved_folder: str = "03-solved-issues"
    designs_folder: str = "04-designs-and-guides"
    epics_folder: str = "05-epics"

    @property
    def issueflows_subdirs(self) -> list[str]:
        return [
            self.tools_folder,
            self.current_issues_folder,
            self.partly_solved_folder,
            self.solved_folder,
            self.designs_folder,
            self.epics_folder,
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

    def resolve_grill_me_default(self, project_root: Path) -> bool:
        """Resolve whether the grill-me skill is on by default for ``project_root``.

        Order: persisted ``.issueflows/config.toml [issueflow].grill_me_default`` >
        ``ISSUEFLOW_GRILL_ME_DEFAULT`` env/``.env`` > ``False``. As with the active
        mode, the persisted value deliberately beats the environment so a stray
        env var cannot silently flip the behavior on ``update``.

        Only meaningful when the ``grill_me`` skill is part of the active mode; the
        rule and plan templates gate the always-on pointer on skill membership too.
        """
        persisted = modes_module.read_grill_me_default(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_GRILL_ME_DEFAULT")

    def resolve_label_flows(self, project_root: Path) -> bool:
        """Resolve whether label-driven flow selection is allowed for ``project_root``.

        Order: persisted ``.issueflows/config.toml [issueflow].label_flows`` >
        ``ISSUEFLOW_LABEL_FLOWS`` env/``.env`` > ``True``. As with the active
        mode, the persisted value deliberately beats the environment so a stray
        env var cannot silently flip the behavior on ``update``.
        """
        persisted = modes_module.read_label_flows(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_LABEL_FLOWS", default=DEFAULT_LABEL_FLOWS)

    def resolve_linguist_attributes(self, project_root: Path) -> bool:
        """Resolve whether to write a managed Linguist ``.gitattributes`` block.

        Order: persisted ``.issueflows/config.toml [issueflow].linguist_attributes`` >
        ``ISSUEFLOW_LINGUIST_ATTRIBUTES`` env/``.env`` > ``False`` (opt-in).
        """
        persisted = modes_module.read_linguist_attributes(
            self.config_path(project_root)
        )
        if persisted is not None:
            return persisted
        return _env_flag(
            "ISSUEFLOW_LINGUIST_ATTRIBUTES", default=DEFAULT_LINGUIST_ATTRIBUTES
        )

    def resolve_yolo_label(self, project_root: Path) -> str:
        """Resolve the GitHub label that triggers the yolo flow for ``project_root``.

        Order: persisted ``.issueflows/config.toml [issueflow].yolo_label`` >
        ``ISSUEFLOW_YOLO_LABEL`` env/``.env`` > ``"yolo"``.
        """
        persisted = modes_module.read_yolo_label(self.config_path(project_root))
        if persisted:
            return persisted
        env = os.getenv("ISSUEFLOW_YOLO_LABEL")
        if env and env.strip():
            return env.strip()
        return DEFAULT_YOLO_LABEL

    def resolve_checks_watch_minutes(self, project_root: Path) -> int:
        """Resolve the ``gh pr checks --watch`` wall-clock budget (minutes).

        Order: persisted ``.issueflows/config.toml [issueflow].checks_watch_minutes`` >
        ``ISSUEFLOW_CHECKS_WATCH_MINUTES`` env/``.env`` > ``15``. Non-positive or
        unparseable values fall through to the next layer, then the default.
        """
        persisted = modes_module.read_checks_watch_minutes(
            self.config_path(project_root)
        )
        if persisted is not None and persisted > 0:
            return persisted
        env = os.getenv("ISSUEFLOW_CHECKS_WATCH_MINUTES")
        if env and env.strip():
            try:
                minutes = int(env.strip())
            except ValueError:
                minutes = 0
            if minutes > 0:
                return minutes
        return DEFAULT_CHECKS_WATCH_MINUTES

    def resolve_step_directives(self, project_root: Path) -> bool:
        """Resolve whether step model directives are baked into lifecycle skills."""
        persisted = modes_module.read_step_directives(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_STEP_DIRECTIVES", default=DEFAULT_STEP_DIRECTIVES)

    def resolve_model_label_flows(self, project_root: Path) -> bool:
        """Resolve whether /iflow-pick announces label-driven profile overrides."""
        persisted = modes_module.read_model_label_flows(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag(
            "ISSUEFLOW_MODEL_LABEL_FLOWS", default=DEFAULT_MODEL_LABEL_FLOWS
        )

    def resolve_deep_model_label(self, project_root: Path) -> str:
        """Resolve the GitHub label that hints a reasoning session profile."""
        persisted = modes_module.read_deep_model_label(self.config_path(project_root))
        if persisted:
            return persisted
        env = os.getenv("ISSUEFLOW_DEEP_MODEL_LABEL")
        if env and env.strip():
            return env.strip()
        return DEFAULT_DEEP_MODEL_LABEL

    def resolve_fast_model_label(self, project_root: Path) -> str:
        """Resolve the GitHub label that hints an economy session profile."""
        persisted = modes_module.read_fast_model_label(self.config_path(project_root))
        if persisted:
            return persisted
        env = os.getenv("ISSUEFLOW_FAST_MODEL_LABEL")
        if env and env.strip():
            return env.strip()
        return DEFAULT_FAST_MODEL_LABEL

    def resolve_skill_level(self, project_root: Path) -> str:
        """Resolve the skill level for ``project_root``.

        Order: persisted ``.issueflows/config.toml [issueflow].skill_level`` >
        ``ISSUEFLOW_SKILL_LEVEL`` env/``.env`` > :data:`DEFAULT_SKILL_LEVEL`. The
        persisted value deliberately beats the environment so a stray env var cannot
        silently change the level on ``update`` — switching skill levels is an
        ``init --skill-level`` action.
        """
        persisted = modes_module.read_skill_level(self.config_path(project_root))
        if persisted:
            return persisted
        env = os.getenv("ISSUEFLOW_SKILL_LEVEL")
        if env and env.strip():
            return env.strip()
        return DEFAULT_SKILL_LEVEL

    def resolve_remind_cleanup(self, project_root: Path) -> bool:
        """Resolve whether skills remind the user to run ``/iflow-cleanup``."""
        persisted = modes_module.read_remind_cleanup(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_REMIND_CLEANUP", default=DEFAULT_REMIND_CLEANUP)

    def resolve_suggest_graphify(self, project_root: Path) -> bool:
        """Resolve whether skills soft-suggest graphify skim/rebuild."""
        persisted = modes_module.read_suggest_graphify(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_SUGGEST_GRAPHIFY", default=DEFAULT_SUGGEST_GRAPHIFY)

    def resolve_auto_graphify_on_plan(self, project_root: Path) -> bool:
        """Resolve whether ``/iflow-plan`` auto-runs ``issue-flow graphify``."""
        persisted = modes_module.read_auto_graphify_on_plan(
            self.config_path(project_root)
        )
        if persisted is not None:
            return persisted
        return _env_flag(
            "ISSUEFLOW_AUTO_GRAPHIFY_ON_PLAN", default=DEFAULT_AUTO_GRAPHIFY_ON_PLAN
        )

    def resolve_auto_switchback(self, project_root: Path) -> bool:
        """Resolve whether ``/iflow-close`` switches back to the default branch."""
        persisted = modes_module.read_auto_switchback(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_AUTO_SWITCHBACK", default=DEFAULT_AUTO_SWITCHBACK)

    def resolve_pr_merge_method(self, project_root: Path) -> str:
        """Resolve the ``gh pr merge`` method for yolo close (squash/merge/rebase)."""
        persisted = modes_module.read_pr_merge_method(self.config_path(project_root))
        if persisted:
            return persisted
        normalized = normalize_pr_merge_method(os.getenv("ISSUEFLOW_PR_MERGE_METHOD"))
        if normalized:
            return normalized
        return DEFAULT_PR_MERGE_METHOD

    def resolve_cycle_max_issues(self, project_root: Path) -> int:
        """Resolve the default ``/iflow-cycle`` queue safety cap.

        Order: persisted ``.issueflows/config.toml [issueflow].cycle_max_issues`` >
        ``ISSUEFLOW_CYCLE_MAX_ISSUES`` env/``.env`` > ``10``. Non-positive or
        unparseable values fall through to the next layer, then the default.
        """
        persisted = modes_module.read_cycle_max_issues(self.config_path(project_root))
        if persisted is not None and persisted > 0:
            return persisted
        env = os.getenv("ISSUEFLOW_CYCLE_MAX_ISSUES")
        if env and env.strip():
            try:
                value = int(env.strip())
            except ValueError:
                value = 0
            if value > 0:
                return value
        return DEFAULT_CYCLE_MAX_ISSUES

    def resolve_auto_adversarial_loops(self, project_root: Path) -> int:
        """Resolve the default ``/iflow-auto`` adversarial loop budget.

        Order: persisted ``[issueflow].auto_adversarial_loops`` >
        ``ISSUEFLOW_AUTO_ADVERSARIAL_LOOPS`` env > ``2``. Non-positive or
        unparseable values fall through to the next layer, then the default.
        """
        persisted = modes_module.read_auto_adversarial_loops(
            self.config_path(project_root)
        )
        if persisted is not None and persisted > 0:
            return persisted
        env = os.getenv("ISSUEFLOW_AUTO_ADVERSARIAL_LOOPS")
        if env and env.strip():
            try:
                value = int(env.strip())
            except ValueError:
                value = 0
            if value > 0:
                return value
        return DEFAULT_AUTO_ADVERSARIAL_LOOPS

    def resolve_confirm_version_bump(self, project_root: Path) -> bool:
        """Resolve whether non-yolo close asks about a version bump when unset."""
        persisted = modes_module.read_confirm_version_bump(
            self.config_path(project_root)
        )
        if persisted is not None:
            return persisted
        return _env_flag(
            "ISSUEFLOW_CONFIRM_VERSION_BUMP", default=DEFAULT_CONFIRM_VERSION_BUMP
        )

    def resolve_ruff_autofix(self, project_root: Path) -> bool:
        """Resolve whether start/close run ``ruff check --fix`` / ``ruff format``."""
        persisted = modes_module.read_ruff_autofix(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_RUFF_AUTOFIX", default=DEFAULT_RUFF_AUTOFIX)

    def resolve_auto_close(self, project_root: Path) -> bool:
        """Resolve whether start/fix chain into ``/iflow-close`` when ready to ship."""
        persisted = modes_module.read_auto_close(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_AUTO_CLOSE", default=DEFAULT_AUTO_CLOSE)

    def resolve_auto_plan(self, project_root: Path) -> bool:
        """Resolve whether ``/iflow-pick`` chains into ``/iflow-plan`` after confirm."""
        persisted = modes_module.read_auto_plan(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_AUTO_PLAN", default=DEFAULT_AUTO_PLAN)

    def resolve_auto_build(self, project_root: Path) -> bool:
        """Resolve whether ``/iflow-plan`` chains into ``/iflow-build`` on Accept."""
        persisted = modes_module.read_auto_build(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_AUTO_BUILD", default=DEFAULT_AUTO_BUILD)

    def resolve_early_pr(self, project_root: Path) -> bool:
        """Resolve whether ``/iflow-build`` opens a draft PR after the first push."""
        persisted = modes_module.read_early_pr(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return _env_flag("ISSUEFLOW_EARLY_PR", default=DEFAULT_EARLY_PR)

    def resolve_confirm_changelog_update(self, project_root: Path) -> bool:
        """Resolve whether ``/iflow-close`` confirms before writing the changelog."""
        persisted = modes_module.read_confirm_changelog_update(
            self.config_path(project_root)
        )
        if persisted is not None:
            return persisted
        return _env_flag(
            "ISSUEFLOW_CONFIRM_CHANGELOG_UPDATE",
            default=DEFAULT_CONFIRM_CHANGELOG_UPDATE,
        )

    def resolve_canonical_format(self, project_root: Path) -> bool:
        """Return whether the project uses the canonical agent store in git."""
        persisted = modes_module.read_canonical_format(self.config_path(project_root))
        if persisted is not None:
            return persisted
        return False

    def resolve_persisted_editor(self, project_root: Path) -> str | None:
        """Return the editor id persisted in ``config.toml``, if any."""
        return modes_module.read_persisted_editor(self.config_path(project_root))

    def resolve_target_editor(self, project_root: Path, cli_editor: str | None) -> str:
        """Resolve the editor for ``convert --to <editor>``.

        Order: explicit CLI value > ``ISSUEFLOW_EDITOR`` env > persisted
        ``config.toml`` > default ``cursor``. The special value ``canonical`` is
        passed through unchanged.
        """
        if cli_editor:
            return cli_editor.strip().lower()
        env = os.getenv("ISSUEFLOW_EDITOR")
        if env and env.strip():
            return env.strip().lower()
        persisted = self.resolve_persisted_editor(project_root)
        if persisted:
            return persisted
        return DEFAULT_EDITOR

    def seed_config_values(self) -> dict[str, object]:
        """Values for a freshly created ``config.toml``: env/``.env`` else defaults.

        Returns the ``[issueflow]`` keys issue-flow reads from ``config.toml``,
        taking each from its ``ISSUEFLOW_*`` env var (loaded from ``.env`` at
        import) when set, otherwise the issue-flow default. Deliberately ignores
        any existing ``config.toml`` since that is the layer being written.
        """
        mode = os.getenv("ISSUEFLOW_MODE")
        skill_level = os.getenv("ISSUEFLOW_SKILL_LEVEL")
        yolo_label = os.getenv("ISSUEFLOW_YOLO_LABEL")
        deep_model_label = os.getenv("ISSUEFLOW_DEEP_MODEL_LABEL")
        fast_model_label = os.getenv("ISSUEFLOW_FAST_MODEL_LABEL")
        checks_watch_raw = os.getenv("ISSUEFLOW_CHECKS_WATCH_MINUTES")
        checks_watch_minutes = DEFAULT_CHECKS_WATCH_MINUTES
        if checks_watch_raw and checks_watch_raw.strip():
            try:
                parsed = int(checks_watch_raw.strip())
            except ValueError:
                parsed = 0
            if parsed > 0:
                checks_watch_minutes = parsed
        cycle_max_raw = os.getenv("ISSUEFLOW_CYCLE_MAX_ISSUES")
        cycle_max_issues = DEFAULT_CYCLE_MAX_ISSUES
        if cycle_max_raw and cycle_max_raw.strip():
            try:
                parsed_cycle = int(cycle_max_raw.strip())
            except ValueError:
                parsed_cycle = 0
            if parsed_cycle > 0:
                cycle_max_issues = parsed_cycle
        loops_raw = os.getenv("ISSUEFLOW_AUTO_ADVERSARIAL_LOOPS")
        auto_adversarial_loops = DEFAULT_AUTO_ADVERSARIAL_LOOPS
        if loops_raw and loops_raw.strip():
            try:
                parsed_loops = int(loops_raw.strip())
            except ValueError:
                parsed_loops = 0
            if parsed_loops > 0:
                auto_adversarial_loops = parsed_loops
        pr_merge = normalize_pr_merge_method(os.getenv("ISSUEFLOW_PR_MERGE_METHOD"))
        return {
            "mode": mode.strip() if mode and mode.strip() else DEFAULT_MODE,
            "skill_level": (
                skill_level.strip()
                if skill_level and skill_level.strip()
                else DEFAULT_SKILL_LEVEL
            ),
            "caveman_default": _env_flag("ISSUEFLOW_CAVEMAN_DEFAULT"),
            "grill_me_default": _env_flag("ISSUEFLOW_GRILL_ME_DEFAULT"),
            "label_flows": _env_flag(
                "ISSUEFLOW_LABEL_FLOWS", default=DEFAULT_LABEL_FLOWS
            ),
            "yolo_label": (
                yolo_label.strip()
                if yolo_label and yolo_label.strip()
                else DEFAULT_YOLO_LABEL
            ),
            "checks_watch_minutes": checks_watch_minutes,
            "step_directives": _env_flag(
                "ISSUEFLOW_STEP_DIRECTIVES", default=DEFAULT_STEP_DIRECTIVES
            ),
            "model_label_flows": _env_flag(
                "ISSUEFLOW_MODEL_LABEL_FLOWS", default=DEFAULT_MODEL_LABEL_FLOWS
            ),
            "deep_model_label": (
                deep_model_label.strip()
                if deep_model_label and deep_model_label.strip()
                else DEFAULT_DEEP_MODEL_LABEL
            ),
            "fast_model_label": (
                fast_model_label.strip()
                if fast_model_label and fast_model_label.strip()
                else DEFAULT_FAST_MODEL_LABEL
            ),
            "linguist_attributes": _env_flag(
                "ISSUEFLOW_LINGUIST_ATTRIBUTES",
                default=DEFAULT_LINGUIST_ATTRIBUTES,
            ),
            "remind_cleanup": _env_flag(
                "ISSUEFLOW_REMIND_CLEANUP", default=DEFAULT_REMIND_CLEANUP
            ),
            "suggest_graphify": _env_flag(
                "ISSUEFLOW_SUGGEST_GRAPHIFY", default=DEFAULT_SUGGEST_GRAPHIFY
            ),
            "auto_graphify_on_plan": _env_flag(
                "ISSUEFLOW_AUTO_GRAPHIFY_ON_PLAN",
                default=DEFAULT_AUTO_GRAPHIFY_ON_PLAN,
            ),
            "auto_switchback": _env_flag(
                "ISSUEFLOW_AUTO_SWITCHBACK", default=DEFAULT_AUTO_SWITCHBACK
            ),
            "pr_merge_method": pr_merge or DEFAULT_PR_MERGE_METHOD,
            "cycle_max_issues": cycle_max_issues,
            "auto_adversarial_loops": auto_adversarial_loops,
            "confirm_version_bump": _env_flag(
                "ISSUEFLOW_CONFIRM_VERSION_BUMP", default=DEFAULT_CONFIRM_VERSION_BUMP
            ),
            "ruff_autofix": _env_flag(
                "ISSUEFLOW_RUFF_AUTOFIX", default=DEFAULT_RUFF_AUTOFIX
            ),
            "auto_close": _env_flag("ISSUEFLOW_AUTO_CLOSE", default=DEFAULT_AUTO_CLOSE),
            "auto_plan": _env_flag("ISSUEFLOW_AUTO_PLAN", default=DEFAULT_AUTO_PLAN),
            "auto_build": _env_flag("ISSUEFLOW_AUTO_BUILD", default=DEFAULT_AUTO_BUILD),
            "early_pr": _env_flag("ISSUEFLOW_EARLY_PR", default=DEFAULT_EARLY_PR),
            "confirm_changelog_update": _env_flag(
                "ISSUEFLOW_CONFIRM_CHANGELOG_UPDATE",
                default=DEFAULT_CONFIRM_CHANGELOG_UPDATE,
            ),
        }

    def template_context(
        self,
        project_root: Path,
        profile: EditorProfile | None = None,
        mode: Mode | None = None,
        skill_level: str | None = None,
    ) -> dict[str, object]:
        """Build the Jinja2 template context dictionary for ``profile``.

        When ``profile`` is omitted, the context targets the editor configured
        via ``ISSUEFLOW_EDITOR`` (default ``cursor``). When ``mode`` is omitted,
        the active mode is resolved from env / persisted config / default. When
        ``skill_level`` is omitted, the active level is resolved.

        Templates can branch on the resolved mode via ``mode`` / ``mode_name``
        and, more robustly, on surface membership via ``included_skills`` /
        ``included_commands`` (so new modes and surfaces need no per-mode
        conditionals). Templates can also branch on ``skill_level`` for
        complexity-gated guidance.
        """
        profile = profile or get_profile(self.editor)
        mode = mode or self.resolve_mode(project_root)
        skill_level = skill_level or self.resolve_skill_level(project_root)
        from issue_flow import __version__ as issue_flow_version

        project_name = _detect_project_name(project_root)
        return {
            "issue_flow_version": issue_flow_version,
            "issueflows_dir": self.issueflows_dir,
            "agent_dir": self.agent_dir_for(profile),
            "docs_dir": self.docs_dir,
            "history_file": self.history_file,
            "tools_folder": self.tools_folder,
            "current_issues_folder": self.current_issues_folder,
            "partly_solved_folder": self.partly_solved_folder,
            "solved_folder": self.solved_folder,
            "designs_folder": self.designs_folder,
            "epics_folder": self.epics_folder,
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
            "grill_me_default": self.resolve_grill_me_default(project_root),
            "label_flows": self.resolve_label_flows(project_root),
            "yolo_label": self.resolve_yolo_label(project_root),
            "checks_watch_minutes": self.resolve_checks_watch_minutes(project_root),
            "step_directives": self.resolve_step_directives(project_root),
            "model_label_flows": self.resolve_model_label_flows(project_root),
            "deep_model_label": self.resolve_deep_model_label(project_root),
            "fast_model_label": self.resolve_fast_model_label(project_root),
            "step_profiles": step_profiles_module.resolve_all(
                self.config_path(project_root)
            ),
            "skill_level": skill_level,
            "remind_cleanup": self.resolve_remind_cleanup(project_root),
            "suggest_graphify": self.resolve_suggest_graphify(project_root),
            "auto_graphify_on_plan": self.resolve_auto_graphify_on_plan(project_root),
            "auto_switchback": self.resolve_auto_switchback(project_root),
            "pr_merge_method": self.resolve_pr_merge_method(project_root),
            "cycle_max_issues": self.resolve_cycle_max_issues(project_root),
            "auto_adversarial_loops": self.resolve_auto_adversarial_loops(project_root),
            "confirm_version_bump": self.resolve_confirm_version_bump(project_root),
            "ruff_autofix": self.resolve_ruff_autofix(project_root),
            "auto_close": self.resolve_auto_close(project_root),
            "auto_plan": self.resolve_auto_plan(project_root),
            "auto_build": self.resolve_auto_build(project_root),
            "early_pr": self.resolve_early_pr(project_root),
            "confirm_changelog_update": self.resolve_confirm_changelog_update(
                project_root
            ),
        }


def _env_flag(name: str, default: bool = False) -> bool:
    """Interpret an environment variable as a boolean flag (``default`` when unset)."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
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
