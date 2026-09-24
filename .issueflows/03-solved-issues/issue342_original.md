# Issue #342: docs: fix Read the Docs URLs missing /en/latest/

Source: https://github.com/jepegit/issue-flow/issues/342

## Original issue text

## Context and spec

Links of the form `https://issue-flow.readthedocs.io/<path>/` (without `/en/latest/`) return 404. They appear in `docs/llms.txt` (6), `README.md` (1), `docs/issue-workflow.md` (1), `src/issue_flow/templates/docs/issue-workflow.md.j2` (1), `src/issue_flow/templates/commands/iflow-init.md.j2` (2) and `src/issue_flow/templates/skills/iflow_init/SKILL.md.j2` (3). Rewrite them to `/en/latest/…`. Also set `site_url` in `zensical.toml` to the versioned base. Re-render this repo's own scaffold (`uv run scripts/update_issueflow_setup.py`) so `docs/issue-workflow.md` matches the template. Optionally add a test that fails if any template contains the unversioned pattern. See review §1.

**Goal:** `grep -rE 'readthedocs\.io/[a-z]' docs src README.md | grep -v /en/` returns nothing, and every rewritten URL returns HTTP 200.

**Model:** fast

Depends on: none

Full review: `.issueflows/04-designs-and-guides/docs-usability-review.md`.

Part of epic #341.
