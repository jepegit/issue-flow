# Status — Issue #224: Release

- [x] Done

## What's done

- Refreshed `docs/developing.md` release playbook (`uv version --bump`,
  HISTORY promote, post-merge `gh release create` on `main`).
- HISTORY: backfilled `## [0.4.8] - 2026-07-26` (#214, #216); promoted
  post-0.4.8 bullets to `## [0.4.9] - 2026-07-30` (incl. #224); empty
  `[Unreleased]`. (`/iflow-close nohistory` — already promoted.)
- `uv version --bump patch` → `0.4.9` (`pyproject.toml` + `uv.lock`).
- pytest 586 + ruff green.

## Remaining work

- After PR merges: on `main`, `gh release create v0.4.9 --generate-notes`
  and confirm `publish.yml` (PyPI). Then `/iflow-cleanup`.
