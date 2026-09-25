"""Unit tests for publish-on-success label parsing (issue #308)."""

from __future__ import annotations

from issue_flow.publishintent import resolve_publish_intent


def test_bare_publish_defaults_to_patch() -> None:
    intent = resolve_publish_intent(["publish"], "publish", current_version="0.5.11")
    assert intent.matched
    assert intent.kind == "level"
    assert intent.level == "patch"
    assert intent.target_version == "0.5.12"
    assert intent.logical is True
    assert intent.conflict is False


def test_publish_minor_level() -> None:
    intent = resolve_publish_intent(
        ["bug", "publish:minor"], "publish", current_version="0.5.11"
    )
    assert intent.matched
    assert intent.level == "minor"
    assert intent.target_version == "0.6.0"


def test_logical_explicit_version() -> None:
    intent = resolve_publish_intent(
        ["publish:0.5.12"], "publish", current_version="0.5.11"
    )
    assert intent.matched
    assert intent.kind == "version"
    assert intent.logical is True
    assert intent.level == "patch"
    assert intent.target_version == "0.5.12"


def test_illogical_explicit_version_suggests_patch() -> None:
    intent = resolve_publish_intent(
        ["publish:0.9.0"], "publish", current_version="0.5.11"
    )
    assert intent.matched
    assert intent.logical is False
    assert intent.suggestion == "patch"
    assert intent.planned_from_level == "0.5.12"
    assert any("not a single-level bump" in n for n in intent.notes)


def test_conflict_same_specificity() -> None:
    intent = resolve_publish_intent(
        ["publish:minor", "publish:major"],
        "publish",
        current_version="0.5.11",
    )
    assert intent.matched
    assert intent.conflict is True


def test_version_beats_bare() -> None:
    intent = resolve_publish_intent(
        ["publish", "publish:0.6.0"],
        "publish",
        current_version="0.5.11",
    )
    assert intent.kind == "version"
    assert intent.target_version == "0.6.0"
    assert intent.logical is True  # minor from 0.5.11


def test_custom_base_label() -> None:
    intent = resolve_publish_intent(["ship:patch"], "ship", current_version="1.0.0")
    assert intent.matched
    assert intent.level == "patch"
    assert intent.target_version == "1.0.1"


def test_no_match() -> None:
    intent = resolve_publish_intent(
        ["yolo", "bug"], "publish", current_version="0.5.11"
    )
    assert intent.matched is False
