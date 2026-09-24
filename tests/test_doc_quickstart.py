"""The canonical quick start must match on Home, Getting started and README (#348)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGES = ["docs/index.md", "docs/getting-started.md", "README.md"]


def _quick_start_rows(path: Path) -> list[str]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `iflow ") and line.endswith("|"):
            rows.append(line)
            if line.startswith("| `iflow cleanup`"):
                break
    return rows


@pytest.mark.parametrize("page", PAGES[1:])
def test_quick_start_matches_home(page: str) -> None:
    home = _quick_start_rows(REPO_ROOT / PAGES[0])
    assert [row.split("|")[1].strip() for row in home] == [
        "`iflow pick`",
        "`iflow plan`",
        "`iflow build`",
        "`iflow close`",
        "`iflow cleanup`",
    ]
    assert _quick_start_rows(REPO_ROOT / page) == home
