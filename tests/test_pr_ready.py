"""Tests for issue-flow agent pr-ready."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import patch

from rich.console import Console
from typer.testing import CliRunner

from issue_flow.agent import classify_pr_ready, run_pr_ready
from issue_flow.cli import app

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _pr(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "number": 317,
        "title": "pr-ready",
        "url": "https://example/317",
        "headRefName": "317-pr-ready",
        "baseRefName": "main",
        "state": "OPEN",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": "",
        "statusCheckRollup": [
            {
                "name": "tests",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "isRequired": True,
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_classify_ready_clean() -> None:
    result = classify_pr_ready(_pr(), gh_available=True)
    assert result["state"] == "ready"
    assert result["pr"] == 317


def test_classify_ready_unstable_optional_pending() -> None:
    result = classify_pr_ready(
        _pr(
            mergeStateStatus="UNSTABLE",
            statusCheckRollup=[
                {
                    "name": "tests",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                    "isRequired": True,
                },
                {
                    "name": "Cursor Approval Agent",
                    "status": "IN_PROGRESS",
                    "conclusion": "",
                    "isRequired": False,
                },
            ],
        ),
        gh_available=True,
    )
    assert result["state"] == "ready"
    assert "Cursor Approval Agent" in result["pending_checks"]


def test_classify_ready_unstable_optional_failure_omitted_required() -> None:
    """UNSTABLE + MERGEABLE + optional noise is ready when required is known."""
    result = classify_pr_ready(
        _pr(
            mergeStateStatus="UNSTABLE",
            statusCheckRollup=[
                {
                    "name": "tests",
                    "status": "COMPLETED",
                    "conclusion": "SUCCESS",
                    "isRequired": True,
                },
                {
                    "name": "Cursor Approval Agent",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                    "isRequired": False,
                },
            ],
        ),
        gh_available=True,
    )
    assert result["state"] == "ready"
    assert "Cursor Approval Agent" in result["failing_checks"]


def test_classify_pending_required_check() -> None:
    result = classify_pr_ready(
        _pr(
            mergeStateStatus="BLOCKED",
            statusCheckRollup=[
                {
                    "name": "tests",
                    "status": "IN_PROGRESS",
                    "conclusion": "",
                    "isRequired": True,
                }
            ],
        ),
        gh_available=True,
    )
    assert result["state"] == "pending"


def test_classify_blocked_draft_and_conflicts_and_review() -> None:
    assert classify_pr_ready(_pr(isDraft=True), gh_available=True)["state"] == "blocked"
    assert (
        classify_pr_ready(
            _pr(mergeable="CONFLICTING", mergeStateStatus="DIRTY"),
            gh_available=True,
        )["state"]
        == "blocked"
    )
    assert (
        classify_pr_ready(_pr(reviewDecision="CHANGES_REQUESTED"), gh_available=True)[
            "state"
        ]
        == "blocked"
    )
    assert (
        classify_pr_ready(
            _pr(
                statusCheckRollup=[
                    {
                        "name": "tests",
                        "status": "COMPLETED",
                        "conclusion": "FAILURE",
                        "isRequired": True,
                    }
                ]
            ),
            gh_available=True,
        )["state"]
        == "blocked"
    )


def test_classify_unknown_without_gh_or_payload() -> None:
    missing_gh = classify_pr_ready(None, gh_available=False)
    assert missing_gh["state"] == "unknown"
    assert "gh is not on PATH" in missing_gh["notes"]
    missing_pr = classify_pr_ready(None, gh_available=True)
    assert missing_pr["state"] == "unknown"


def test_classify_pending_review_required() -> None:
    result = classify_pr_ready(_pr(reviewDecision="REVIEW_REQUIRED"), gh_available=True)
    assert result["state"] == "pending"


def test_classify_omitted_required_pending_is_not_ready() -> None:
    """UNSTABLE + MERGEABLE + omitted isRequired pending must stay pending."""
    result = classify_pr_ready(
        _pr(
            mergeStateStatus="UNSTABLE",
            statusCheckRollup=[
                {
                    "name": "test (3.13)",
                    "status": "IN_PROGRESS",
                    "conclusion": "",
                }
            ],
        ),
        gh_available=True,
    )
    assert result["state"] == "pending"
    assert "test (3.13)" in result["pending_checks"]


def test_classify_omitted_required_failure_blocks() -> None:
    result = classify_pr_ready(
        _pr(
            statusCheckRollup=[
                {
                    "name": "tests",
                    "status": "COMPLETED",
                    "conclusion": "FAILURE",
                }
            ]
        ),
        gh_available=True,
    )
    assert result["state"] == "blocked"


def test_pr_ready_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["agent", "pr-ready", "--help"])
    assert result.exit_code == 0
    out = _strip_ansi(result.stdout)
    assert "--watch" in out
    assert "Never merges" in out or "never merges" in out.lower()


def test_run_pr_ready_ready_exit_zero(tmp_path: Path) -> None:
    with (
        patch("issue_flow.agent.gitutils.gh_available", return_value=True),
        patch("issue_flow.agent.gitutils.worktree_home_path", return_value=tmp_path),
        patch(
            "issue_flow.agent.gitutils.remote_owner_repo",
            return_value=("acme", "widgets"),
        ),
        patch("issue_flow.agent.gitutils.gh_pr_view", return_value=_pr()),
        patch("issue_flow.agent._emit_json") as emit,
    ):
        code = run_pr_ready(tmp_path, Console(), 317, watch=False, as_json=True)
    assert code == 0
    payload: dict[str, Any] = emit.call_args[0][1]
    assert payload["state"] == "ready"
    assert payload["pr"] == 317
    assert payload["repo"] == "acme/widgets"


def test_run_pr_ready_missing_gh(tmp_path: Path) -> None:
    with (
        patch("issue_flow.agent.gitutils.gh_available", return_value=False),
        patch("issue_flow.agent._emit_json") as emit,
    ):
        code = run_pr_ready(tmp_path, Console(), 317, watch=False, as_json=True)
    assert code == 1
    assert emit.call_args[0][1]["state"] == "unknown"


def test_run_pr_ready_no_pr_for_branch(tmp_path: Path) -> None:
    with (
        patch("issue_flow.agent.gitutils.gh_available", return_value=True),
        patch("issue_flow.agent.gitutils.worktree_home_path", return_value=tmp_path),
        patch(
            "issue_flow.agent.gitutils.remote_owner_repo",
            return_value=("acme", "widgets"),
        ),
        patch("issue_flow.agent.gitutils.gh_pr_view", return_value=None),
        patch("issue_flow.agent._emit_json") as emit,
    ):
        code = run_pr_ready(tmp_path, Console(), None, watch=False, as_json=True)
    assert code == 1
    payload: dict[str, Any] = emit.call_args[0][1]
    assert payload["state"] == "unknown"
    assert "no PR for this branch" in payload["notes"]


def test_run_pr_ready_watch_times_out_without_real_sleep(tmp_path: Path) -> None:
    slept: list[float] = []

    with (
        patch("issue_flow.agent.gitutils.gh_available", return_value=True),
        patch("issue_flow.agent.gitutils.worktree_home_path", return_value=tmp_path),
        patch(
            "issue_flow.agent.gitutils.remote_owner_repo",
            return_value=("acme", "widgets"),
        ),
        patch(
            "issue_flow.agent.gitutils.gh_pr_view",
            return_value=_pr(mergeable="UNKNOWN", mergeStateStatus="UNKNOWN"),
        ),
        patch(
            "issue_flow.agent.Settings.resolve_checks_watch_minutes",
            return_value=0,
        ),
        patch("issue_flow.agent._emit_json") as emit,
    ):
        code = run_pr_ready(
            tmp_path,
            Console(),
            317,
            watch=True,
            as_json=True,
            sleep_fn=slept.append,
            monotonic_fn=lambda: 0.0,
        )
    assert code == 1
    assert slept == []
    notes = emit.call_args[0][1]["notes"]
    assert any("watch budget" in str(n) for n in notes)


def test_run_pr_ready_watch_becomes_ready(tmp_path: Path) -> None:
    views = [
        _pr(mergeable="UNKNOWN", mergeStateStatus="UNKNOWN"),
        _pr(),
    ]
    slept: list[float] = []
    clock = {"t": 0.0}

    def monotonic() -> float:
        return clock["t"]

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        clock["t"] += seconds

    with (
        patch("issue_flow.agent.gitutils.gh_available", return_value=True),
        patch("issue_flow.agent.gitutils.worktree_home_path", return_value=tmp_path),
        patch(
            "issue_flow.agent.gitutils.remote_owner_repo",
            return_value=("acme", "widgets"),
        ),
        patch("issue_flow.agent.gitutils.gh_pr_view", side_effect=views),
        patch(
            "issue_flow.agent.Settings.resolve_checks_watch_minutes",
            return_value=15,
        ),
        patch("issue_flow.agent._emit_json") as emit,
    ):
        code = run_pr_ready(
            tmp_path,
            Console(),
            317,
            watch=True,
            as_json=True,
            sleep_fn=sleep,
            monotonic_fn=monotonic,
            poll_seconds=15.0,
        )
    assert code == 0
    assert slept == [15.0]
    assert emit.call_count == 1
    assert emit.call_args[0][1]["state"] == "ready"
