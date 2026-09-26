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


def test_additive_resolver_keeps_table_rows_anywhere() -> None:
    """Design-guide tables (issue #386): both sides appended rows, not bullets."""
    text = (
        "# Test registry\n"
        "\n"
        "## Registry\n"
        "\n"
        "| Test | Why |\n"
        "|---|---|\n"
        "| test_a | landed |\n"
        "<<<<<<< HEAD\n"
        "| test_b | landed later |\n"
        "=======\n"
        "| test_c | in flight |\n"
        ">>>>>>> 1a2b3c4 (feat: ours)\n"
    )
    result = history.resolve_additive_conflict(text, in_flight_side="theirs")
    assert result.ok, result.reason
    assert result.text is not None
    assert "<<<<<<<" not in result.text
    b = result.text.index("| test_b |")
    c = result.text.index("| test_c |")
    assert b < c


def test_additive_resolver_accepts_bullets_outside_unreleased() -> None:
    """Bullets under any heading resolve; the changelog rule is not required."""
    text = _conflicted(heading="## Decisions")
    strict = history.resolve_changelog_conflict(text, in_flight_side="theirs")
    assert not strict.ok and strict.reason == history.NOT_UNRELEASED_SECTION
    loose = history.resolve_additive_conflict(text, in_flight_side="theirs")
    assert loose.ok, loose.reason
    assert loose.text is not None
    assert loose.text.index(_LANDED) < loose.text.index(_IN_FLIGHT)


def test_additive_resolver_refuses_heading_and_prose() -> None:
    """A duplicated `## Link` section or an edited paragraph stays a human call."""
    with_heading = _conflicted(theirs="## Link\n\nAuto: x.md", heading="## Notes")
    refused = history.resolve_additive_conflict(with_heading, in_flight_side="theirs")
    assert not refused.ok and refused.reason == history.HEADING_CONFLICT

    with_prose = _conflicted(theirs="Plain prose edit.", heading="## Notes")
    refused = history.resolve_additive_conflict(with_prose, in_flight_side="theirs")
    assert not refused.ok and refused.reason == history.NON_BULLET_CONTENT
    assert refused.text is None


@pytest.mark.parametrize("side", ["ours", "theirs"])
def test_refusal_never_returns_text(side: str) -> None:
    result = history.resolve_changelog_conflict(
        _conflicted(theirs="## [0.5.0] - 2026-08-25"), in_flight_side=side
    )
    assert result.text is None


# ---------------------------------------------------------------------------
# writers (issue #288)
# ---------------------------------------------------------------------------


_CLEAN = "# History\n\n## [Unreleased]\n\n## [0.1.0] - 2026-01-01\n\n- First release.\n"

_ONE_UNRELEASED = (
    "# History\n"
    "\n"
    "## [Unreleased]\n"
    "\n"
    "- Already landed. (#1)\n"
    "\n"
    "## [0.1.0] - 2026-01-01\n"
    "\n"
    "- First release.\n"
)


def test_append_unreleased_bullet_adds_last() -> None:
    bullet = "- Newer work. (#2)"
    out = history.append_unreleased_bullet(_ONE_UNRELEASED, bullet)
    lines = out.splitlines()
    assert lines.index("- Already landed. (#1)") < lines.index(bullet)
    assert out.endswith("\n")


def test_append_unreleased_bullet_is_idempotent() -> None:
    first = history.append_unreleased_bullet(_CLEAN, "- One. (#2)")
    again = history.append_unreleased_bullet(first, "- One. (#2)")
    assert first == again
    assert first.count("- One. (#2)") == 1


def test_changelog_has_bullet_normalizes_dash() -> None:
    text = history.append_unreleased_bullet(_CLEAN, "One. (#2)")
    assert history.changelog_has_bullet(text, "- One. (#2)")
    assert history.changelog_has_bullet(text, "One. (#2)")
    assert not history.changelog_has_bullet(text, "- Other. (#3)")


def test_promote_unreleased_opens_empty_section() -> None:
    filled = history.append_unreleased_bullet(_CLEAN, "- Ship it. (#9)")
    out = history.promote_unreleased(filled, "0.2.0", "2026-09-18")
    lines = out.splitlines()
    assert lines.count("## [Unreleased]") == 1
    unreleased = lines.index("## [Unreleased]")
    released = lines.index("## [0.2.0] - 2026-09-18")
    assert unreleased < released
    assert "- Ship it. (#9)" in lines[released:]
    assert "- Ship it. (#9)" not in lines[unreleased + 1 : released]


def test_append_missing_unreleased_raises() -> None:
    with pytest.raises(history.MissingUnreleased):
        history.append_unreleased_bullet(
            "# History\n\n## [0.1.0] - 2026-01-01\n", "- x"
        )


def test_parse_deferred_changelog_reads_bullet_and_version() -> None:
    text = (
        "# Status\n"
        "\n"
        "### Deferred changelog\n"
        "\n"
        "- Prevent HISTORY conflicts. (#288)\n"
        "\n"
        "Planned version: 0.5.0\n"
    )
    deferred = history.parse_deferred_changelog(text)
    assert deferred is not None
    assert not deferred.skipped
    assert deferred.bullet == "- Prevent HISTORY conflicts. (#288)"
    assert deferred.planned_version == "0.5.0"


def test_parse_deferred_changelog_nohistory() -> None:
    text = "### Deferred changelog\n\nnohistory\n"
    deferred = history.parse_deferred_changelog(text)
    assert deferred is not None
    assert deferred.skipped
    assert deferred.bullet is None


def test_parse_deferred_changelog_absent() -> None:
    assert history.parse_deferred_changelog("# Status\n\n- [ ] Done\n") is None
