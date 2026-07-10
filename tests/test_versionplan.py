"""Tests for issue_flow.versionplan — PEP 440 planning + strategy detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from issue_flow.versionplan import (
    bump,
    default_levels,
    detect_strategy,
    parse_version,
)

# ---------------------------------------------------------------------------
# parsing / formatting
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "1.0.4",
        "v1.0.4a2",
        "0.4.1rc1",
        "2.0.0.post1",
        "0.5.0.dev3",
        "v0.4.1a4.post1",
    ],
)
def test_parse_format_roundtrip(text: str) -> None:
    version = parse_version(text)
    assert version is not None
    assert version.formatted() == text


@pytest.mark.parametrize("text", ["not-a-version", "1.0.0+local", "release-2020"])
def test_parse_rejects_out_of_scope_forms(text: str) -> None:
    assert parse_version(text) is None


# ---------------------------------------------------------------------------
# bump arithmetic — the level table from the iflow-version-bump skill
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "levels, expected",
    [
        (["major"], "1.0.0"),
        (["minor"], "0.5.0"),
        (["patch"], "0.4.2"),
        (["stable"], "0.4.1"),
        (["alpha"], "0.4.1a5"),
        (["beta"], "0.4.1b1"),
        (["rc"], "0.4.1rc1"),
        (["post"], "0.4.1a4.post1"),
        (["minor", "alpha"], "0.5.0a1"),
    ],
)
def test_bump_matches_skill_table(levels: list[str], expected: str) -> None:
    current = parse_version("0.4.1a4")
    assert current is not None
    planned, _ = bump(current, levels)
    assert planned is not None
    assert planned.formatted() == expected


def test_bump_preserves_v_prefix() -> None:
    current = parse_version("v1.0.4a2")
    assert current is not None
    planned, _ = bump(current, ["alpha"])
    assert planned is not None
    assert planned.formatted() == "v1.0.4a3"


def test_bump_refuses_prerelease_demotion() -> None:
    current = parse_version("1.0.0rc1")
    assert current is not None
    planned, notes = bump(current, ["alpha"])
    assert planned is None
    assert any("forward" in note for note in notes)


def test_bump_alpha_from_stable_advances_patch() -> None:
    current = parse_version("1.0.4")
    assert current is not None
    planned, notes = bump(current, ["alpha"])
    assert planned is not None
    assert planned.formatted() == "1.0.5a1"
    assert any("stable" in note for note in notes)


def test_bump_dev_requires_pairing_from_non_dev() -> None:
    current = parse_version("1.0.4")
    assert current is not None
    planned, notes = bump(current, ["dev"])
    assert planned is None
    assert any("paired" in note for note in notes)


def test_bump_dev_alone_advances_existing_dev() -> None:
    current = parse_version("1.0.4.dev1")
    assert current is not None
    planned, _ = bump(current, ["dev"])
    assert planned is not None
    assert planned.formatted() == "1.0.4.dev2"


def test_bump_dev_paired_with_patch() -> None:
    current = parse_version("0.4.1")
    assert current is not None
    planned, _ = bump(current, ["patch", "dev"])
    assert planned is not None
    assert planned.formatted() == "0.4.2.dev1"


def test_bump_applies_levels_in_canonical_order() -> None:
    current = parse_version("0.4.1a4")
    assert current is not None
    planned, notes = bump(current, ["alpha", "minor"])
    assert planned is not None
    assert planned.formatted() == "0.5.0a1"
    assert any("canonical order" in note for note in notes)


def test_bump_rejects_unknown_level() -> None:
    current = parse_version("0.4.1")
    assert current is not None
    planned, notes = bump(current, ["huge"])
    assert planned is None
    assert any("unknown bump level" in note for note in notes)


@pytest.mark.parametrize(
    "current, expected",
    [
        ("0.4.1a4", ["alpha"]),
        ("0.4.1b2", ["beta"]),
        ("0.4.1rc1", ["rc"]),
        ("0.4.1", ["patch"]),
        ("0.4.2.dev1", ["dev"]),
    ],
)
def test_default_levels_stay_on_channel(current: str, expected: list[str]) -> None:
    version = parse_version(current)
    assert version is not None
    assert default_levels(version) == expected


# ---------------------------------------------------------------------------
# strategy detection
# ---------------------------------------------------------------------------


def _write_pyproject(tmp_path: Path, body: str) -> None:
    (tmp_path / "pyproject.toml").write_text(body, encoding="utf-8")


def test_detect_static_version(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, '[project]\nname = "x"\nversion = "1.2.3"\n')
    strategy, _reason, static = detect_strategy(tmp_path)
    assert strategy == "uv"
    assert static == "1.2.3"


def test_detect_setuptools_scm_table(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        '[project]\nname = "x"\ndynamic = ["version"]\n\n[tool.setuptools_scm]\n',
    )
    strategy, reason, static = detect_strategy(tmp_path)
    assert strategy == "tag"
    assert "setuptools_scm" in reason
    assert static is None


def test_detect_hatch_vcs_in_build_requires(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        '[build-system]\nrequires = ["hatchling", "hatch-vcs"]\n\n'
        '[project]\nname = "x"\ndynamic = ["version"]\n',
    )
    assert detect_strategy(tmp_path)[0] == "tag"


def test_detect_hatch_vcs_version_source(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        '[project]\nname = "x"\ndynamic = ["version"]\n\n'
        '[tool.hatch.version]\nsource = "vcs"\n',
    )
    assert detect_strategy(tmp_path)[0] == "tag"


def test_detect_dynamic_unknown_backend(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, '[project]\nname = "x"\ndynamic = ["version"]\n')
    strategy, reason, _static = detect_strategy(tmp_path)
    assert strategy == "unknown"
    assert "unrecognized" in reason


def test_detect_missing_pyproject(tmp_path: Path) -> None:
    assert detect_strategy(tmp_path)[0] == "unknown"
