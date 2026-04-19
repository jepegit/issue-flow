"""Shared pytest fixtures for issue-flow tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _stub_dependency_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``check_dependencies`` a no-op by default.

    The production dep-check uses :func:`shutil.which` and would otherwise
    behave differently between dev machines (where ``git`` / ``gh`` are
    usually present) and CI (where they may not be). Stubbing it out
    keeps unrelated tests deterministic and prevents any ``typer.confirm``
    prompt from being triggered during ``run_init`` / ``run_update``.

    Tests that want to exercise the real dependency logic import and call
    :func:`issue_flow.dependencies.check_dependencies` (or
    ``_dependency_gate``) directly after re-patching ``shutil.which`` —
    see ``tests/test_dependencies.py`` and the dep-focused cases in
    ``tests/test_init.py``.
    """
    from issue_flow import init as init_module

    monkeypatch.setattr(init_module, "check_dependencies", lambda: [])
