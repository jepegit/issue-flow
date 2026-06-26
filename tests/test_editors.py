"""Tests for issue_flow.editors (editor profile registry and resolution)."""

from __future__ import annotations

import pytest

from issue_flow.editors import (
    DEFAULT_EDITOR,
    EDITORS,
    EditorProfile,
    get_profile,
    resolve_editors,
)


def test_registry_contains_the_four_supported_editors() -> None:
    assert set(EDITORS) == {"cursor", "claude", "opencode", "codex"}
    for editor_id, profile in EDITORS.items():
        assert isinstance(profile, EditorProfile)
        assert profile.id == editor_id
        assert profile.agent_dir.startswith(".")


def test_default_editor_is_cursor() -> None:
    assert DEFAULT_EDITOR == "cursor"
    assert get_profile(DEFAULT_EDITOR).agent_dir == ".cursor"


def test_cursor_is_skills_first_with_rules_extra() -> None:
    cursor = get_profile("cursor")
    assert cursor.commands_dir is None
    assert cursor.rules_extra == (
        "rules/issueflow-rules.mdc.j2",
        "{agent_dir}/rules/issueflow-rules.mdc",
    )
    assert cursor.graphify_installer == "cursor"


def test_codex_has_no_commands_dir_and_no_rules_extra() -> None:
    codex = get_profile("codex")
    assert codex.commands_dir is None
    assert codex.rules_extra is None
    assert codex.graphify_installer is None


def test_opencode_uses_singular_command_dir() -> None:
    assert get_profile("opencode").commands_dir == "command"


def test_only_cursor_has_a_graphify_installer() -> None:
    assert get_profile("cursor").graphify_installer == "cursor"
    for editor_id in ("claude", "opencode", "codex"):
        assert get_profile(editor_id).graphify_installer is None


def test_get_profile_rejects_unknown_editor() -> None:
    with pytest.raises(ValueError):
        get_profile("sublime")


def test_resolve_editors_defaults_to_cursor() -> None:
    assert [p.id for p in resolve_editors(None)] == ["cursor"]
    assert [p.id for p in resolve_editors([])] == ["cursor"]


def test_resolve_editors_all_expands_to_registry_order() -> None:
    assert [p.id for p in resolve_editors(["all"])] == list(EDITORS)


def test_resolve_editors_dedupes_preserving_order() -> None:
    resolved = resolve_editors(["claude", "cursor", "claude"])
    assert [p.id for p in resolved] == ["claude", "cursor"]


def test_resolve_editors_is_case_insensitive() -> None:
    assert [p.id for p in resolve_editors(["Cursor", "CLAUDE"])] == [
        "cursor",
        "claude",
    ]


def test_resolve_editors_rejects_unknown_editor() -> None:
    with pytest.raises(ValueError):
        resolve_editors(["cursor", "nano"])
