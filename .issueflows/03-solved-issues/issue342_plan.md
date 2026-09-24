# Plan — Issue #342: docs: fix Read the Docs URLs missing /en/latest/

(yolo chain via /iflow-drive 341 → /iflow-auto → /iflow-cycle; auto-confirmed.)

## Goal

Every link to a docs page uses `https://issue-flow.readthedocs.io/en/latest/<path>/`. Unversioned page paths return 404 on Read the Docs.

## Approach

- Rewrite unversioned page URLs (`…readthedocs.io/<page>/`) to `/en/latest/<page>/` in `docs/llms.txt`, `README.md`, and the templates `commands/iflow-init.md.j2`, `skills/iflow_init/SKILL.md.j2`, `docs/issue-workflow.md.j2`.
- Keep the bare root URL (`https://issue-flow.readthedocs.io/`) and `/llms.txt`: both return 200 (verified with curl).
- Set `site_url` in `zensical.toml` to `https://issue-flow.readthedocs.io/en/latest/`.
- Re-render this repo's scaffold (`uv run scripts/update_issueflow_setup.py`) so `docs/issue-workflow.md` and `.cursor/` match.
- Update the tests that pin the old URLs, and add a regression test that scans `src/issue_flow/templates/` and `docs/llms.txt` for unversioned page links.

## Files to touch

`docs/llms.txt`, `README.md`, `zensical.toml`, the three templates, `docs/issue-workflow.md` (rendered), `tests/test_init.py`, `tests/test_templating.py`, and a new test.

## Test strategy

`uv run pytest`. Grep check from the issue goal. curl every rewritten URL and expect 200.
