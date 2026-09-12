"""Tests for issue-flow agent pr-sync."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

from rich.console import Console
from typer.testing import CliRunner

from issue_flow.agent import _pr_needs_sync, run_pr_sync
from issue_flow.cli import app


def test_pr_needs_sync_dirty_and_conflicting() -> None:
    assert _pr_needs_sync({"mergeable": "CONFLICTING", "mergeStateStatus": "DIRTY"})
    assert _pr_needs_sync({"mergeable": "MERGEABLE", "mergeStateStatus": "BEHIND"})
    assert not _pr_needs_sync({"mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN"})


def test_pr_sync_dry_run_lists_dirty_only(tmp_path: Path) -> None:
    prs = [
        {
            "number": 1,
            "title": "clean",
            "url": "https://example/1",
            "headRefName": "1-clean",
            "baseRefName": "main",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
        },
        {
            "number": 2,
            "title": "dirty",
            "url": "https://example/2",
            "headRefName": "2-dirty",
            "baseRefName": "main",
            "mergeable": "CONFLICTING",
            "mergeStateStatus": "DIRTY",
        },
    ]

    with (
        patch("issue_flow.agent.gitutils.git_available", return_value=True),
        patch("issue_flow.agent.gitutils.gh_available", return_value=True),
        patch("issue_flow.agent.gitutils.worktree_home_path", return_value=tmp_path),
        patch("issue_flow.agent.gitutils.default_branch", return_value="main"),
        patch(
            "issue_flow.agent.gitutils.remote_owner_repo",
            return_value=("acme", "widgets"),
        ),
        patch("issue_flow.agent.gitutils.fetch_prune", return_value=True),
        patch("issue_flow.agent.gitutils.gh_open_prs", return_value=prs),
        patch("issue_flow.agent._emit_json") as emit,
    ):
        code = run_pr_sync(
            tmp_path,
            Console(),
            numbers=None,
            all_open=False,
            dirty_only=True,
            dry_run=True,
            push=True,
            fail_fast=True,
            strategy="rebase",
            cleanup_worktrees=True,
            as_json=True,
        )
    assert code == 0
    payload: dict[str, Any] = emit.call_args[0][1]
    assert [c["number"] for c in payload["candidates"]] == [2]
    assert payload["dry_run"] is True
    assert payload["results"] == []


def test_pr_sync_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["agent", "pr-sync", "--help"])
    assert result.exit_code == 0
    assert "force-with-lease" in result.stdout
    assert "--dry-run" in result.stdout


def test_pr_sync_template_renders() -> None:
    from issue_flow.templating import render_template
    from tests.test_templating import _default_context

    rendered = render_template(
        "skills/iflow_pr_sync/SKILL.md.j2",
        {**_default_context(), "included_skills": ["iflow_pr_sync", "iflow_cleanup"]},
    )
    assert "name: iflow-pr-sync" in rendered
    assert "pr-sync" in rendered
    assert "force-with-lease" in rendered
