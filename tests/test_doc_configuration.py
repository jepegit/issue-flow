"""docs/configuration.md must document every config key exactly once (#359)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from issue_flow.config_ops import CONFIG_KEYS

DOC = Path(__file__).resolve().parent.parent / "docs" / "configuration.md"


def _section(text: str, heading: str) -> str:
    start = text.index(f"\n## {heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else None]


@pytest.mark.essential
def test_all_settings_table_lists_every_config_key_once() -> None:
    table = _section(DOC.read_text(encoding="utf-8"), "All settings")
    rows = re.findall(r"^\| `([a-z_]+)` \|", table, flags=re.MULTILINE)
    assert sorted(rows) == sorted(CONFIG_KEYS), (
        f"missing: {sorted(set(CONFIG_KEYS) - set(rows))}, "
        f"unknown: {sorted(set(rows) - set(CONFIG_KEYS))}"
    )
    assert len(rows) == len(set(rows)), "a key is listed twice"


def test_configuration_page_starts_with_common_changes() -> None:
    text = DOC.read_text(encoding="utf-8")
    first_h2 = re.search(r"^## (.+)$", text, flags=re.MULTILINE)
    assert first_h2 is not None and first_h2.group(1) == "Common changes"


def test_configuration_prose_has_no_bare_issue_numbers() -> None:
    text = re.sub(r"\]\([^)]*\)", "]()", DOC.read_text(encoding="utf-8"))
    assert not re.search(r"(?<![\w/])#\d{2,4}\b", text)
