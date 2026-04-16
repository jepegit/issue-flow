"""Refresh this repository's issue-flow scaffold from packaged templates.

Equivalent to running ``uv run issue-flow update .`` from the repo root, but
works no matter what directory your shell is currently in.
"""

from __future__ import annotations

from pathlib import Path

from issue_flow.init import run_update


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    run_update(repo_root)


if __name__ == "__main__":
    main()
