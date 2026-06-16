# Status for issue #70: Iterative small fixes

Interactive `/issue-fix` session. Each small fix gets a short plan, is
implemented only on confirmation, and is logged below. The session is landed as
one PR via `/issue-close`.

- [x] Done

## Verification

- `uv run pytest` — **146 passed**. (An earlier run showed 5 failures in the
  per-editor init/cli tests; root cause was the project's local `.env` setting
  `ISSUEFLOW_AGENT_DIR=.cursor`, which `load_dotenv` leaked into the test env and
  forced every editor's agent dir to `.cursor`. Resolved by trimming `.env` to
  just the API key — not a code issue. Test-isolation hardening for `ISSUEFLOW_*`
  env vars is a possible future follow-up.)
- `uv run ruff check src/ tests/` — all checks passed.
- `graphify-out/` regeneration from testing `graphify extract` was intentionally
  left out of the PR.

## Iterative fixes log

- **2026-06-16 — `issue-flow graphify` now loads the project `.env`.** The
  `graphify` CLI path never imported `issue_flow.config` (where `load_dotenv()`
  runs), and `graphify` itself doesn't read `.env`, so `GEMINI_API_KEY` (and
  other LLM keys) in `.env` never reached the spawned subprocess —
  `graphify extract` failed with "no LLM API key found". Added
  `_load_project_env(project_root)` in `src/issue_flow/graphify.py`, called from
  `run_build()` before spawning, which loads `<project_root>/.env`
  (`override=False`, relative to `-C` dir). Added two tests in
  `tests/test_graphify.py`. Verified end-to-end: `graphify extract` now selects
  the gemini backend and runs semantic extraction.
  - _Follow-up (graphify-side, out of scope):_ graphify's gemini backend needs
    the `openai` package in its own tool venv (`chunk 1/1 failed: ... requires
    the openai package`). Reinstall graphify with that extra, e.g.
    `uv tool install graphifyy --with openai`.
- **2026-06-16 — Document putting the LLM API key in `.env` (`README.md`).**
  The README listed the API-key env vars and (separately) that `.env` is read,
  but never connected them — and said the graphify integration had "no `.env`
  switch". Now that fix #1 makes `issue-flow graphify` load `.env`, updated the
  graphify section and the Configuration `.env` section to state that an LLM key
  (`GEMINI_API_KEY`, etc.) in `.env` is picked up for `graphify extract`, and
  reworded the "no `.env` switch" line so it only refers to enabling the
  integration. Docs-only; no code/tests.
