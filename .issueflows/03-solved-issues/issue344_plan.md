# Plan — Issue #344: ci: add a link check on the built docs site

(yolo chain via /iflow-drive 341 → /iflow-auto → /iflow-cycle; auto-confirmed. Planned as yolo: no. The scope turned out small: one CI job plus a script.)

## Goal

A PR that introduces a broken internal doc link fails CI. The current `main` passes.

## Approach

- `scripts/check_doc_links.sh`: `uv run --group docs zensical build`, then copy `site/` to `_linkcheck/en/latest/`. The copy is needed because `site_url` (since #342) puts `/en/latest/` into root-relative links. Then run `lychee --offline --root-dir _linkcheck --index-files index.html`. `--stage-only` skips lychee, for CI.
- New `docs-links` job in `ci.yml`. The internal check (offline) blocks. The external check is non-blocking (`fail: false`, retries, accepts 429), with results in the job summary.
- Fix the 2 broken links the new check found in `developing.md` (`../src/issue_flow/modes.*`), pointing them to GitHub blob URLs.
- Document how to run the check locally in `docs/developing.md`. Add `/_linkcheck` to `.gitignore`.

## Test strategy

Run the script locally with lychee 0.24.2: it fails (rc=2) on the old `developing.md` and passes (rc=0) after the fix. The PR's own CI run exercises the new job.
