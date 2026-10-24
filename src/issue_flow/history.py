"""Changelog text helpers: keep-both conflict resolution plus append/promote.

The resolver is the load-bearing half of issue #240: it decides when a
conflicted changelog is *mechanical* (both sides only appended bullets under
``[Unreleased]``) and when it is a real conflict that must stop the flow.

Issue #288 adds the *write* half used when ``defer_changelog`` is on:
append a bullet under ``[Unreleased]``, optionally promote that section to a
dated release, and parse the deferred block recorded in ``issue<N>_status.md``.
These writers are pure text in / text out so they can be unit-tested without a
git repo.
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

#: Refusal reasons for ``changelog release``. Success is a written file, not a
#: code in this list.
VERSION_EXISTS = "version_exists"
DIRTY_TREE = "dirty_tree"
NOT_DEFAULT_BRANCH = "not_default_branch"
HEAD_MOVED = "head_moved"
EMPTY_LIST = "empty_list"

_DATED_VERSION_RE = re.compile(
    r"^##\s+\[(?P<version>[^\]]+)\]\s+-\s+(?P<date>\d{4}-\d{2}-\d{2})\s*$"
)
_CHANGELOG_LINE_RE = re.compile(r"^Changelog:\s*(.*?)\s*$")
_CHANGELOG_DATE_LINE_RE = re.compile(r"^Changelog-Date:\s*(\d{4}-\d{2}-\d{2})\s*$")
_CHANGELOG_ID_LINE_RE = re.compile(r"^Changelog-Id:\s*([0-9a-fA-F]{12})\s*$")
_RELEASE_TRAILER_RE = re.compile(r"^Changelog-Release:\s*(\S+)\s*$", re.MULTILINE)
_IDS_COMMENT_RE = re.compile(r"<!--\s*changelog-ids:([^>]*)-->", re.IGNORECASE)

_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
_UNRELEASED_RE = re.compile(r"^\s{0,3}##\s*\[?unreleased\]?", re.IGNORECASE)
_VERSION_HEADING_RE = re.compile(r"^\s{0,3}##\s+\[")
_BULLET_RE = re.compile(r"^\s*[-*+]\s")
_DEFERRED_HEADING_RE = re.compile(r"^###\s+Deferred changelog\s*$", re.IGNORECASE)
_PLANNED_VERSION_RE = re.compile(r"^Planned version:\s*(\S+)\s*$", re.IGNORECASE)


class MissingUnreleased(ValueError):
    """Raised when a writer cannot find ``## [Unreleased]``."""


@dataclass(frozen=True)
class DeferredChangelog:
    """Deferred changelog decision recorded on ``issue<N>_status.md``.

    ``skipped`` is true when the close step chose ``nohistory``. ``bullet`` is
    the list item to append (normalized to start with ``- ``). ``planned_version``
    is set when close bumped or planned a version, so apply-changelog can
    promote ``[Unreleased]``.
    """

    skipped: bool
    bullet: str | None
    planned_version: str | None


def _join_lines(text: str, lines: list[str]) -> str:
    newline = detect_newline(text)
    out = newline.join(lines)
    if text.endswith(("\n", "\r")):
        out += newline
    return out


def normalize_bullet(bullet: str) -> str:
    """Return ``bullet`` as a single ``- …`` list item."""
    text = bullet.strip()
    if text.startswith(("- ", "* ", "+ ")):
        return f"- {text[2:].strip()}"
    if text.startswith(("-", "*", "+")):
        return f"- {text[1:].strip()}"
    return f"- {text}"


def changelog_has_bullet(text: str, bullet: str) -> bool:
    """True when ``bullet`` is already present as a list item (whitespace-folded)."""
    needle = normalize_bullet(bullet)
    for line in text.splitlines():
        if line.strip() == needle:
            return True
        if _BULLET_RE.match(line) and normalize_bullet(line) == needle:
            return True
    return False


def _unreleased_span(lines: list[str]) -> tuple[int, int]:
    start: int | None = None
    for i, line in enumerate(lines):
        if _UNRELEASED_RE.match(line):
            start = i
            break
    if start is None:
        raise MissingUnreleased("no ## [Unreleased] heading")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _VERSION_HEADING_RE.match(lines[j]) and not _UNRELEASED_RE.match(lines[j]):
            end = j
            break
    return start, end


def append_unreleased_bullet(text: str, bullet: str) -> str:
    """Append ``bullet`` at the end of ``## [Unreleased]`` (idempotent)."""
    item = normalize_bullet(bullet)
    if changelog_has_bullet(text, item):
        return text
    lines = text.splitlines()
    start, end = _unreleased_span(lines)
    section = lines[start:end]
    while section and section[-1].strip() == "":
        section.pop()
    if len(section) == 1:
        section.append("")
    section.append(item)
    out = lines[:start] + section
    if end < len(lines):
        out.append("")
        out.extend(lines[end:])
    return _join_lines(text, out)


def promote_unreleased(text: str, version: str, date: str) -> str:
    """Rename ``[Unreleased]`` to ``[version] - date`` and open an empty one above.

    Existing bullets stay in the new dated section. Does not add a bullet —
    call :func:`append_unreleased_bullet` first when applying a deferred one.
    """
    version = version.strip()
    if version.startswith("v") and version[1:2].isdigit():
        version = version[1:]
    lines = text.splitlines()
    start, end = _unreleased_span(lines)
    body = lines[start + 1 : end]
    while body and body[0].strip() == "":
        body.pop(0)
    while body and body[-1].strip() == "":
        body.pop()
    rebuilt = [
        "## [Unreleased]",
        "",
        f"## [{version}] - {date}",
    ]
    if body:
        rebuilt.append("")
        rebuilt.extend(body)
    out = lines[:start] + rebuilt
    if end < len(lines):
        out.append("")
        out.extend(lines[end:])
    return _join_lines(text, out)


def parse_deferred_changelog(status_text: str) -> DeferredChangelog | None:
    """Read the ``### Deferred changelog`` block from a status file.

    Returns ``None`` when the heading is absent. A ``nohistory`` token means
    the close step explicitly skipped the bullet.
    """
    lines = status_text.splitlines()
    start: int | None = None
    for i, line in enumerate(lines):
        if _DEFERRED_HEADING_RE.match(line):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("##"):
            end = j
            break
    bullet: str | None = None
    planned: str | None = None
    skipped = False
    for line in lines[start + 1 : end]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower() == "nohistory":
            skipped = True
            continue
        planned_match = _PLANNED_VERSION_RE.match(stripped)
        if planned_match:
            planned = planned_match.group(1)
            continue
        if _BULLET_RE.match(line) and bullet is None:
            bullet = normalize_bullet(line)
    if skipped:
        return DeferredChangelog(skipped=True, bullet=None, planned_version=None)
    if bullet is None:
        return DeferredChangelog(skipped=False, bullet=None, planned_version=planned)
    return DeferredChangelog(skipped=False, bullet=bullet, planned_version=planned)


@dataclass(frozen=True)
class ChangelogNote:
    """One unreleased changelog bullet recovered from commit trailers.

    ``text`` is the sentence without a leading list marker. ``note_date`` is
    the ``Changelog-Date`` value (a sort key inside the release, not a filing
    date). ``order`` is the winning commit's position in the scan window,
    oldest first, so equal dates stay in commit order.
    """

    text: str
    note_date: str
    note_id: str
    order: int = 0


def normalize_version(version: str) -> str:
    """Strip a single leading ``v`` when the next character is a digit."""
    text = version.strip()
    if text.startswith("v") and len(text) > 1 and text[1].isdigit():
        return text[1:]
    return text


def parse_message_notes(message: str) -> list[ChangelogNote]:
    """Pull changelog triples out of a full commit message.

    A triple is ``Changelog`` / ``Changelog-Date`` / ``Changelog-Id``, in that
    order, anywhere in the body — squash commits embed several trailer blocks,
    so this does not stop at the last ``git interpret-trailers`` block. An
    incomplete triple is dropped. The same id later in the same message
    replaces the earlier text (one bullet per id).
    """
    pending_text: str | None = None
    pending_date: str | None = None
    found: list[ChangelogNote] = []
    for raw in message.splitlines():
        line = raw.strip()
        id_match = _CHANGELOG_ID_LINE_RE.match(line)
        if id_match and pending_text is not None and pending_date is not None:
            found.append(
                ChangelogNote(
                    text=pending_text,
                    note_date=pending_date,
                    note_id=id_match.group(1).lower(),
                )
            )
            pending_text = None
            pending_date = None
            continue
        date_match = _CHANGELOG_DATE_LINE_RE.match(line)
        if date_match and pending_text is not None:
            pending_date = date_match.group(1)
            continue
        text_match = _CHANGELOG_LINE_RE.match(line)
        if text_match:
            pending_text = text_match.group(1).strip()
            pending_date = None
    return _collapse_notes(found)


def _collapse_notes(notes: list[ChangelogNote]) -> list[ChangelogNote]:
    """Keep the last note for each id, in the order those last occurrences appear."""
    last_at: dict[str, int] = {}
    for index, note in enumerate(notes):
        last_at[note.note_id] = index
    return [notes[index] for index in sorted(last_at.values())]


def merge_commit_notes(per_commit: list[list[ChangelogNote]]) -> list[ChangelogNote]:
    """Merge per-commit note lists (oldest commit first).

    A later commit with the same id replaces the text and the date. The result
    is sorted by ``Changelog-Date``, then by commit order.
    """
    winners: dict[str, ChangelogNote] = {}
    for commit_index, notes in enumerate(per_commit):
        for note in notes:
            winners[note.note_id] = ChangelogNote(
                text=note.text,
                note_date=note.note_date,
                note_id=note.note_id,
                order=commit_index,
            )
    ordered = sorted(winners.values(), key=lambda note: (note.note_date, note.order))
    return ordered


def message_is_release(message: str) -> bool:
    """True when ``message`` carries a ``Changelog-Release:`` trailer."""
    return _RELEASE_TRAILER_RE.search(message) is not None


def recorded_changelog_ids(text: str) -> set[str]:
    """Ids named in ``<!-- changelog-ids: ... -->`` comments."""
    found: set[str] = set()
    for match in _IDS_COMMENT_RE.finditer(text):
        for token in match.group(1).split():
            if re.fullmatch(r"[0-9a-fA-F]{12}", token):
                found.add(token.lower())
    return found


def top_version_heading(text: str) -> str | None:
    """First dated ``## [version] - YYYY-MM-DD`` line, skipping ``[Unreleased]``."""
    for line in text.splitlines():
        stripped = line.strip()
        if _UNRELEASED_RE.match(stripped):
            continue
        if _DATED_VERSION_RE.match(stripped):
            return stripped
    return None


def has_version_heading(text: str, version: str) -> bool:
    """True when ``## [version]`` already exists (with or without a date)."""
    want = normalize_version(version)
    pattern = re.compile(rf"^##\s+\[{re.escape(want)}\](?:\s|$)")
    for line in text.splitlines():
        if pattern.match(line.strip()):
            return True
    return False


def unreleased_bullet_lines(text: str) -> list[str]:
    """Normalized bullets under ``## [Unreleased]``, or ``[]`` when it is absent."""
    lines = text.splitlines()
    try:
        start, end = _unreleased_span(lines)
    except MissingUnreleased:
        return []
    bullets: list[str] = []
    for line in lines[start + 1 : end]:
        if _BULLET_RE.match(line):
            bullets.append(normalize_bullet(line))
    return bullets


def render_release_section(
    version: str,
    date: str,
    legacy_bullets: list[str],
    notes: list[ChangelogNote],
) -> str:
    """One new version section. Does not include older sections.

    Legacy ``[Unreleased]`` bullets come first, then trailer notes. Shipped
    ids are stored in an HTML comment so a later list can skip them even if
    the scan window is wrong.
    """
    version = normalize_version(version)
    lines = [f"## [{version}] - {date}", ""]
    if notes:
        ids = " ".join(note.note_id for note in notes)
        lines.append(f"<!-- changelog-ids: {ids} -->")
        lines.append("")
    for bullet in legacy_bullets:
        lines.append(normalize_bullet(bullet))
    for note in notes:
        lines.append(normalize_bullet(note.text))
    return "\n".join(lines)


def apply_release(text: str, section: str) -> str:
    """Prepend ``section`` and delete ``## [Unreleased]`` when it is present.

    Older dated sections are left byte-for-byte apart from the blank line that
    separates them from the new section.
    """
    lines = text.splitlines()
    try:
        start, end = _unreleased_span(lines)
    except MissingUnreleased:
        start = None
        end = None
    if start is not None and end is not None:
        lines = lines[:start] + lines[end:]
        insert_at = start
    else:
        insert_at = len(lines)
        for index, line in enumerate(lines):
            if _VERSION_HEADING_RE.match(line):
                insert_at = index
                break
    while insert_at > 0 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
        lines.pop(insert_at)
    section_lines = section.splitlines()
    rest = lines[insert_at:]
    while rest and rest[0].strip() == "":
        rest.pop(0)
    out = lines[:insert_at]
    if out and out[-1].strip():
        out.append("")
    out.extend(section_lines)
    if rest:
        out.append("")
        out.extend(rest)
    return _join_lines(text if text.endswith(("\n", "\r")) else text + "\n", out)


def release_is_empty(legacy_bullets: list[str], notes: list[ChangelogNote]) -> bool:
    """True when a release would write a heading with no bullets."""
    return not legacy_bullets and not notes


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


_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")


def _is_additive_line(line: str) -> bool:
    """True for a list item, a markdown table row, a continuation, or a blank.

    This is the widened predicate behind :func:`resolve_additive_conflict`
    (issue #386): design guides and the test registry append **table rows**
    as well as bullets, and both are pure bookkeeping. Headings, prose, and
    code fences stay real content and refuse the resolve.
    """
    if _is_bullet_or_blank(line):
        return True
    return bool(_TABLE_ROW_RE.match(line))


def resolve_additive_conflict(
    text: str,
    *,
    in_flight_side: Side,
) -> ResolveResult:
    """Resolve a conflict whose every side only *appends* bullets or table rows.

    Same keep-both rule as :func:`resolve_changelog_conflict` — landed lines
    first, the in-flight side last, byte-identical lines collapse — but with
    two differences: the block may sit **anywhere** in the file (not only under
    ``[Unreleased]``) and markdown **table rows** count as additive content.

    Intended for files whose whole content is bookkeeping: design guides under
    ``04-designs-and-guides/`` (registry tables, appended bullets) and
    ``issue<N>_status.md``. A side containing a heading, prose, or a code
    fence refuses — a duplicated ``## Link`` section or an edited paragraph is
    a human decision (issue #386).
    """
    blocks = parse_conflicts(text)
    if blocks is None:
        return ResolveResult(None, UNTERMINATED_CONFLICT, 0)
    if not blocks:
        return ResolveResult(None, NO_CONFLICTS, 0)

    count = len(blocks)
    for block in blocks:
        for side in (block.ours, block.theirs):
            if any(_HEADING_RE.match(line) for line in side):
                return ResolveResult(None, HEADING_CONFLICT, count)
            if not all(_is_additive_line(line) for line in side):
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
