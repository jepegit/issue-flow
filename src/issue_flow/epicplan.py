"""Parser for staged epic plan files (``epic<N>_plan.md``).

The ``/iflow-epic`` skill drafts a plan whose structure is a deliberate
machine-readable contract (stages, ``### Issue:`` specs, ``Depends on:`` /
``yolo:`` / ``Published: #<M>`` lines). This module encodes that contract
once, so ``issue-flow agent epic-status`` (and later ``agent queue``) can
give deterministic answers instead of every agent re-parsing markdown by
hand. Read-only: nothing here writes files or talks to GitHub.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_TITLE_RE = re.compile(r"^#\s+Epic\s+#(\d+):\s*(.*)$")
_STATUS_RE = re.compile(r"^Status:\s*(\w+)\s*$", re.IGNORECASE)
# "## Stage 1 — title" (em dash, hyphen, or colon separators all accepted).
_STAGE_RE = re.compile(r"^##\s+Stage\s+(\d+)\s*(?:[—:-]\s*)?(.*)$")
_LATER_RE = re.compile(r"^##\s+Later\b")
_ISSUE_RE = re.compile(r"^###\s+Issue:\s*(.*)$")
_PUBLISHED_RE = re.compile(r"^-\s*Published:\s*#(\d+)\s*$")
_DEPENDS_RE = re.compile(r"^-\s*Depends on:\s*(.*)$")
_YOLO_RE = re.compile(r"^-\s*yolo:\s*(yes|no)\b", re.IGNORECASE)
_DEP_NUMBER_RE = re.compile(r"#(\d+)")
_DEP_PLACEHOLDER_RE = re.compile(r"stage\s+(\d+)\s+issue\s+(\d+)", re.IGNORECASE)


@dataclass
class IssueSpec:
    """One ``### Issue:`` block inside a stage."""

    title: str
    stage: int
    index: int  # 1-based position within the stage
    published: int | None = None
    depends_on: list[int] = field(default_factory=list)
    placeholder_deps: list[tuple[int, int]] = field(default_factory=list)
    yolo: bool = False


@dataclass
class Stage:
    index: int
    title: str
    issues: list[IssueSpec] = field(default_factory=list)


@dataclass
class EpicPlan:
    number: int | None
    title: str
    status: str  # "draft" | "confirmed" | anything else found
    stages: list[Stage] = field(default_factory=list)

    def resolve_placeholders(self) -> None:
        """Fold ``stage <j> issue <k>`` placeholders into ``depends_on``
        wherever the referenced spec has been published."""
        by_position = {
            (spec.stage, spec.index): spec
            for stage in self.stages
            for spec in stage.issues
        }
        for stage in self.stages:
            for spec in stage.issues:
                remaining: list[tuple[int, int]] = []
                for position in spec.placeholder_deps:
                    target = by_position.get(position)
                    if target is not None and target.published is not None:
                        if target.published not in spec.depends_on:
                            spec.depends_on.append(target.published)
                    else:
                        remaining.append(position)
                spec.placeholder_deps = remaining


def parse_epic_plan(path: Path) -> EpicPlan | None:
    """Parse an epic plan file, or ``None`` when unreadable.

    Lenient by design: unknown lines are ignored, so hand-edited prose never
    breaks parsing — only the marker lines above carry meaning.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    plan = EpicPlan(number=None, title="", status="draft")
    current_stage: Stage | None = None
    current_issue: IssueSpec | None = None
    in_later = False

    for line in text.splitlines():
        stripped = line.strip()

        title_match = _TITLE_RE.match(stripped)
        if title_match:
            plan.number = int(title_match.group(1))
            plan.title = title_match.group(2).strip()
            continue

        status_match = _STATUS_RE.match(stripped)
        if status_match:
            plan.status = status_match.group(1).lower()
            continue

        if _LATER_RE.match(stripped):
            in_later = True
            current_stage = None
            current_issue = None
            continue

        stage_match = _STAGE_RE.match(stripped)
        if stage_match:
            in_later = False
            current_stage = Stage(
                index=int(stage_match.group(1)),
                title=stage_match.group(2).strip(),
            )
            plan.stages.append(current_stage)
            current_issue = None
            continue

        if in_later or current_stage is None:
            continue

        issue_match = _ISSUE_RE.match(stripped)
        if issue_match:
            current_issue = IssueSpec(
                title=issue_match.group(1).strip(),
                stage=current_stage.index,
                index=len(current_stage.issues) + 1,
            )
            current_stage.issues.append(current_issue)
            continue

        if current_issue is None:
            continue

        published_match = _PUBLISHED_RE.match(stripped)
        if published_match:
            current_issue.published = int(published_match.group(1))
            continue

        depends_match = _DEPENDS_RE.match(stripped)
        if depends_match:
            payload = depends_match.group(1)
            current_issue.depends_on = [
                int(number) for number in _DEP_NUMBER_RE.findall(payload)
            ]
            current_issue.placeholder_deps = [
                (int(j), int(k)) for j, k in _DEP_PLACEHOLDER_RE.findall(payload)
            ]
            continue

        yolo_match = _YOLO_RE.match(stripped)
        if yolo_match:
            current_issue.yolo = yolo_match.group(1).lower() == "yes"
            continue

    plan.resolve_placeholders()
    return plan
