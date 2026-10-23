"""Scan commit trailers and rebuild HISTORY.md at release time.

Pure text lives in :mod:`issue_flow.history`. This module owns the git scan
window, the dirty / branch / HEAD guards, and the single file write.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from issue_flow import history
from issue_flow.gitutils import (
    current_branch,
    default_branch,
    head_sha,
    working_tree_clean,
)

GIT = "git"


@dataclass(frozen=True)
class ReleaseResult:
    """Outcome of :func:`release`."""

    ok: bool
    reason: str | None
    version: str | None
    path: str | None
    bullet_count: int


@dataclass(frozen=True)
class CheckResult:
    """Outcome of :func:`check_history_diff`."""

    ok: bool
    reason: str | None
    changed: bool


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [GIT, *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def _history_text(root: Path, history_file: str) -> str:
    path = root / history_file
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _anchor_sha(root: Path, history_file: str, heading: str | None) -> str | None:
    """Commit that introduced the current top version heading, if any."""
    if not heading:
        return None
    result = _git(
        root,
        "log",
        "--first-parent",
        "-1",
        "--format=%H",
        "-S",
        heading,
        "--",
        history_file,
    )
    sha = result.stdout.strip()
    return sha or None


def _messages_after(root: Path, anchor: str | None) -> list[str]:
    """Full messages of first-parent commits after ``anchor`` (oldest first)."""
    rev_range = f"{anchor}..HEAD" if anchor else "HEAD"
    listed = _git(root, "rev-list", "--reverse", "--first-parent", rev_range)
    if listed.returncode != 0:
        return []
    messages: list[str] = []
    for sha in listed.stdout.split():
        shown = _git(root, "log", "-1", "--format=%B", sha)
        if shown.returncode == 0:
            messages.append(shown.stdout)
    return messages


def list_notes(root: Path, history_file: str) -> list[history.ChangelogNote]:
    """Unreleased trailer notes. Does not write ``history_file``."""
    text = _history_text(root, history_file)
    anchor = _anchor_sha(root, history_file, history.top_version_heading(text))
    per_commit = [
        history.parse_message_notes(message)
        for message in _messages_after(root, anchor)
    ]
    notes = history.merge_commit_notes(per_commit)
    recorded = history.recorded_changelog_ids(text)
    return [note for note in notes if note.note_id not in recorded]


def release(
    root: Path,
    version: str,
    *,
    history_file: str,
    today: str,
) -> ReleaseResult:
    """Prepend one version section, or refuse without writing.

    Does not commit, tag, or bump a package version. ``today`` is the
    ``YYYY-MM-DD`` stamped on the new heading.
    """
    path = root / history_file
    if working_tree_clean(root) is not True:
        return ReleaseResult(False, history.DIRTY_TREE, None, None, 0)
    if current_branch(root) != default_branch(root):
        return ReleaseResult(False, history.NOT_DEFAULT_BRANCH, None, None, 0)
    before = head_sha(root)
    text = _history_text(root, history_file)
    if history.has_version_heading(text, version):
        return ReleaseResult(False, history.VERSION_EXISTS, None, None, 0)
    legacy = history.unreleased_bullet_lines(text)
    notes = list_notes(root, history_file)
    if history.release_is_empty(legacy, notes):
        return ReleaseResult(False, history.EMPTY_LIST, None, None, 0)
    if head_sha(root) != before:
        return ReleaseResult(False, history.HEAD_MOVED, None, None, 0)
    section = history.render_release_section(version, today, legacy, notes)
    updated = history.apply_release(text, section)
    path.write_text(updated, encoding="utf-8")
    return ReleaseResult(
        True,
        None,
        history.normalize_version(version),
        history_file,
        len(legacy) + len(notes),
    )


def check_history_diff(root: Path, history_file: str, base: str) -> CheckResult:
    """Fail when ``history_file`` changed vs ``base`` without a release trailer.

    A commit that touches the file must contain ``Changelog-Release:``. That is
    the feature-PR guard: ordinary closes do not edit the changelog.
    """
    diff = _git(root, "diff", "--name-only", f"{base}...HEAD", "--", history_file)
    if diff.returncode != 0:
        detail = (diff.stderr or diff.stdout or "git diff failed").strip()
        return CheckResult(False, detail, False)
    changed = bool(diff.stdout.strip())
    if not changed:
        return CheckResult(True, None, False)
    listed = _git(root, "log", "--format=%H", f"{base}..HEAD", "--", history_file)
    if listed.returncode != 0 or not listed.stdout.strip():
        return CheckResult(False, "history diff has no explaining commit", True)
    for sha in listed.stdout.split():
        shown = _git(root, "log", "-1", "--format=%B", sha)
        if not history.message_is_release(shown.stdout):
            short = sha[:12]
            return CheckResult(
                False,
                f"{history_file} changed in {short} without Changelog-Release",
                True,
            )
    return CheckResult(True, None, True)
