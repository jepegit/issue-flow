"""Guard against unversioned Read the Docs page links (issue #342).

Read the Docs serves pages under ``/en/latest/``; a page path without that
prefix (``https://issue-flow.readthedocs.io/how-to/…``) returns 404. The bare
site root and ``/llms.txt`` do resolve, so they are allowed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
UNVERSIONED = re.compile(r"https://issue-flow\.readthedocs\.io/(?!en/|llms\.txt)[a-z]")

SCANNED = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs",
    REPO_ROOT / "src" / "issue_flow" / "templates",
]


def _files() -> list[Path]:
    out: list[Path] = []
    for target in SCANNED:
        if target.is_file():
            out.append(target)
        else:
            out.extend(
                p for p in target.rglob("*") if p.suffix in {".md", ".j2", ".txt"}
            )
    return out


@pytest.mark.essential
def test_no_unversioned_readthedocs_page_links() -> None:
    hits = [
        f"{path.relative_to(REPO_ROOT)}:{lineno}"
        for path in _files()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if UNVERSIONED.search(line)
    ]
    assert not hits, (
        "Unversioned readthedocs page links (use /en/latest/): " + ", ".join(hits)
    )


@pytest.mark.essential
def test_no_mangled_graphify_domain() -> None:
    """``iflow-graphify.net`` is a #74 rename artefact; the site is graphify.net (#353)."""
    hits = [
        f"{path.relative_to(REPO_ROOT)}:{lineno}"
        for path in _files()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if "iflow-graphify.net" in line
    ]
    assert not hits, "Use https://graphify.net/: " + ", ".join(hits)
