"""Deterministic keep-both resolution for changelog merge conflicts.

When an unrelated PR lands on the default branch while one issue is in flight,
the two branches often add a bullet to the *same* ``## [Unreleased]`` section of
the changelog. Git cannot merge that, so the PR goes ``CONFLICTING`` /
``DIRTY`` and — before issue #240 — ``/iflow-cycle`` treated the refused merge
as a stop even though there is no semantic merge to invent: both sides only
appended list items.

This module owns that one mechanical resolution, as pure text in / text out so
it can be unit-tested without a git repo. It is deliberately **narrow**:
anything that is not "both sides only add bullets under the same
``[Unreleased]`` heading" is refused with a reason, and the caller
(``issue-flow agent sync-branch``) aborts the rebase and stops. Edited existing
bullets, renamed headings, and promoted version sections are all real conflicts
that a human (or the agent) must look at.

Ordering rule: the bullets already on the default branch keep their positions
and the in-flight issue's bullets are appended **last** — the same append
semantics as the ``iflow-history-update`` skill's mode A, so a resolved conflict
is indistinguishable from having written the bullet after the other one landed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

CONFLICT_START = "<<<<<<<"
CONFLICT_SEP = "======="
CONFLICT_END = ">>>>>>>"

Side = Literal["ours", "theirs"]

#: Refusal reasons, in the order they are checked. ``resolved`` is the only
#: success value.
RESOLVED = "resolved"
NO_CONFLICTS = "no_conflicts"
UNTERMINATED_CONFLICT = "unterminated_conflict"
NOT_UNRELEASED_SECTION = "not_unreleased_section"
HEADING_CONFLICT = "heading_conflict"
NON_BULLET_CONTENT = "non_bullet_content"
EMPTY_SIDE = "empty_side"

_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
_UNRELEASED_RE = re.compile(r"^\s{0,3}##\s*\[?unreleased\]?", re.IGNORECASE)
_BULLET_RE = re.compile(r"^\s*[-*+]\s")


@dataclass(frozen=True)
class ConflictBlock:
    """One ``<<<<<<< / ======= / >>>>>>>`` region of a conflicted file.

    ``start`` / ``sep`` / ``end`` are line indices of the marker lines
    themselves; ``ours`` / ``theirs`` are the lines between them (markers
    excluded). ``heading`` is the nearest ``#``-heading above the block, which
    is what decides whether the block sits in the ``[Unreleased]`` section.
    """

    start: int
    sep: int
    end: int
    ours: list[str]
    theirs: list[str]
    heading: str | None


@dataclass(frozen=True)
class ResolveResult:
    """Outcome of :func:`resolve_changelog_conflict`.

    ``text`` is the resolved file content on success and ``None`` on refusal;
    ``reason`` is :data:`RESOLVED` or one of the refusal codes; ``blocks`` is
    how many conflict regions were seen (0 when the file is not conflicted).
    """

    text: str | None
    reason: str
    blocks: int

    @property
    def ok(self) -> bool:
        return self.text is not None


def detect_newline(text: str) -> str:
    """Dominant line ending of ``text`` (``\\r\\n`` only when it is used)."""
    return "\r\n" if "\r\n" in text else "\n"


def parse_conflicts(text: str) -> list[ConflictBlock] | None:
    """Split ``text`` into its conflict regions.

    Returns an empty list for a file with no conflict markers, and ``None``
    when the markers are malformed (an unterminated or nested region) — that is
    not a file this module is willing to rewrite.
    """
    lines = text.splitlines()
    blocks: list[ConflictBlock] = []
    index = 0
    while index < len(lines):
        if not lines[index].startswith(CONFLICT_START):
            index += 1
            continue

        start = index
        sep = -1
        end = -1
        for cursor in range(start + 1, len(lines)):
            line = lines[cursor]
            if line.startswith(CONFLICT_START):
                return None  # nested start: refuse to guess
            if line.startswith(CONFLICT_SEP) and sep == -1:
                sep = cursor
                continue
            if line.startswith(CONFLICT_END):
                end = cursor
                break
        if sep == -1 or end == -1:
            return None

        blocks.append(
            ConflictBlock(
                start=start,
                sep=sep,
                end=end,
                ours=lines[start + 1 : sep],
                theirs=lines[sep + 1 : end],
                heading=_preceding_heading(lines, start),
            )
        )
        index = end + 1

    return blocks


def _preceding_heading(lines: list[str], start: int) -> str | None:
    """Nearest markdown heading above line ``start``, if any."""
    for cursor in range(start - 1, -1, -1):
        if _HEADING_RE.match(lines[cursor]):
            return lines[cursor]
    return None


def _is_bullet_or_blank(line: str) -> bool:
    """True for a list item, a wrapped continuation line, or a blank line.

    A continuation line is indented and non-empty (e.g. the second line of a
    long bullet). Anything flush-left that is not a bullet — prose, a heading,
    a code fence — is treated as real content and refuses the resolve.
    """
    if not line.strip():
        return True
    if _HEADING_RE.match(line):
        return False
    if _BULLET_RE.match(line):
        return True
    return line[:1].isspace()


def _trim_blank_edges(lines: list[str]) -> list[str]:
    """Drop leading/trailing blank lines, preserving interior ones."""
    first = 0
    last = len(lines)
    while first < last and not lines[first].strip():
        first += 1
    while last > first and not lines[last - 1].strip():
        last -= 1
    return lines[first:last]


def _merge_sides(landed: list[str], in_flight: list[str]) -> list[str]:
    """Keep both sides: landed bullets first, in-flight bullets appended last.

    Byte-identical bullets (ignoring surrounding whitespace) collapse to one so
    a bullet that somehow exists on both sides is not duplicated.
    """
    merged: list[str] = []
    seen: set[str] = set()
    for line in _trim_blank_edges(landed) + _trim_blank_edges(in_flight):
        key = line.strip()
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        merged.append(line)
    return merged


def resolve_changelog_conflict(
    text: str,
    *,
    in_flight_side: Side,
) -> ResolveResult:
    """Resolve an additive ``[Unreleased]`` conflict by keeping both sides.

    ``in_flight_side`` says which conflict side belongs to the issue being
    landed: during a **rebase** the replayed commit is ``theirs`` (``HEAD`` is
    the upstream being replayed onto), during a **merge** it is ``ours``.
    Getting this right is what makes the bullet order deterministic.

    Every conflict region must sit under the ``## [Unreleased]`` heading and
    contain only list items (or blank / continuation lines) on both sides.
    Otherwise nothing is rewritten and the refusal reason is returned.
    """
    blocks = parse_conflicts(text)
    if blocks is None:
        return ResolveResult(None, UNTERMINATED_CONFLICT, 0)
    if not blocks:
        return ResolveResult(None, NO_CONFLICTS, 0)

    count = len(blocks)
    for block in blocks:
        if block.heading is None or not _UNRELEASED_RE.match(block.heading):
            return ResolveResult(None, NOT_UNRELEASED_SECTION, count)
        for side in (block.ours, block.theirs):
            if any(_HEADING_RE.match(line) for line in side):
                return ResolveResult(None, HEADING_CONFLICT, count)
            if not all(_is_bullet_or_blank(line) for line in side):
                return ResolveResult(None, NON_BULLET_CONTENT, count)
        if not _trim_blank_edges(block.ours) or not _trim_blank_edges(block.theirs):
            return ResolveResult(None, EMPTY_SIDE, count)

    lines = text.splitlines()
    out: list[str] = []
    cursor = 0
    for block in blocks:
        out.extend(lines[cursor : block.start])
        landed = block.theirs if in_flight_side == "ours" else block.ours
        in_flight = block.ours if in_flight_side == "ours" else block.theirs
        out.extend(_merge_sides(landed, in_flight))
        cursor = block.end + 1
    out.extend(lines[cursor:])

    newline = detect_newline(text)
    resolved = newline.join(out)
    if text.endswith(("\n", "\r")):
        resolved += newline
    return ResolveResult(resolved, RESOLVED, count)
