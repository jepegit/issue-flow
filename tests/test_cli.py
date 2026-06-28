"""Tests for the `issue-flow` Typer CLI."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from issue_flow.cli import app

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    """Strip ANSI color/style codes so help text can be matched reliably.

    Rich colorizes ``--help`` output when it thinks it is talking to a
    terminal (as on CI), which splits literals like ``--editor`` across escape
    sequences. Stripping the codes makes the assertions environment-agnostic.
    """
    return _ANSI_RE.sub("", text)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_lists_graphify_command(runner: CliRunner) -> None:
    """`issue-flow --help` must mention the `graphify` command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "graphify" in result.stdout


def test_init_help_documents_editor_option(runner: CliRunner) -> None:
    """`issue-flow init --help` must advertise the --editor option."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "--editor" in _plain(result.stdout)


def test_init_editor_codex_scaffolds_skills_only(
    runner: CliRunner, tmp_path: Path
) -> None:
    """`issue-flow init --editor codex` writes the codex tree without commands."""
    result = runner.invoke(app, ["init", str(tmp_path), "--editor", "codex"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".codex" / "skills" / "iflow" / "SKILL.md").is_file()
    assert not (tmp_path / ".codex" / "commands").exists()
    assert (tmp_path / "AGENTS.md").is_file()


def test_init_unknown_editor_exits_with_code_2(
    runner: CliRunner, tmp_path: Path
) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--editor", "nano"])
    assert result.exit_code == 2


def test_init_help_documents_mode_option(runner: CliRunner) -> None:
    """`issue-flow init --help` must advertise the --mode option."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    plain = _plain(result.stdout)
    assert "--mode" in plain
    assert "simple" in plain


def test_init_mode_simple_scaffolds_subset_and_persists(
    runner: CliRunner, tmp_path: Path
) -> None:
    """`issue-flow init --mode simple` installs the subset and records the mode."""
    result = runner.invoke(app, ["init", str(tmp_path), "--mode", "simple"])
    assert result.exit_code == 0, result.output

    skills = tmp_path / ".cursor" / "skills"
    assert (skills / "iflow-init" / "SKILL.md").is_file()
    assert (skills / "iflow-plan" / "SKILL.md").is_file()
    # Excluded by simple mode.
    assert not (skills / "iflow-close").exists()
    assert not (skills / "iflow-yolo").exists()
    assert not (skills / "iflow-fix").exists()

    config = tmp_path / ".issueflows" / "config.toml"
    assert config.is_file()
    assert 'mode = "simple"' in config.read_text(encoding="utf-8")


def test_init_unknown_mode_exits_with_code_2(
    runner: CliRunner, tmp_path: Path
) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--mode", "bogus"])
    assert result.exit_code == 2
    assert not (tmp_path / ".cursor").exists()


def test_update_has_no_mode_option(runner: CliRunner) -> None:
    """`issue-flow update` must not expose a --mode flag (init-only)."""
    result = runner.invoke(app, ["update", "--help"])
    assert result.exit_code == 0
    assert "--mode" not in _plain(result.stdout)


def test_graphify_help_describes_passthrough(runner: CliRunner) -> None:
    result = runner.invoke(app, ["graphify", "--help"])
    assert result.exit_code == 0
    assert "graphify" in result.stdout.lower()


def test_graphify_invokes_graphify_when_available(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`issue-flow graphify` should call subprocess.run with the graphify CLI."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)

    result = runner.invoke(app, ["graphify", "-C", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert captured["cmd"][0] == "graphify"
    # Default subcommand must be injected since graphify requires one.
    # We default to ``update`` (AST-only, no LLM API key required) so
    # ``issue-flow graphify`` works on a fresh machine with no backend
    # configured.
    assert captured["cmd"][1] == "update"


def test_graphify_forwards_extra_args(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leading subcommand and trailing flags must reach `graphify` verbatim."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(cmd: list[str], **kwargs: Any) -> _Result:
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(graphify_module.subprocess, "run", fake_run)

    # `cluster-only` is a real graphify build subcommand; `--no-viz` is
    # one of its real flags. Both must reach graphify verbatim, and the
    # project root must be injected after the subcommand.
    result = runner.invoke(
        app, ["graphify", "-C", str(tmp_path), "cluster-only", "--no-viz"]
    )

    assert result.exit_code == 0, result.output
    assert captured["cmd"] == [
        "graphify",
        "cluster-only",
        str(tmp_path),
        "--no-viz",
    ]


def test_graphify_exits_nonzero_when_graphify_missing(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When graphify is not installed, `issue-flow graphify` exits with the error code from run_build."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: None)
    monkeypatch.setattr(graphify_module, "_candidate_install_locations", lambda: [])

    def fail_run(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("subprocess.run must not be called when graphify is missing")

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)

    result = runner.invoke(app, ["graphify", "-C", str(tmp_path)])

    assert result.exit_code == 2
    assert "graphifyy" in result.output


def test_graphify_propagates_graphify_exit_code(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify")

    class _Result:
        returncode = 7

    monkeypatch.setattr(graphify_module.subprocess, "run", lambda *a, **kw: _Result())

    result = runner.invoke(app, ["graphify", "-C", str(tmp_path)])

    assert result.exit_code == 7


# ---------------------------------------------------------------------------
# status + agent sub-app
# ---------------------------------------------------------------------------


def _seed_issue(tmp_path: Path, number: int, *, plan: bool = False,
                status: str | None = None, title: str = "Title") -> None:
    cur = tmp_path / ".issueflows" / "01-current-issues"
    cur.mkdir(parents=True, exist_ok=True)
    (cur / f"issue{number}_original.md").write_text(
        f"# Issue #{number}: {title}\n\nbody\n", encoding="utf-8"
    )
    if plan:
        (cur / f"issue{number}_plan.md").write_text("plan\n", encoding="utf-8")
    if status is not None:
        (cur / f"issue{number}_status.md").write_text(status, encoding="utf-8")


def _json(output: str) -> Any:
    return json.loads(_plain(output))


def test_cli_lists_status_and_agent(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    plain = _plain(result.stdout)
    assert "status" in plain
    assert "agent" in plain


def test_agent_help_lists_subcommands(runner: CliRunner) -> None:
    result = runner.invoke(app, ["agent", "--help"])
    assert result.exit_code == 0
    plain = _plain(result.stdout)
    for sub in ("state", "preflight", "sweep", "capture"):
        assert sub in plain


def test_status_help_documents_local_and_json(runner: CliRunner) -> None:
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0
    plain = _plain(result.stdout)
    assert "--local" in plain
    assert "--json" in plain


def test_agent_state_json_reports_stage(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "current_branch", lambda _cwd: None)
    _seed_issue(tmp_path, 5, plan=True)

    result = runner.invoke(app, ["agent", "state", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["focus"] == 5
    assert payload["resolved_via"] == "single-group"
    assert payload["stage"] == "start"
    assert payload["next_command"] == "/iflow-start"


def test_agent_sweep_dry_run_does_not_move(
    runner: CliRunner, tmp_path: Path
) -> None:
    _seed_issue(tmp_path, 1, status="- [x] Done\n")
    _seed_issue(tmp_path, 2, status="- [ ] Done\n")

    result = runner.invoke(
        app, ["agent", "sweep", str(tmp_path), "--except", "2", "--dry-run", "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["dry_run"] is True
    moves = {m["issue"]: m for m in payload["moves"]}
    assert set(moves) == {1}
    assert moves[1]["to"] == "03-solved-issues"
    # Dry run: nothing actually moved.
    assert (tmp_path / ".issueflows" / "01-current-issues" / "issue1_original.md").exists()


def test_agent_sweep_applies_moves(
    runner: CliRunner, tmp_path: Path
) -> None:
    _seed_issue(tmp_path, 1, status="- [x] Done\n")
    _seed_issue(tmp_path, 9)  # focus, kept

    result = runner.invoke(
        app, ["agent", "sweep", str(tmp_path), "--except", "9"]
    )

    assert result.exit_code == 0, result.output
    cur = tmp_path / ".issueflows" / "01-current-issues"
    solved = tmp_path / ".issueflows" / "03-solved-issues"
    assert not (cur / "issue1_original.md").exists()
    assert (solved / "issue1_original.md").exists()
    assert (cur / "issue9_original.md").exists()


def test_agent_preflight_json_handles_missing_git(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "git_available", lambda: False)

    result = runner.invoke(app, ["agent", "preflight", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["git_available"] is False


def test_agent_capture_errors_without_gh(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "gh_available", lambda: False)

    result = runner.invoke(
        app, ["agent", "capture", "5", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["written"] is False


def test_agent_capture_writes_original(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "gh_available", lambda: True)
    monkeypatch.setattr(
        gitutils_module, "remote_owner_repo", lambda _cwd: ("octo", "repo")
    )
    monkeypatch.setattr(
        gitutils_module,
        "gh_issue_view",
        lambda *_a, **_kw: {
            "number": 12,
            "title": "Fix the thing",
            "url": "https://github.com/octo/repo/issues/12",
            "body": "Please fix it.",
            "comments": [],
        },
    )

    result = runner.invoke(
        app, ["agent", "capture", "12", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["written"] is True
    assert payload["repo"] == "octo/repo"
    target = tmp_path / ".issueflows" / "01-current-issues" / "issue12_original.md"
    assert target.is_file()
    content = target.read_text(encoding="utf-8")
    assert "# Issue #12: Fix the thing" in content
    assert "Please fix it." in content


# ---------------------------------------------------------------------------
# config sub-app
# ---------------------------------------------------------------------------


def _clear_issueflow_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "ISSUEFLOW_MODE",
        "ISSUEFLOW_CAVEMAN_DEFAULT",
        "ISSUEFLOW_GRILL_ME_DEFAULT",
    ):
        monkeypatch.delenv(var, raising=False)


def test_config_help_lists_add(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "add" in _plain(result.stdout)


def test_config_add_creates_defaults(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tomllib

    _clear_issueflow_env(monkeypatch)

    result = runner.invoke(
        app, ["config", "add", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["written"] is True
    assert payload["overwritten"] is False
    assert payload["mode"] == "standard"
    assert payload["caveman_default"] is False
    assert payload["grill_me_default"] is False

    cfg = tmp_path / ".issueflows" / "config.toml"
    assert cfg.is_file()
    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert data["issueflow"]["mode"] == "standard"
    assert data["issueflow"]["caveman_default"] is False
    assert data["issueflow"]["grill_me_default"] is False


def test_config_add_reads_env(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tomllib

    monkeypatch.setenv("ISSUEFLOW_MODE", "simple")
    monkeypatch.setenv("ISSUEFLOW_CAVEMAN_DEFAULT", "true")
    monkeypatch.delenv("ISSUEFLOW_GRILL_ME_DEFAULT", raising=False)

    result = runner.invoke(app, ["config", "add", "-C", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    cfg = tmp_path / ".issueflows" / "config.toml"
    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert data["issueflow"]["mode"] == "simple"
    assert data["issueflow"]["caveman_default"] is True
    assert data["issueflow"]["grill_me_default"] is False


def test_config_add_does_not_clobber_without_force(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_issueflow_env(monkeypatch)
    cfg = tmp_path / ".issueflows" / "config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    original = (
        "[issueflow]\n"
        'mode = "simple"\n'
        "caveman_default = true\n\n"
        "# hand-added comment\n"
        "[modes.mine]\n"
        'extends = "simple"\n'
    )
    cfg.write_text(original, encoding="utf-8")

    result = runner.invoke(app, ["config", "add", "-C", str(tmp_path), "--json"])

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["written"] is False
    # File untouched.
    assert cfg.read_text(encoding="utf-8") == original


def test_config_add_force_upserts_and_preserves(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tomllib

    _clear_issueflow_env(monkeypatch)
    cfg = tmp_path / ".issueflows" / "config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        "[issueflow]\n"
        'mode = "simple"\n\n'
        "# keep me\n"
        "[modes.mine]\n"
        'extends = "simple"\n',
        encoding="utf-8",
    )

    result = runner.invoke(
        app, ["config", "add", "-C", str(tmp_path), "--force", "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["written"] is True
    assert payload["overwritten"] is True

    text = cfg.read_text(encoding="utf-8")
    data = tomllib.loads(text)
    # Three keys upserted to env/defaults.
    assert data["issueflow"]["mode"] == "standard"
    assert data["issueflow"]["caveman_default"] is False
    assert data["issueflow"]["grill_me_default"] is False
    # User content preserved.
    assert "# keep me" in text
    assert data["modes"]["mine"]["extends"] == "simple"


def test_status_local_json(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "current_branch", lambda _cwd: None)
    _seed_issue(tmp_path, 7, plan=True, status="- [x] Done\n", title="Done one")

    result = runner.invoke(app, ["status", str(tmp_path), "--local", "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["focus"]["number"] == 7
    assert payload["focus"]["stage"] == "close"
    assert payload["github"] is None


def test_status_text_escapes_malicious_title(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A title with Rich markup must not crash the text report or be interpreted."""
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "current_branch", lambda _cwd: None)
    # `[/]` is invalid Rich markup and would raise MarkupError if not escaped.
    _seed_issue(tmp_path, 3, plan=True, title="[/]evil [bold]oops")

    result = runner.invoke(app, ["status", str(tmp_path), "--local"])

    assert result.exit_code == 0, result.output
    # The literal markup survives as text rather than being interpreted.
    assert "[/]evil" in result.stdout
