# Status — Issue #344

- [x] Done

## What's done

- `scripts/check_doc_links.sh` builds and stages the site under `/en/latest/` and runs lychee offline. `--stage-only` is for CI.
- New `docs-links` job in `.github/workflows/ci.yml`: the internal check blocks, the external check does not (lychee-action v2).
- Fixed 2 broken links found by the check (`developing.md` → `modes.toml` / `modes.py`).
- `developing.md` "How CI works" documents the job and the local command. `/_linkcheck` is ignored.
- Verified locally: the check fails on the old tree and passes on the fixed one. `uv run pytest` passes.

## Remaining work

- None. Stage 1 of epic #341 is complete once this merges.
