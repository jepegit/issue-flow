"""Read-only reader for the ``.issueflows/`` tracking tree.

This is the first piece of Python that actually *reads* the issue-tracking
state that the scaffolded agent workflow maintains under ``.issueflows/``.
Until now the folder layout, the ``issue<N>_*`` grouping, the lifecycle
stages, and the ``- [x] Done`` checkbox convention lived only as instructions
inside the Jinja templates. This module encodes those same rules once, so the
``issue-flow status`` / ``issue-flow agent ...`` commands can give agents (and
humans) a deterministic answer instead of re-deriving it by hand every time.

Nothing here ever talks to git or GitHub — that lives in
:mod:`issue_flow.gitutils`. This module only touches the filesystem, and only
:func:`apply_sweep` mutates it (moving whole issue groups between the
``01``/``02``/``03`` folders).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ``issue<N>_<suffix>.md`` — the leading number identifies the group, the
# suffix (``original`` / ``plan`` / ``status`` / supplementary) identifies the
# role. We are deliberately lenient about the suffix so supplementary files
# (e.g. ``issue42_status_followup.md``) still attach to the right group.
_ISSUE_FILE_RE = re.compile(r"^issue(\d+)_", re.IGNORECASE)

# The "done" marker the whole lifecycle keys off: a checked checkbox followed
# by the word ``done``. ``- [ ] Done`` (unchecked) must NOT match; only an
# ``x``/``X`` inside the brackets counts. Case-insensitive on ``done``.
_DONE_RE = re.compile(r"-\s*\[\s*x\s*\]\s*done", re.IGNORECASE)

# Lifecycle stages, in linear order. Each maps to the slash command that should
# run next (skills-first editors use the same names without the leading slash).
STAGE_INIT = "init"
STAGE_PLAN = "plan"
STAGE_START = "start"
STAGE_CLOSE = "close"

STAGE_NEXT_COMMAND: dict[str, str] = {
    STAGE_INIT: "/iflow-init",
    STAGE_PLAN: "/iflow-plan",
    STAGE_START: "/iflow-start",
    STAGE_CLOSE: "/iflow-close",
}


@dataclass
class IssueGroup:
    """All tracked files for a single issue number within one folder."""

    number: int
    location: str
    files: list[Path] = field(default_factory=list)

    @property
    def original(self) -> Path | None:
        return self._first_with_suffix("original")

    @property
    def plan(self) -> Path | None:
        return self._first_with_suffix("plan")

    @property
    def status_files(self) -> list[Path]:
        """Every file in the group whose suffix looks like a status file."""
        return [p for p in self.files if "status" in _suffix(p).lower()]

    @property
    def is_done(self) -> bool:
        """True iff any status file in the group carries a checked Done marker."""
        return any(file_marks_done(p) for p in self.status_files)

    @property
    def stage(self) -> str:
        """Lifecycle stage using the same first-match logic as ``/iflow``."""
        if self.original is None:
            return STAGE_INIT
        if self.plan is None:
            return STAGE_PLAN
        if self.is_done:
            return STAGE_CLOSE
        return STAGE_START

    @property
    def next_command(self) -> str:
        return STAGE_NEXT_COMMAND[self.stage]

    def title(self) -> str | None:
        """Best-effort issue title parsed from the ``# Issue #N: <title>`` line."""
        original = self.original
        if original is None:
            return None
        try:
            text = original.read_text(encoding="utf-8")
        except OSError:
            return None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
                # Drop a leading "Issue #N:" / "Issue N:" prefix if present.
                match = re.match(r"issue\s*#?\d+\s*:?\s*(.*)", heading, re.IGNORECASE)
                if match and match.group(1):
                    return match.group(1).strip()
                if heading:
                    return heading
        return None

    def _first_with_suffix(self, suffix: str) -> Path | None:
        for path in self.files:
            if _suffix(path).lower() == suffix:
                return path
        return None


def _suffix(path: Path) -> str:
    """Return the ``issue<N>_<suffix>`` suffix part of a filename (no extension)."""
    match = _ISSUE_FILE_RE.match(path.name)
    if not match:
        return ""
    return path.stem[len("issue") + len(match.group(1)) + 1 :]


def file_marks_done(path: Path) -> bool:
    """True iff ``path`` contains a checked ``- [x] Done`` marker."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return _DONE_RE.search(text) is not None


def group_issue_files(folder: Path) -> dict[int, IssueGroup]:
    """Group ``issue<N>_*`` files in ``folder`` by issue number.

    Missing folders yield an empty mapping (the tracking tree may not exist
    yet, or a project may have customised the folder names).
    """
    groups: dict[int, IssueGroup] = {}
    if not folder.is_dir():
        return groups
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        match = _ISSUE_FILE_RE.match(path.name)
        if not match:
            continue
        number = int(match.group(1))
        group = groups.get(number)
        if group is None:
            group = IssueGroup(number=number, location=folder.name)
            groups[number] = group
        group.files.append(path)
    return groups


@dataclass
class FocusResolution:
    """Outcome of resolving which issue is the current focus."""

    number: int | None
    resolved_via: str  # "branch" | "single-group" | "none" | "ambiguous"
    candidates: list[int] = field(default_factory=list)


_BRANCH_ISSUE_RE = re.compile(r"^(\d+)-.+")


def issue_number_from_branch(branch: str | None) -> int | None:
    """Extract the leading issue number from an issue-style branch name."""
    if not branch:
        return None
    match = _BRANCH_ISSUE_RE.match(branch.strip())
    return int(match.group(1)) if match else None


def resolve_focus(current_dir: Path, branch: str | None) -> FocusResolution:
    """Resolve the focus issue using ``/iflow``'s precedence rules.

    1. A branch-derived ``N`` wins outright.
    2. Else exactly one group in ``01-current-issues`` is the focus.
    3. Else no group -> nothing to focus on yet.
    4. Else (multiple groups, no branch) -> ambiguous; the caller must ask.
    """
    branch_n = issue_number_from_branch(branch)
    if branch_n is not None:
        return FocusResolution(number=branch_n, resolved_via="branch")

    groups = group_issue_files(current_dir)
    numbers = sorted(groups)
    if len(numbers) == 1:
        return FocusResolution(number=numbers[0], resolved_via="single-group")
    if not numbers:
        return FocusResolution(number=None, resolved_via="none")
    return FocusResolution(number=None, resolved_via="ambiguous", candidates=numbers)


@dataclass
class SweepMove:
    """A planned (or applied) move of one issue group between folders."""

    number: int
    done: bool
    source: str
    destination: str
    files: list[Path]


def plan_sweep(
    current_dir: Path,
    partly_dir: Path,
    solved_dir: Path,
    except_number: int | None = None,
) -> list[SweepMove]:
    """Plan archive moves for every group in ``current_dir`` except the focus.

    Done groups (a status file with ``- [x] Done``) go to the solved folder;
    everything else goes to the partly-solved folder. The focus issue
    (``except_number``) is never moved.
    """
    moves: list[SweepMove] = []
    for number, group in sorted(group_issue_files(current_dir).items()):
        if except_number is not None and number == except_number:
            continue
        done = group.is_done
        destination = solved_dir if done else partly_dir
        moves.append(
            SweepMove(
                number=number,
                done=done,
                source=current_dir.name,
                destination=destination.name,
                files=list(group.files),
            )
        )
    return moves


def apply_sweep(
    moves: list[SweepMove],
    partly_dir: Path,
    solved_dir: Path,
) -> list[SweepMove]:
    """Execute planned moves, creating destination folders as needed.

    Returns the moves that were actually applied. Destination folders are
    keyed by name so the function stays decoupled from how ``plan_sweep``
    recorded them.
    """
    by_name = {partly_dir.name: partly_dir, solved_dir.name: solved_dir}
    applied: list[SweepMove] = []
    for move in moves:
        dest_dir = by_name.get(move.destination)
        if dest_dir is None:
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        for path in move.files:
            if path.exists():
                path.replace(dest_dir / path.name)
        applied.append(move)
    return applied


@dataclass
class ArchiveMove:
    """A planned (or applied) removal of one solved issue group.

    Archiving (``/iflow-archive``) condenses solved issue groups into a single
    dated summary file and then deletes the original ``issue<N>_*`` files.
    The files stay recoverable through git history, which is why the archive
    workflow records the pre-archive HEAD sha alongside the summaries.
    """

    number: int
    title: str | None
    files: list[Path]


def plan_archive(
    solved_dir: Path, issues: list[int]
) -> tuple[list[ArchiveMove], list[int]]:
    """Plan the removal of the given solved issue groups.

    Returns ``(moves, missing)`` where ``moves`` covers every requested issue
    that has a group in ``solved_dir`` and ``missing`` lists requested numbers
    with no group there. Callers should treat a non-empty ``missing`` as a
    reason to refuse the whole archive rather than silently skipping.
    """
    groups = group_issue_files(solved_dir)
    moves: list[ArchiveMove] = []
    missing: list[int] = []
    for number in sorted(set(issues)):
        group = groups.get(number)
        if group is None:
            missing.append(number)
            continue
        moves.append(
            ArchiveMove(
                number=number,
                title=group.title(),
                files=list(group.files),
            )
        )
    return moves, missing


def apply_archive(moves: list[ArchiveMove]) -> list[Path]:
    """Delete the files of the planned archive moves.

    Returns the paths that were actually removed. Files already gone are
    skipped silently (the plan may be stale).
    """
    removed: list[Path] = []
    for move in moves:
        for path in move.files:
            if path.exists():
                path.unlink()
                removed.append(path)
    return removed
