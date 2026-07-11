"""Deterministic issue-queue planning for the cycling workflow.

Backs ``issue-flow agent queue``: given a set of issues (explicit numbers, a
label, or an epic stage), parse their ``Depends on #N`` / ``Blocked by #N``
lines, order the queue topologically, and flag blocked and independent
members — the mechanical groundwork ``/iflow-cycle`` confirms and executes.
Read-only computation throughout; dependency cycles are reported, never
silently broken.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_DEP_MARKER_RE = re.compile(r"\b(?:depends on|blocked by)\b", re.IGNORECASE)
_REF_RE = re.compile(r"#(\d+)")


def parse_dependencies(body: str) -> list[int]:
    """Issue numbers referenced on dependency-marker lines of a body.

    Only lines containing ``depends on`` / ``blocked by`` count, so ordinary
    prose references (``see #12``) never create accidental edges.
    """
    deps: list[int] = []
    for line in body.splitlines():
        if _DEP_MARKER_RE.search(line):
            for ref in _REF_RE.findall(line):
                number = int(ref)
                if number not in deps:
                    deps.append(number)
    return deps


@dataclass
class QueueItem:
    """One issue considered for the queue."""

    number: int
    title: str
    state: str  # "open" | "closed" | "unknown"
    yolo: bool = False
    depends_on: list[int] = field(default_factory=list)


@dataclass
class QueuePlan:
    """The computed queue: execution order plus everything set aside."""

    ordered: list[QueueItem] = field(default_factory=list)
    blocked: list[tuple[QueueItem, list[int]]] = field(default_factory=list)
    skipped_closed: list[QueueItem] = field(default_factory=list)
    independent: list[int] = field(default_factory=list)
    cycle: list[int] | None = None


def build_queue(items: list[QueueItem]) -> QueuePlan:
    """Order ``items`` for sequential hands-off execution.

    Rules:

    - closed items are skipped (their number still satisfies dependencies);
    - an item with an **open dependency outside the queue** is blocked —
      the cycle cannot unblock it, so it is set aside with the blockers named;
    - remaining items are Kahn-toposorted over in-queue dependency edges,
      ties broken by issue number for determinism;
    - a dependency cycle aborts the plan (``cycle`` names the members);
    - ``independent`` lists members with **no dependency relation in either
      direction** to any other queue member — the safe candidates for a
      future parallel dispatch.
    """
    plan = QueuePlan()
    closed = {item.number for item in items if item.state == "closed"}
    members = {item.number: item for item in items if item.state != "closed"}
    plan.skipped_closed = [item for item in items if item.state == "closed"]

    # Split off items blocked by open dependencies outside the queue.
    runnable: dict[int, QueueItem] = {}
    for number, item in members.items():
        external_open = [
            dep for dep in item.depends_on if dep not in closed and dep not in members
        ]
        if external_open:
            plan.blocked.append((item, external_open))
        else:
            runnable[number] = item
    plan.blocked.sort(key=lambda pair: pair[0].number)

    # Kahn toposort over in-queue edges (dep -> dependant), among runnables.
    indegree: dict[int, int] = {number: 0 for number in runnable}
    dependants: dict[int, list[int]] = {number: [] for number in runnable}
    for number, item in runnable.items():
        for dep in item.depends_on:
            if dep in runnable:
                indegree[number] += 1
                dependants[dep].append(number)

    ready = sorted(number for number, degree in indegree.items() if degree == 0)
    while ready:
        number = ready.pop(0)
        plan.ordered.append(runnable[number])
        for dependant in dependants[number]:
            indegree[dependant] -= 1
            if indegree[dependant] == 0:
                # Keep determinism: insert in numeric order.
                ready.append(dependant)
                ready.sort()

    if len(plan.ordered) != len(runnable):
        placed = {item.number for item in plan.ordered}
        plan.cycle = sorted(number for number in runnable if number not in placed)
        plan.ordered = []
        return plan

    # Independence: no dependency relation (either direction) with any other
    # member — computed over all non-closed members, including blocked ones,
    # since a blocked relative still makes parallel dispatch unsafe.
    related: set[int] = set()
    for number, item in members.items():
        for dep in item.depends_on:
            if dep in members:
                related.add(number)
                related.add(dep)
    plan.independent = sorted(number for number in members if number not in related)
    return plan
