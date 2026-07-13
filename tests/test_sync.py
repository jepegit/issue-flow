"""Tests for issue_flow.sync — folder → label sync planning and apply."""

from __future__ import annotations

from pathlib import Path

import pytest

from issue_flow.config import Settings
from issue_flow import sync as sync_module


def _layout(
    base: Path,
    *,
    current: list[int] | None = None,
    parked: list[int] | None = None,
    solved: list[int] | None = None,
) -> Path:
    settings = Settings()
    root = base / "project"
    for folder, numbers in (
        (settings.current_issues_folder, current or []),
        (settings.partly_solved_folder, parked or []),
        (settings.solved_folder, solved or []),
    ):
        target = root / settings.issueflows_dir / folder
        target.mkdir(parents=True)
        for number in numbers:
            (target / f"issue{number}_status.md").write_text(
                "# status\n\n- [ ] Done\n", encoding="utf-8"
            )
    return root


def test_collect_maps_folders_to_states(tmp_path: Path) -> None:
    root = _layout(tmp_path, current=[1], parked=[2], solved=[3])
    settings = Settings()
    states, folders, warnings = sync_module.collect_tracked_issues(root, settings)
    assert warnings == []
    assert states == {1: "current", 2: "parked", 3: "solved"}
    assert folders[1] == settings.current_issues_folder
    assert folders[3] == settings.solved_folder


def test_collect_prefers_current_on_duplicate(tmp_path: Path) -> None:
    root = _layout(tmp_path, current=[5], solved=[5])
    settings = Settings()
    states, _, warnings = sync_module.collect_tracked_issues(root, settings)
    assert states[5] == "current"
    assert any("keeping" in w for w in warnings)


def test_plan_issue_sync_label_diff() -> None:
    config = sync_module.SyncSettings()
    plan = sync_module.plan_issue_sync(
        7,
        "solved",
        "03-solved-issues",
        config=config,
        current_labels=["status:current", "yolo"],
        current_milestone=None,
        issue_open=True,
    )
    assert plan.labels_to_add == ["status:solved"]
    assert plan.labels_to_remove == ["status:current"]
    assert plan.close is False


def test_plan_issue_sync_skips_when_already_synced() -> None:
    config = sync_module.SyncSettings()
    plan = sync_module.plan_issue_sync(
        7,
        "current",
        "01-current-issues",
        config=config,
        current_labels=["status:current", "yolo"],
        current_milestone=None,
        issue_open=True,
    )
    assert plan.skipped is True
    assert plan.labels_to_add == []
    assert plan.labels_to_remove == []


def test_plan_issue_sync_close_on_solved_when_enabled() -> None:
    config = sync_module.SyncSettings(close_on_solved=True)
    plan = sync_module.plan_issue_sync(
        9,
        "solved",
        "03-solved-issues",
        config=config,
        current_labels=["status:solved"],
        current_milestone=None,
        issue_open=True,
    )
    assert plan.close is True


def test_plan_sync_dry_run_without_gh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _layout(tmp_path, current=[10])
    settings = Settings()
    config = sync_module.SyncSettings()

    monkeypatch.setattr(
        sync_module.gitutils,
        "gh_issue_meta",
        lambda number, cwd, repo=None: {
            "number": number,
            "state": "OPEN",
            "labels": [{"name": "bug"}],
            "milestone": None,
        },
    )

    plans, _ = sync_module.plan_sync(root, settings, config, repo="o/r")
    assert len(plans) == 1
    assert plans[0].labels_to_add == ["status:current"]

    result = sync_module.apply_plan(
        plans[0], root, repo="o/r", config=config, dry_run=True
    )
    assert result.labels_added == ["status:current"]
    assert result.error is None


def test_apply_plan_calls_gh_issue_edit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path
    plan = sync_module.IssueSyncPlan(
        number=11,
        state="parked",
        folder="02-partly-solved-issues",
        labels_to_add=["status:parked"],
        labels_to_remove=["status:current"],
    )
    calls: list[dict] = []

    def fake_edit(
        number, cwd, *, repo=None, add_labels=None, remove_labels=None, milestone=None
    ):
        calls.append(
            {
                "number": number,
                "add": add_labels,
                "remove": remove_labels,
                "milestone": milestone,
            }
        )
        return True, None

    monkeypatch.setattr(sync_module.gitutils, "gh_issue_edit", fake_edit)
    result = sync_module.apply_plan(
        plan, root, repo="o/r", config=sync_module.SyncSettings(), dry_run=False
    )
    assert result.error is None
    assert calls == [
        {
            "number": 11,
            "add": ["status:parked"],
            "remove": ["status:current"],
            "milestone": None,
        }
    ]


def test_load_sync_settings_from_config(tmp_path: Path) -> None:
    settings = Settings()
    cfg = settings.config_path(tmp_path)
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        """
[issueflow.sync]
enabled = false
label_prefix = "if:"
labels = true
milestones = false
close_on_solved = false

[issueflow.sync.milestone_map]
current = "Active"
parked = ""
solved = ""
""".strip(),
        encoding="utf-8",
    )
    loaded = sync_module.load_sync_settings(settings, tmp_path)
    assert loaded.enabled is False
    assert loaded.label_prefix == "if:"
    assert loaded.milestone_map["current"] == "Active"
