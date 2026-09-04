"""Tests for issue_flow.history — keep-both changelog conflict resolution.

The resolver is the load-bearing half of issue #240: it decides when a
conflicted changelog is *mechanical* (both sides only appended bullets under
``[Unreleased]``, so keeping both is the only sane answer) and when it is a
real conflict that must stop ``/iflow-close``. These tests pin both halves,
because a resolver that is too eager would silently rewrite someone's release
notes.
"""

from __future__ import annotations

import pytest

from issue_flow import history

_LANDED = "- Fix Batch.drop leaving a ghost cell in the store. (#952)"
_IN_FLIGHT = "- Clearer otherpath error messages. (#961)"


def _conflicted(
    ours: str = _LANDED,
    theirs: str = _IN_FLIGHT,
    heading: str = "## [Unreleased]",
) -> str:
    return (
        "# History\n"
        "\n"
        f"{heading}\n"
        "\n"
        "<<<<<<< HEAD\n"
        f"{ours}\n"
        "=======\n"
        f"{theirs}\n"
        ">>>>>>> 1a2b3c4 (feat: ours)\n"
        "\n"
        "## [0.4.7] - 2026-07-24\n"
        "\n"
        "- Something released earlier. (#900)\n"
    )


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------


def test_parse_conflicts_finds_sides_and_heading() -> None:
    blocks = history.parse_conflicts(_conflicted())
    assert blocks is not None
    assert len(blocks) == 1
    block = blocks[0]
    assert block.ours == [_LANDED]
    assert block.theirs == [_IN_FLIGHT]
    assert block.heading == "## [Unreleased]"


def test_parse_conflicts_empty_for_clean_file() -> None:
    assert history.parse_conflicts("## [Unreleased]\n\n- one bullet.\n") == []


def test_parse_conflicts_rejects_unterminated_markers() -> None:
    """A half-written conflict is not a file this module will rewrite."""
    text = "## [Unreleased]\n<<<<<<< HEAD\n- ours.\n"
    assert history.parse_conflicts(text) is None


# ---------------------------------------------------------------------------
# resolving
# ---------------------------------------------------------------------------


def test_rebase_keeps_both_with_in_flight_bullet_last() -> None:
    """During a rebase the replayed (issue) commit is the `theirs` side."""
    result = history.resolve_changelog_conflict(_conflicted(), in_flight_side="theirs")
    assert result.ok
    assert result.reason == history.RESOLVED
    assert result.text is not None
    lines = result.text.splitlines()
    assert lines.index(_LANDED) < lines.index(_IN_FLIGHT)
    assert not any(line.startswith("<<<<<<<") for line in lines)
    # the untouched parts of the file survive verbatim
    assert "## [0.4.7] - 2026-07-24" in result.text
    assert "- Something released earlier. (#900)" in result.text


def test_merge_keeps_both_with_in_flight_bullet_last() -> None:
    """During a merge the issue branch is `ours`, so the order flips."""
    text = _conflicted(ours=_IN_FLIGHT, theirs=_LANDED)
    result = history.resolve_changelog_conflict(text, in_flight_side="ours")
    assert result.ok
    assert result.text is not None
    lines = result.text.splitlines()
    assert lines.index(_LANDED) < lines.index(_IN_FLIGHT)


def test_identical_bullets_collapse() -> None:
    result = history.resolve_changelog_conflict(
        _conflicted(ours=_LANDED, theirs=_LANDED), in_flight_side="theirs"
    )
    assert result.ok
    assert result.text is not None
    assert result.text.count(_LANDED) == 1


def test_multi_line_bullets_and_several_blocks_resolve() -> None:
    text = (
        "## [Unreleased]\n"
        "\n"
        "<<<<<<< HEAD\n"
        "- Landed one. (#1)\n"
        "=======\n"
        "- Ours one, which wraps\n"
        "  onto a second line. (#2)\n"
        ">>>>>>> abc (ours)\n"
        "\n"
        "<<<<<<< HEAD\n"
        "- Landed two. (#3)\n"
        "=======\n"
        "- Ours two. (#4)\n"
        ">>>>>>> abc (ours)\n"
    )
    result = history.resolve_changelog_conflict(text, in_flight_side="theirs")
    assert result.ok
    assert result.blocks == 2
    assert result.text is not None
    for bullet in ("(#1)", "(#2)", "(#3)", "(#4)"):
        assert bullet in result.text
    assert "  onto a second line. (#2)" in result.text


def test_crlf_and_trailing_newline_preserved() -> None:
    text = _conflicted().replace("\n", "\r\n")
    result = history.resolve_changelog_conflict(text, in_flight_side="theirs")
    assert result.ok
    assert result.text is not None
    assert "\r\n" in result.text
    assert "\n" not in result.text.replace("\r\n", "")
    assert result.text.endswith("\r\n")


# ---------------------------------------------------------------------------
# refusals — everything that is not "two additive bullet lists"
# ---------------------------------------------------------------------------


def test_refuses_conflict_outside_unreleased() -> None:
    """A conflict inside a released section is a real conflict."""
    result = history.resolve_changelog_conflict(
        _conflicted(heading="## [0.4.7] - 2026-07-24"), in_flight_side="theirs"
    )
    assert not result.ok
    assert result.reason == history.NOT_UNRELEASED_SECTION


def test_refuses_promoted_version_heading() -> None:
    """A version promotion rewrites the heading — never auto-resolved."""
    text = _conflicted(theirs="## [0.5.0] - 2026-08-25\n\n- Ours. (#961)")
    result = history.resolve_changelog_conflict(text, in_flight_side="theirs")
    assert not result.ok
    assert result.reason == history.HEADING_CONFLICT


def test_refuses_non_bullet_content() -> None:
    text = _conflicted(theirs="Some rewritten prose paragraph.")
    result = history.resolve_changelog_conflict(text, in_flight_side="theirs")
    assert not result.ok
    assert result.reason == history.NON_BULLET_CONTENT


def test_refuses_when_one_side_is_empty() -> None:
    """An empty side means a deletion, not an addition."""
    text = _conflicted(theirs="")
    result = history.resolve_changelog_conflict(text, in_flight_side="theirs")
    assert not result.ok
    assert result.reason == history.EMPTY_SIDE


def test_refuses_file_without_conflicts() -> None:
    result = history.resolve_changelog_conflict(
        "## [Unreleased]\n\n- one.\n", in_flight_side="theirs"
    )
    assert not result.ok
    assert result.reason == history.NO_CONFLICTS


@pytest.mark.parametrize("side", ["ours", "theirs"])
def test_refusal_never_returns_text(side: str) -> None:
    result = history.resolve_changelog_conflict(
        _conflicted(theirs="## [0.5.0] - 2026-08-25"), in_flight_side=side
    )
    assert result.text is None
