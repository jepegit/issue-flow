"""Tests for issue_flow.queueplan — dependency parsing and queue building."""

from __future__ import annotations

from issue_flow.queueplan import QueueItem, build_queue, parse_dependencies

# ---------------------------------------------------------------------------
# dependency parsing
# ---------------------------------------------------------------------------


def test_parse_dependencies_marker_lines_only() -> None:
    body = (
        "Some context referencing #1 in prose.\n"
        "Depends on #140 and #141.\n"
        "More prose about #99.\n"
        "Blocked by #7\n"
    )
    assert parse_dependencies(body) == [140, 141, 7]


def test_parse_dependencies_dedupes_and_handles_none() -> None:
    assert parse_dependencies("Depends on #5, #5 and #6") == [5, 6]
    assert parse_dependencies("Depends on: none") == []
    assert parse_dependencies("no markers at all #4") == []


# ---------------------------------------------------------------------------
# queue building
# ---------------------------------------------------------------------------


def _item(
    number: int,
    *,
    state: str = "open",
    deps: list[int] | None = None,
    yolo: bool = False,
) -> QueueItem:
    return QueueItem(
        number=number,
        title=f"Issue {number}",
        state=state,
        yolo=yolo,
        depends_on=deps or [],
    )


def test_build_queue_topological_order() -> None:
    plan = build_queue(
        [
            _item(3, deps=[1, 2]),
            _item(1),
            _item(2, deps=[1]),
        ]
    )
    assert [item.number for item in plan.ordered] == [1, 2, 3]
    assert plan.cycle is None
    assert plan.blocked == []


def test_build_queue_skips_closed_and_satisfies_deps_through_them() -> None:
    plan = build_queue(
        [
            _item(1, state="closed"),
            _item(2, deps=[1]),
        ]
    )
    assert [item.number for item in plan.ordered] == [2]
    assert [item.number for item in plan.skipped_closed] == [1]


def test_build_queue_blocks_on_open_external_dependency() -> None:
    plan = build_queue([_item(2, deps=[99])])
    assert plan.ordered == []
    assert len(plan.blocked) == 1
    item, deps = plan.blocked[0]
    assert item.number == 2
    assert deps == [99]


def test_build_queue_reports_cycle() -> None:
    plan = build_queue(
        [
            _item(1, deps=[2]),
            _item(2, deps=[1]),
            _item(3),
        ]
    )
    assert plan.cycle == [1, 2]
    assert plan.ordered == []


def test_build_queue_independent_members() -> None:
    plan = build_queue(
        [
            _item(1),
            _item(2, deps=[1]),
            _item(5),
            _item(9),
        ]
    )
    # 1 and 2 are related; 5 and 9 have no relation to anyone.
    assert plan.independent == [5, 9]


def test_build_queue_deterministic_tiebreak_by_number() -> None:
    plan = build_queue([_item(9), _item(2), _item(5)])
    assert [item.number for item in plan.ordered] == [2, 5, 9]
