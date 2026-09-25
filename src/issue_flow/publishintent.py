"""Parse publish-on-success GitHub labels into a bump / release intent.

Backs ``issue-flow agent publish-intent`` (issue #308): a configurable
base label (default ``publish``) optionally carries a colon payload
(``publish:minor``, ``publish:0.6.0``). Bare label → patch. Explicit
versions are checked against single-level bumps from the current version
so agents can stop-and-ask when the number is not a sensible next release.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from issue_flow import versionplan
from issue_flow.versionplan import LEVELS, Version, parse_version


@dataclass(frozen=True)
class PublishMatch:
    """One label that matched the configured publish base."""

    raw: str
    kind: str  # "bare" | "level" | "version"
    level: str | None = None
    target_version: str | None = None  # without leading v


@dataclass(frozen=True)
class PublishIntent:
    """Resolved publish intent for an issue (or label list)."""

    matched: bool
    publish_label: str
    kind: str | None  # None | "level" | "version"
    level: str | None
    target_version: str | None
    label: str | None
    logical: bool | None
    suggestion: str | None
    planned_from_level: str | None
    notes: tuple[str, ...]
    conflict: bool = False


def _norm(text: str) -> str:
    return text.strip().lower()


def match_publish_labels(
    labels: Iterable[str], publish_label: str
) -> list[PublishMatch]:
    """Return every label that matches ``publish_label`` or ``publish_label:…``."""
    base = _norm(publish_label)
    if not base:
        return []
    out: list[PublishMatch] = []
    for raw in labels:
        name = _norm(str(raw))
        if not name:
            continue
        if name == base:
            out.append(PublishMatch(raw=str(raw).strip(), kind="bare", level="patch"))
            continue
        prefix = base + ":"
        if not name.startswith(prefix):
            continue
        payload = name[len(prefix) :].strip()
        if not payload:
            out.append(PublishMatch(raw=str(raw).strip(), kind="bare", level="patch"))
            continue
        if payload in LEVELS:
            out.append(PublishMatch(raw=str(raw).strip(), kind="level", level=payload))
            continue
        parsed = parse_version(payload)
        if parsed is not None:
            out.append(
                PublishMatch(
                    raw=str(raw).strip(),
                    kind="version",
                    target_version=parsed.formatted().lstrip("v"),
                )
            )
            continue
        # Unrecognised payload — still a match, but caller must ask.
        out.append(PublishMatch(raw=str(raw).strip(), kind="bare", level=None))
    return out


def _specificity(match: PublishMatch) -> int:
    if match.kind == "version":
        return 3
    if match.kind == "level":
        return 2
    return 1


def _single_level_targets(current: Version) -> dict[str, str]:
    """Map each single bump level to its planned version string (no v)."""
    targets: dict[str, str] = {}
    for level in ("major", "minor", "patch", "stable", "alpha", "beta", "rc", "post"):
        planned, _notes = versionplan.bump(current, [level])
        if planned is None:
            continue
        targets[level] = planned.formatted().lstrip("v")
    return targets


def resolve_publish_intent(
    labels: Iterable[str],
    publish_label: str,
    *,
    current_version: str | None,
) -> PublishIntent:
    """Pick the winning publish match and judge explicit versions.

    Precedence among matches: explicit version > level > bare. Two matches
    at the same specificity with different payloads → ``conflict=True`` and
    ``matched=True`` so the agent stops and asks.
    """
    matches = match_publish_labels(labels, publish_label)
    if not matches:
        return PublishIntent(
            matched=False,
            publish_label=publish_label,
            kind=None,
            level=None,
            target_version=None,
            label=None,
            logical=None,
            suggestion=None,
            planned_from_level=None,
            notes=(),
        )

    bad = [m for m in matches if m.kind == "bare" and m.level is None]
    good = [m for m in matches if not (m.kind == "bare" and m.level is None)]
    notes: list[str] = []
    for m in bad:
        notes.append(f"unrecognised publish payload on label '{m.raw}'")

    if not good and bad:
        return PublishIntent(
            matched=True,
            publish_label=publish_label,
            kind=None,
            level=None,
            target_version=None,
            label=bad[0].raw,
            logical=False,
            suggestion="patch",
            planned_from_level=None,
            notes=tuple(notes),
            conflict=True,
        )

    by_spec: dict[int, list[PublishMatch]] = {}
    for m in good:
        by_spec.setdefault(_specificity(m), []).append(m)
    top = max(by_spec)
    winners = by_spec[top]

    def _key(m: PublishMatch) -> tuple[str, str]:
        return (m.kind, m.level or m.target_version or "")

    unique = {_key(m): m for m in winners}
    if len(unique) > 1:
        notes.append(
            "conflicting publish labels: " + ", ".join(sorted({m.raw for m in winners}))
        )
        return PublishIntent(
            matched=True,
            publish_label=publish_label,
            kind=None,
            level=None,
            target_version=None,
            label=winners[0].raw,
            logical=None,
            suggestion="patch",
            planned_from_level=None,
            notes=tuple(notes),
            conflict=True,
        )

    chosen = next(iter(unique.values()))
    if chosen.kind in ("bare", "level"):
        level = chosen.level or "patch"
        planned = None
        current = parse_version(current_version) if current_version else None
        if current is not None:
            planned_ver, bump_notes = versionplan.bump(current, [level])
            notes.extend(bump_notes)
            if planned_ver is not None:
                planned = planned_ver.formatted().lstrip("v")
        return PublishIntent(
            matched=True,
            publish_label=publish_label,
            kind="level",
            level=level,
            target_version=planned,
            label=chosen.raw,
            logical=True,
            suggestion=None,
            planned_from_level=planned,
            notes=tuple(notes),
        )

    target = chosen.target_version or ""
    current = parse_version(current_version) if current_version else None
    if current is None:
        notes.append(
            "could not parse current version; treat explicit target as "
            "unverified and ask the user."
        )
        return PublishIntent(
            matched=True,
            publish_label=publish_label,
            kind="version",
            level=None,
            target_version=target,
            label=chosen.raw,
            logical=False,
            suggestion="patch",
            planned_from_level=None,
            notes=tuple(notes),
        )

    targets = _single_level_targets(current)
    patch_plan = targets.get("patch")
    logical = target in targets.values()
    suggestion = None
    matching_level = None
    for level, ver in targets.items():
        if ver == target:
            matching_level = level
            break
    if not logical:
        suggestion = "patch"
        closer = None
        for level in ("patch", "minor", "major"):
            if level in targets:
                closer = f"{level} → {targets[level]}"
                break
        notes.append(
            f"explicit version {target} is not a single-level bump from "
            f"{current.formatted().lstrip('v')}"
            + (f" (nearest: {closer})" if closer else "")
            + "; ask the user before releasing."
        )
    return PublishIntent(
        matched=True,
        publish_label=publish_label,
        kind="version",
        level=matching_level,
        target_version=target,
        label=chosen.raw,
        logical=logical,
        suggestion=suggestion,
        planned_from_level=patch_plan,
        notes=tuple(notes),
    )


def intent_to_dict(intent: PublishIntent) -> dict[str, object]:
    """JSON-serialisable form of :class:`PublishIntent`."""
    return {
        "matched": intent.matched,
        "publish_label": intent.publish_label,
        "kind": intent.kind,
        "level": intent.level,
        "target_version": intent.target_version,
        "label": intent.label,
        "logical": intent.logical,
        "suggestion": intent.suggestion,
        "planned_from_level": intent.planned_from_level,
        "conflict": intent.conflict,
        "notes": list(intent.notes),
    }
