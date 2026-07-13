"""Tests for the `issue-flow` Typer CLI."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from issue_flow.cli import app
from issue_flow.config import Settings

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


def test_cli_version_option(runner: CliRunner) -> None:
    """`issue-flow --version` must print the package version and exit 0."""
    from importlib.metadata import version

    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert version("issue-flow") in result.stdout


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


def test_init_unknown_mode_exits_with_code_2(runner: CliRunner, tmp_path: Path) -> None:
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


def test_sync_help_documents_apply(runner: CliRunner) -> None:
    result = runner.invoke(app, ["sync", "--help"])
    assert result.exit_code == 0
    assert "--apply" in result.stdout


def test_sync_json_dry_run(runner: CliRunner, tmp_path: Path) -> None:
    settings = Settings()
    current = tmp_path / settings.issueflows_dir / settings.current_issues_folder
    current.mkdir(parents=True)
    (current / "issue1_status.md").write_text("- [ ] Done\n", encoding="utf-8")
    result = runner.invoke(app, ["sync", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    assert '"dry_run": true' in result.stdout


def test_graphify_invokes_graphify_when_available(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`issue-flow graphify` should call subprocess.run with the graphify CLI."""
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(
        graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify"
    )

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

    monkeypatch.setattr(
        graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify"
    )

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
        raise AssertionError(
            "subprocess.run must not be called when graphify is missing"
        )

    monkeypatch.setattr(graphify_module.subprocess, "run", fail_run)

    result = runner.invoke(app, ["graphify", "-C", str(tmp_path)])

    assert result.exit_code == 2
    assert "graphifyy" in result.output


def test_graphify_propagates_graphify_exit_code(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import graphify as graphify_module

    monkeypatch.setattr(
        graphify_module.shutil, "which", lambda _cmd: "/usr/bin/graphify"
    )

    class _Result:
        returncode = 7

    monkeypatch.setattr(graphify_module.subprocess, "run", lambda *a, **kw: _Result())

    result = runner.invoke(app, ["graphify", "-C", str(tmp_path)])

    assert result.exit_code == 7


# ---------------------------------------------------------------------------
# status + agent sub-app
# ---------------------------------------------------------------------------


def _seed_issue(
    tmp_path: Path,
    number: int,
    *,
    plan: bool = False,
    status: str | None = None,
    title: str = "Title",
) -> None:
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
    for sub in (
        "state",
        "preflight",
        "switchback",
        "resolve",
        "sweep",
        "capture",
        "archive",
    ):
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


def test_agent_sweep_dry_run_does_not_move(runner: CliRunner, tmp_path: Path) -> None:
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
    assert (
        tmp_path / ".issueflows" / "01-current-issues" / "issue1_original.md"
    ).exists()


def test_agent_sweep_applies_moves(runner: CliRunner, tmp_path: Path) -> None:
    _seed_issue(tmp_path, 1, status="- [x] Done\n")
    _seed_issue(tmp_path, 9)  # focus, kept

    result = runner.invoke(app, ["agent", "sweep", str(tmp_path), "--except", "9"])

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


def test_agent_switchback_refuses_dirty_tree(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "git_available", lambda: True)
    monkeypatch.setattr(gitutils_module, "current_branch", lambda _cwd: "42-fix")
    monkeypatch.setattr(gitutils_module, "default_branch", lambda _cwd: "main")
    monkeypatch.setattr(
        gitutils_module, "dirty_paths", lambda _cwd: ["src/wip.py", "notes.md"]
    )

    def explode(*_a: object, **_kw: object) -> object:
        raise AssertionError("must not switch or pull while the tree is dirty")

    monkeypatch.setattr(gitutils_module, "switch_branch", explode)
    monkeypatch.setattr(gitutils_module, "pull_ff_only", explode)

    result = runner.invoke(app, ["agent", "switchback", str(tmp_path), "--json"])

    assert result.exit_code == 1, result.output
    payload = _json(result.stdout)
    assert payload["switched"] is False
    assert payload["pulled"] is False
    assert payload["dirty_paths"] == ["src/wip.py", "notes.md"]
    assert any("dirty" in note for note in payload["notes"])


def test_agent_switchback_switches_and_pulls_when_clean(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    calls: list[str] = []
    monkeypatch.setattr(gitutils_module, "git_available", lambda: True)
    monkeypatch.setattr(gitutils_module, "current_branch", lambda _cwd: "42-fix")
    monkeypatch.setattr(gitutils_module, "default_branch", lambda _cwd: "main")
    monkeypatch.setattr(gitutils_module, "dirty_paths", lambda _cwd: [])
    monkeypatch.setattr(
        gitutils_module,
        "switch_branch",
        lambda _cwd, branch: (calls.append(f"switch {branch}"), (True, None))[1],
    )
    monkeypatch.setattr(
        gitutils_module,
        "pull_ff_only",
        lambda _cwd: (calls.append("pull"), (True, None))[1],
    )

    result = runner.invoke(app, ["agent", "switchback", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["previous_branch"] == "42-fix"
    assert payload["default_branch"] == "main"
    assert payload["switched"] is True
    assert payload["pulled"] is True
    assert calls == ["switch main", "pull"]


def test_agent_switchback_already_on_default_still_pulls(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "git_available", lambda: True)
    monkeypatch.setattr(gitutils_module, "current_branch", lambda _cwd: "main")
    monkeypatch.setattr(gitutils_module, "default_branch", lambda _cwd: "main")
    monkeypatch.setattr(gitutils_module, "dirty_paths", lambda _cwd: [])

    def explode(*_a: object, **_kw: object) -> object:
        raise AssertionError("must not switch when already on the default branch")

    monkeypatch.setattr(gitutils_module, "switch_branch", explode)
    monkeypatch.setattr(gitutils_module, "pull_ff_only", lambda _cwd: (True, None))

    result = runner.invoke(app, ["agent", "switchback", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["switched"] is False
    assert payload["pulled"] is True
    assert any("already on main" in note for note in payload["notes"])


def test_agent_switchback_reports_ff_refusal(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "git_available", lambda: True)
    monkeypatch.setattr(gitutils_module, "current_branch", lambda _cwd: "42-fix")
    monkeypatch.setattr(gitutils_module, "default_branch", lambda _cwd: "main")
    monkeypatch.setattr(gitutils_module, "dirty_paths", lambda _cwd: [])
    monkeypatch.setattr(
        gitutils_module, "switch_branch", lambda _cwd, _branch: (True, None)
    )
    monkeypatch.setattr(
        gitutils_module,
        "pull_ff_only",
        lambda _cwd: (False, "fatal: Not possible to fast-forward"),
    )

    result = runner.invoke(app, ["agent", "switchback", str(tmp_path), "--json"])

    assert result.exit_code == 1, result.output
    payload = _json(result.stdout)
    assert payload["switched"] is True
    assert payload["pulled"] is False
    assert any("fast-forward" in note for note in payload["notes"])


def test_agent_switchback_missing_git_exits_nonzero(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "git_available", lambda: False)

    result = runner.invoke(app, ["agent", "switchback", str(tmp_path), "--json"])

    assert result.exit_code == 1, result.output
    payload = _json(result.stdout)
    assert payload["git_available"] is False


def _seed_solved_issue(tmp_path: Path, number: int, *, title: str = "Title") -> None:
    solved = tmp_path / ".issueflows" / "03-solved-issues"
    solved.mkdir(parents=True, exist_ok=True)
    (solved / f"issue{number}_original.md").write_text(
        f"# Issue #{number}: {title}\n\nbody\n", encoding="utf-8"
    )
    (solved / f"issue{number}_status.md").write_text("- [x] Done\n", encoding="utf-8")


def test_agent_archive_dry_run_does_not_delete(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "head_sha", lambda _cwd: "abc123")
    _seed_solved_issue(tmp_path, 1, title="Old one")

    result = runner.invoke(
        app, ["agent", "archive", "1", "-C", str(tmp_path), "--dry-run", "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["dry_run"] is True
    assert payload["head_sha"] == "abc123"
    assert payload["issues"][0]["issue"] == 1
    assert payload["issues"][0]["title"] == "Old one"
    assert payload["removed"] == []
    solved = tmp_path / ".issueflows" / "03-solved-issues"
    assert (solved / "issue1_original.md").exists()


def test_agent_archive_deletes_files(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "head_sha", lambda _cwd: "abc123")
    _seed_solved_issue(tmp_path, 1)
    _seed_solved_issue(tmp_path, 2)  # kept

    result = runner.invoke(
        app, ["agent", "archive", "1", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert sorted(payload["removed"]) == [
        "issue1_original.md",
        "issue1_status.md",
    ]
    solved = tmp_path / ".issueflows" / "03-solved-issues"
    assert not (solved / "issue1_original.md").exists()
    assert (solved / "issue2_original.md").exists()


def test_agent_archive_never_touches_sibling_folders(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Archiving issue N deletes only its files inside 03-solved-issues/.

    Pins the safety contract: sibling .issueflows/ folders survive untouched,
    even when they contain files whose names match the issue<N>_* pattern of
    the archived issue, and non-issue files inside the solved folder (the
    dated summary) survive too.
    """
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "head_sha", lambda _cwd: "abc123")
    _seed_solved_issue(tmp_path, 1)

    base = tmp_path / ".issueflows"
    tools = base / "00-tools"
    tools.mkdir(parents=True)
    (tools / "README.md").write_text("# Tool index\n", encoding="utf-8")
    # The nasty case: an issue-pattern filename in the wrong folder.
    (tools / "issue1_helper.py").write_text("print('keep me')\n", encoding="utf-8")
    designs = base / "04-designs-and-guides"
    designs.mkdir(parents=True)
    (designs / "issue1_design-notes.md").write_text("keep\n", encoding="utf-8")
    current = base / "01-current-issues"
    current.mkdir(parents=True)
    (current / "issue1_original.md").write_text("active copy\n", encoding="utf-8")
    solved = base / "03-solved-issues"
    summary = solved / "2026-07-10_archived_issues.md"
    summary.write_text("# Archived issues\n", encoding="utf-8")

    result = runner.invoke(
        app, ["agent", "archive", "1", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 0, result.output
    # The solved group itself is gone...
    assert not (solved / "issue1_original.md").exists()
    assert not (solved / "issue1_status.md").exists()
    # ...and everything else survived.
    assert (tools / "README.md").exists()
    assert (tools / "issue1_helper.py").exists()
    assert (designs / "issue1_design-notes.md").exists()
    assert (current / "issue1_original.md").exists()
    assert summary.exists()


def test_agent_archive_refuses_missing_issue(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "head_sha", lambda _cwd: "abc123")
    _seed_solved_issue(tmp_path, 1)

    result = runner.invoke(
        app, ["agent", "archive", "1", "99", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["archived"] is False
    assert payload["missing"] == [99]
    # Nothing was deleted, not even the issue that does exist.
    solved = tmp_path / ".issueflows" / "03-solved-issues"
    assert (solved / "issue1_original.md").exists()


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


def test_agent_resolve_json(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    workspace = tmp_path / "workspace"
    repo = workspace / "alpha"
    sibling = workspace / "beta"
    repo.mkdir(parents=True)
    sibling.mkdir()
    (repo / ".issueflows" / "01-current-issues").mkdir(parents=True)
    (sibling / ".issueflows").mkdir()

    monkeypatch.setattr(
        gitutils_module, "remote_owner_repo", lambda _cwd: ("octo", "repo")
    )
    monkeypatch.setattr(gitutils_module, "current_branch", lambda _cwd: "67-fix")
    monkeypatch.setattr(gitutils_module, "default_branch", lambda _cwd: "main")
    monkeypatch.setattr(gitutils_module, "git_available", lambda: True)

    nested = repo / "src" / "mod.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("x", encoding="utf-8")

    result = runner.invoke(
        app,
        ["agent", "resolve", "-C", str(repo), "--from-file", str(nested), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["project_root"] == str(repo.resolve())
    assert payload["repo"] == "octo/repo"
    assert payload["branch"] == "67-fix"
    assert payload["default_branch"] == "main"
    assert payload["issueflows_dir"] == ".issueflows"
    assert payload["sibling_roots"] == [str(sibling.resolve())]


def test_agent_resolve_fails_without_scaffold(
    runner: CliRunner, tmp_path: Path
) -> None:
    result = runner.invoke(app, ["agent", "resolve", "-C", str(tmp_path), "--json"])
    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["project_root"] is None
    assert payload["workspace_root"] is None
    assert payload["resolved_via_workspace_default"] is False


# ---------------------------------------------------------------------------
# agent version-plan (issue #133)
# ---------------------------------------------------------------------------


def test_agent_version_plan_static_project(runner: CliRunner, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0.4.1a4"\n', encoding="utf-8"
    )

    result = runner.invoke(
        app, ["agent", "version-plan", str(tmp_path), "--bump", "beta", "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["strategy"] == "uv"
    assert payload["current_version"] == "0.4.1a4"
    assert payload["planned_version"] == "0.4.1b1"
    assert payload["planned_tag"] is None
    assert payload["commands"] == ["uv version --bump beta"]


def test_agent_version_plan_tag_project_defaults_to_channel(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndynamic = ["version"]\n\n[tool.setuptools_scm]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(gitutils_module, "latest_tag", lambda _cwd: "v1.0.4a2")

    result = runner.invoke(app, ["agent", "version-plan", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["strategy"] == "tag"
    assert payload["latest_tag"] == "v1.0.4a2"
    # No level given -> pre-release-aware default keeps the alpha channel.
    assert payload["levels"] == ["alpha"]
    assert payload["planned_tag"] == "v1.0.4a3"
    assert payload["commands"][0] == "git tag v1.0.4a3"
    assert any("after the PR merges" in note for note in payload["notes"])


def test_agent_version_plan_tag_project_without_tags_fails(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndynamic = ["version"]\n\n[tool.setuptools_scm]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(gitutils_module, "latest_tag", lambda _cwd: None)

    result = runner.invoke(app, ["agent", "version-plan", str(tmp_path), "--json"])

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["planned_tag"] is None
    assert any("no git tags" in note for note in payload["notes"])


def test_agent_version_plan_unknown_strategy_fails(
    runner: CliRunner, tmp_path: Path
) -> None:
    result = runner.invoke(app, ["agent", "version-plan", str(tmp_path), "--json"])

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["strategy"] == "unknown"
    assert payload["commands"] == []


def test_agent_version_plan_flags_filled_brief(
    runner: CliRunner, tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    designs = tmp_path / ".issueflows" / "04-designs-and-guides"
    designs.mkdir(parents=True)
    (designs / "this-project.md").write_text(
        "# x\n\n## Release & version bump\n\nWe tag manually on main.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["agent", "version-plan", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["brief_release_section"] == "filled"
    assert any("wins over" in note for note in payload["notes"])


# ---------------------------------------------------------------------------
# agent epic-status (issue #138)
# ---------------------------------------------------------------------------

_EPIC_PLAN = """# Epic #9: Test epic

Status: confirmed

## Stage 1 — first

### Issue: Done thing

- Spec: closed already.
- Depends on: none
- yolo: no
- Published: #11

### Issue: Open thing

- Spec: ready to work.
- Depends on: #11
- yolo: yes
- Published: #12

## Stage 2 — second

### Issue: Future thing

- Spec: not yet published.
- Depends on: #12
- yolo: no
"""


def _seed_epic_plan(tmp_path: Path) -> None:
    epics = tmp_path / ".issueflows" / "05-epics"
    epics.mkdir(parents=True)
    (epics / "epic9_plan.md").write_text(_EPIC_PLAN, encoding="utf-8")


def test_agent_epic_status_reports_stages_and_candidates(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    _seed_epic_plan(tmp_path)
    states = {11: "closed", 12: "open"}
    monkeypatch.setattr(gitutils_module, "remote_owner_repo", lambda _cwd: None)
    monkeypatch.setattr(
        gitutils_module,
        "gh_issue_state",
        lambda number, _cwd, _repo=None: states.get(number),
    )

    result = runner.invoke(
        app, ["agent", "epic-status", "9", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["epic"] == 9
    assert payload["plan_status"] == "confirmed"
    stage1, stage2 = payload["stages"]
    assert stage1["done"] is False  # #12 is still open
    assert stage1["issues"][0]["state"] == "closed"
    assert stage1["issues"][1]["state"] == "open"
    # #12's only dependency (#11) is closed -> unblocked candidate.
    assert stage1["issues"][1]["blocked_by"] == []
    assert payload["current_stage"] == 1
    assert payload["next_candidates"] == [12]
    # Stage 2's spec is unpublished and blocked by the open #12.
    assert stage2["issues"][0]["state"] == "unpublished"
    assert stage2["issues"][0]["blocked_by"] == [12]


def test_agent_epic_status_local_skips_github(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    _seed_epic_plan(tmp_path)

    def explode(*_a: object, **_kw: object) -> object:
        raise AssertionError("gh must not be queried with --local")

    monkeypatch.setattr(gitutils_module, "gh_issue_state", explode)
    monkeypatch.setattr(gitutils_module, "remote_owner_repo", lambda _cwd: None)

    result = runner.invoke(
        app, ["agent", "epic-status", "9", "-C", str(tmp_path), "--local", "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["local"] is True
    assert payload["stages"][0]["issues"][0]["state"] == "published"


def test_agent_epic_status_missing_plan_fails(
    runner: CliRunner, tmp_path: Path
) -> None:
    result = runner.invoke(
        app, ["agent", "epic-status", "9", "-C", str(tmp_path), "--json"]
    )
    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert "no epic plan" in payload["error"]


# ---------------------------------------------------------------------------
# agent queue (issue #140)
# ---------------------------------------------------------------------------


def _fake_meta(
    number: int,
    *,
    state: str = "OPEN",
    body: str = "",
    labels: list[str] | None = None,
) -> dict[str, object]:
    return {
        "number": number,
        "title": f"Issue {number}",
        "state": state,
        "body": body,
        "labels": [{"name": name} for name in (labels or [])],
    }


def test_agent_queue_numbers_orders_by_dependencies(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    metas = {
        1: _fake_meta(1, labels=["yolo"]),
        2: _fake_meta(2, body="Depends on #1."),
        3: _fake_meta(3, state="CLOSED"),
    }
    monkeypatch.setattr(gitutils_module, "remote_owner_repo", lambda _cwd: None)
    monkeypatch.setattr(
        gitutils_module,
        "gh_issue_meta",
        lambda number, _cwd, _repo=None: metas.get(number),
    )

    result = runner.invoke(
        app, ["agent", "queue", "2", "1", "3", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert [entry["number"] for entry in payload["queue"]] == [1, 2]
    assert payload["queue"][0]["yolo"] is True
    assert payload["skipped_closed"] == [3]


def test_agent_queue_refuses_partial_fetch(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "remote_owner_repo", lambda _cwd: None)
    monkeypatch.setattr(
        gitutils_module, "gh_issue_meta", lambda _n, _cwd, _repo=None: None
    )

    result = runner.invoke(app, ["agent", "queue", "1", "-C", str(tmp_path), "--json"])

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert "refusing" in payload["error"]


def test_agent_queue_reports_cycle(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    metas = {
        1: _fake_meta(1, body="Depends on #2."),
        2: _fake_meta(2, body="Depends on #1."),
    }
    monkeypatch.setattr(gitutils_module, "remote_owner_repo", lambda _cwd: None)
    monkeypatch.setattr(
        gitutils_module,
        "gh_issue_meta",
        lambda number, _cwd, _repo=None: metas.get(number),
    )

    result = runner.invoke(
        app, ["agent", "queue", "1", "2", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["cycle"] == [1, 2]


def test_agent_queue_requires_exactly_one_source(
    runner: CliRunner, tmp_path: Path
) -> None:
    result = runner.invoke(
        app,
        ["agent", "queue", "1", "--label", "x", "-C", str(tmp_path), "--json"],
    )
    assert result.exit_code == 2

    result = runner.invoke(app, ["agent", "queue", "-C", str(tmp_path), "--json"])
    assert result.exit_code == 2


def test_agent_queue_epic_source_uses_current_stage(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from issue_flow import gitutils as gitutils_module

    _seed_epic_plan(tmp_path)  # epic 9: stage 1 has #11 (closed) and #12 (open)
    states = {11: "closed", 12: "open"}
    monkeypatch.setattr(gitutils_module, "remote_owner_repo", lambda _cwd: None)
    monkeypatch.setattr(
        gitutils_module,
        "gh_issue_state",
        lambda number, _cwd, _repo=None: states.get(number),
    )

    result = runner.invoke(
        app, ["agent", "queue", "--epic", "9", "-C", str(tmp_path), "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["source"] == {"type": "epic", "value": 9, "stage": 1}
    assert [entry["number"] for entry in payload["queue"]] == [12]
    assert payload["queue"][0]["yolo"] is True
    assert payload["skipped_closed"] == [11]


# ---------------------------------------------------------------------------
# workspace registry (issue #126)
# ---------------------------------------------------------------------------


def _seed_workspace(tmp_path: Path, *, default: str | None = "alpha") -> Path:
    """Workspace dir with two scaffolded members and a registry file."""
    workspace = tmp_path / "workspace"
    for name in ("alpha", "beta"):
        (workspace / name / ".issueflows" / "01-current-issues").mkdir(parents=True)
    lines = ["[workspace]"]
    if default is not None:
        lines.append(f'default = "{default}"')
    (workspace / "issueflow-workspace.toml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return workspace


def test_agent_resolve_falls_back_to_workspace_default(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """From the workspace root (no scaffold above), the default member wins."""
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "remote_owner_repo", lambda _cwd: None)
    monkeypatch.setattr(gitutils_module, "git_available", lambda: False)

    workspace = _seed_workspace(tmp_path, default="alpha")

    result = runner.invoke(app, ["agent", "resolve", "-C", str(workspace), "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["project_root"] == str((workspace / "alpha").resolve())
    assert payload["resolved_via_workspace_default"] is True
    assert payload["workspace_root"] == str(workspace.resolve())
    assert payload["workspace_default"] == "alpha"
    assert payload["workspace_members"] == [
        str((workspace / "alpha").resolve()),
        str((workspace / "beta").resolve()),
    ]


def test_agent_resolve_nearest_scaffold_beats_workspace_default(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Inside a member repo, that repo wins even when another is the default."""
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "remote_owner_repo", lambda _cwd: None)
    monkeypatch.setattr(gitutils_module, "git_available", lambda: False)

    workspace = _seed_workspace(tmp_path, default="alpha")

    result = runner.invoke(
        app, ["agent", "resolve", "-C", str(workspace / "beta"), "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["project_root"] == str((workspace / "beta").resolve())
    assert payload["resolved_via_workspace_default"] is False
    # Workspace context is still reported for the agent's awareness.
    assert payload["workspace_default"] == "alpha"


def test_agent_resolve_no_default_still_fails_from_workspace_root(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a default, the registry adds context but resolution still asks."""
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "remote_owner_repo", lambda _cwd: None)
    monkeypatch.setattr(gitutils_module, "git_available", lambda: False)

    workspace = _seed_workspace(tmp_path, default=None)

    result = runner.invoke(app, ["agent", "resolve", "-C", str(workspace), "--json"])

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["project_root"] is None
    assert payload["workspace_root"] == str(workspace.resolve())
    assert len(payload["workspace_members"]) == 2


def test_workspace_init_creates_registry(runner: CliRunner, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    for name in ("alpha", "beta"):
        (workspace / name / ".issueflows").mkdir(parents=True)
    (workspace / "plain").mkdir()

    result = runner.invoke(
        app,
        ["workspace", "init", str(workspace), "--default", "beta", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["written"] is True
    assert payload["default"] == "beta"
    assert payload["members"] == ["alpha", "beta"]
    text = (workspace / "issueflow-workspace.toml").read_text(encoding="utf-8")
    assert 'default = "beta"' in text
    assert '"alpha"' in text
    assert '"plain"' not in text


def test_workspace_init_single_member_becomes_default(
    runner: CliRunner, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "solo" / ".issueflows").mkdir(parents=True)

    result = runner.invoke(app, ["workspace", "init", str(workspace), "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["default"] == "solo"


def test_workspace_init_refuses_unknown_default(
    runner: CliRunner, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "alpha" / ".issueflows").mkdir(parents=True)

    result = runner.invoke(
        app, ["workspace", "init", str(workspace), "--default", "nope", "--json"]
    )

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["written"] is False
    assert "nope" in payload["error"]
    assert not (workspace / "issueflow-workspace.toml").exists()


def test_workspace_init_refuses_without_members(
    runner: CliRunner, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "plain").mkdir(parents=True)

    result = runner.invoke(app, ["workspace", "init", str(workspace), "--json"])

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["written"] is False


def test_workspace_init_refuses_overwrite_without_force(
    runner: CliRunner, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "alpha" / ".issueflows").mkdir(parents=True)
    registry = workspace / "issueflow-workspace.toml"
    registry.write_text("# hand-written\n[workspace]\n", encoding="utf-8")

    result = runner.invoke(app, ["workspace", "init", str(workspace), "--json"])
    assert result.exit_code == 1
    assert "hand-written" in registry.read_text(encoding="utf-8")

    result = runner.invoke(
        app, ["workspace", "init", str(workspace), "--force", "--json"]
    )
    assert result.exit_code == 0, result.output
    assert "hand-written" not in registry.read_text(encoding="utf-8")


def _seed_scaffolded_workspace(tmp_path: Path) -> Path:
    """Workspace with two fully scaffolded members and a registry file."""
    from issue_flow.init import run_init

    workspace = tmp_path / "workspace"
    for name in ("alpha", "beta"):
        run_init(workspace / name)
    (workspace / "issueflow-workspace.toml").write_text(
        '[workspace]\ndefault = "alpha"\n', encoding="utf-8"
    )
    return workspace


def test_workspace_update_refreshes_all_members(
    runner: CliRunner, tmp_path: Path
) -> None:
    workspace = _seed_scaffolded_workspace(tmp_path)
    rule = workspace / "alpha" / ".cursor" / "rules" / "issueflow-rules.mdc"
    rule.write_text("stale custom content", encoding="utf-8")

    result = runner.invoke(
        app,
        ["workspace", "update", str(workspace), "--skip-dep-check", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["ok"] is True
    assert payload["ok_count"] == 2
    assert payload["fail_count"] == 0
    assert len(payload["members"]) == 2
    assert all(m["ok"] for m in payload["members"])
    assert "stale custom content" not in rule.read_text(encoding="utf-8")
    beta_rule = workspace / "beta" / ".cursor" / "rules" / "issueflow-rules.mdc"
    assert beta_rule.is_file()


def test_workspace_update_without_registry_fails(
    runner: CliRunner, tmp_path: Path
) -> None:
    bare = tmp_path / "nowhere"
    bare.mkdir()

    result = runner.invoke(
        app,
        ["workspace", "update", str(bare), "--skip-dep-check", "--json"],
    )

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["ok"] is False
    assert "issueflow-workspace.toml" in payload["error"]


def test_workspace_update_partial_failure_continues(
    runner: CliRunner, tmp_path: Path
) -> None:
    from issue_flow.init import run_init

    workspace = tmp_path / "workspace"
    run_init(workspace / "alpha")
    bad = workspace / "beta"
    (bad / ".issueflows").mkdir(parents=True)
    (bad / ".issueflows" / "config.toml").write_text(
        '[issueflow]\nmode = "nonexistent-mode"\n', encoding="utf-8"
    )
    (workspace / "issueflow-workspace.toml").write_text(
        '[workspace]\nmembers = ["alpha", "beta"]\n', encoding="utf-8"
    )
    alpha_rule = workspace / "alpha" / ".cursor" / "rules" / "issueflow-rules.mdc"
    alpha_rule.write_text("STALE_MARKER_ONLY", encoding="utf-8")

    result = runner.invoke(
        app,
        ["workspace", "update", str(workspace), "--skip-dep-check", "--json"],
    )

    assert result.exit_code == 1
    payload = _json(result.stdout)
    assert payload["ok"] is False
    assert payload["ok_count"] == 1
    assert payload["fail_count"] == 1
    by_name = {m["name"]: m for m in payload["members"]}
    assert by_name["alpha"]["ok"] is True
    assert by_name["beta"]["ok"] is False
    assert "STALE_MARKER_ONLY" not in alpha_rule.read_text(encoding="utf-8")


def test_workspace_help_lists_update(runner: CliRunner) -> None:
    result = runner.invoke(app, ["workspace", "--help"])
    assert result.exit_code == 0
    assert "update" in _plain(result.stdout)


# ---------------------------------------------------------------------------
# config sub-app
# ---------------------------------------------------------------------------


def _clear_issueflow_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "ISSUEFLOW_MODE",
        "ISSUEFLOW_CAVEMAN_DEFAULT",
        "ISSUEFLOW_GRILL_ME_DEFAULT",
        "ISSUEFLOW_LABEL_FLOWS",
        "ISSUEFLOW_YOLO_LABEL",
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

    result = runner.invoke(app, ["config", "add", "-C", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = _json(result.stdout)
    assert payload["written"] is True
    assert payload["overwritten"] is False
    assert payload["mode"] == "standard"
    assert payload["caveman_default"] is False
    assert payload["grill_me_default"] is False
    assert payload["label_flows"] is True
    assert payload["yolo_label"] == "yolo"

    cfg = tmp_path / ".issueflows" / "config.toml"
    assert cfg.is_file()
    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert data["issueflow"]["mode"] == "standard"
    assert data["issueflow"]["caveman_default"] is False
    assert data["issueflow"]["grill_me_default"] is False
    assert data["issueflow"]["label_flows"] is True
    assert data["issueflow"]["yolo_label"] == "yolo"


def test_config_add_reads_env(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tomllib

    monkeypatch.setenv("ISSUEFLOW_MODE", "simple")
    monkeypatch.setenv("ISSUEFLOW_CAVEMAN_DEFAULT", "true")
    monkeypatch.delenv("ISSUEFLOW_GRILL_ME_DEFAULT", raising=False)
    monkeypatch.setenv("ISSUEFLOW_LABEL_FLOWS", "false")
    monkeypatch.setenv("ISSUEFLOW_YOLO_LABEL", "fast-track")

    result = runner.invoke(app, ["config", "add", "-C", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    cfg = tmp_path / ".issueflows" / "config.toml"
    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert data["issueflow"]["mode"] == "simple"
    assert data["issueflow"]["caveman_default"] is True
    assert data["issueflow"]["grill_me_default"] is False
    assert data["issueflow"]["label_flows"] is False
    assert data["issueflow"]["yolo_label"] == "fast-track"


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
        '[issueflow]\nmode = "simple"\n\n# keep me\n[modes.mine]\nextends = "simple"\n',
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
    # The [issueflow] keys are upserted to env/defaults.
    assert data["issueflow"]["mode"] == "standard"
    assert data["issueflow"]["caveman_default"] is False
    assert data["issueflow"]["grill_me_default"] is False
    assert data["issueflow"]["label_flows"] is True
    assert data["issueflow"]["yolo_label"] == "yolo"
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
    assert payload["cycle_active"] is False


def test_status_reports_in_flight_cycle(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cycle_status.md in current-issues is reported as an in-flight cycle."""
    from issue_flow import gitutils as gitutils_module

    monkeypatch.setattr(gitutils_module, "current_branch", lambda _cwd: None)
    current = tmp_path / ".issueflows" / "01-current-issues"
    current.mkdir(parents=True)
    (current / "cycle_status.md").write_text(
        "# Cycle\n- [ ] #12 — thing — pending\n", encoding="utf-8"
    )

    result = runner.invoke(app, ["status", str(tmp_path), "--local", "--json"])

    assert result.exit_code == 0, result.output
    assert _json(result.stdout)["cycle_active"] is True


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
