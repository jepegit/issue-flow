# Issue #16 — status

- [x] Done

## Summary

`issue-flow init` now creates a project-root `.env` with commented `ISSUEFLOW_*` defaults when the file is missing, or appends commented lines for any variables not yet documented in an existing `.env`. Existing `.env` files are never replaced wholesale, including with `init --force`.

## Changes

- `src/issue_flow/init.py`: `_ensure_dotenv_file`, `_dotenv_documents_key`, wired from `run_init`.
- `tests/test_init.py`: coverage for create, idempotent skip, append-missing, and force not wiping secrets.
