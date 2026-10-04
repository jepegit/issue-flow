"""graphify_gitignored: managed .gitignore block and tracked-path note."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from issue_flow.config import Settings
from issue_flow.surfaces import note_tracked_graphify, sync_graphify_gitignore

_BEGIN = "# BEGIN issue-flow graphify (generated; do not edit)"
_END = "# END issue-flow graphify"


def test_sync_writes_block_and_is_idempotent(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("# keep\nfoo.txt\n", encoding="utf-8")
    assert sync_graphify_gitignore(tmp_path, enabled=True) is True
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "# keep" in text
    assert "foo.txt" in text
    assert _BEGIN in text
    assert "graphify-out/" in text
    assert _END in text
    assert sync_graphify_gitignore(tmp_path, enabled=True) is False


def test_sync_remove_keeps_unrelated_lines(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("# keep\nfoo.txt\n", encoding="utf-8")
    sync_graphify_gitignore(tmp_path, enabled=True)
    assert sync_graphify_gitignore(tmp_path, enabled=False) is True
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert _BEGIN not in text
    assert "graphify-out/" not in text
    assert "# keep" in text
    assert "foo.txt" in text
    assert sync_graphify_gitignore(tmp_path, enabled=False) is False


def test_sync_disabled_does_not_create_gitignore(tmp_path: Path) -> None:
    assert sync_graphify_gitignore(tmp_path, enabled=False) is False
    assert not (tmp_path / ".gitignore").exists()


def test_note_tracked_graphify_when_indexed(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    out = tmp_path / "graphify-out"
    out.mkdir()
    (out / "GRAPH_REPORT.md").write_text("x\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "graphify-out"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    assert note_tracked_graphify(tmp_path) is True


def test_note_tracked_graphify_when_clean(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    assert note_tracked_graphify(tmp_path) is False


def test_graphify_gitignored_persisted_beats_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ISSUEFLOW_GRAPHIFY_GITIGNORED", "true")
    cfg = tmp_path / ".issueflows"
    cfg.mkdir()
    (cfg / "config.toml").write_text(
        "[issueflow]\ngraphify_gitignored = false\n", encoding="utf-8"
    )
    assert Settings().resolve_graphify_gitignored(tmp_path) is False
