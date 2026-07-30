# Plan — Issue #224: Release v0.4.9

## Goal

Ship **v0.4.9**: bump static version `0.4.8` → `0.4.9`, promote
`HISTORY.md` `[Unreleased]` into a dated `## [0.4.9]` section, refresh
release docs per the issue comment, land via PR, then create the GitHub
release so `publish.yml` publishes to PyPI.

## Constraints

- Strategy: **static uv** (`this-project.md` + `version-plan` →
  `uv version --bump patch` → planned `0.4.9`).
- Issue title asks for **v0.4.9**, not `0.5.0`. Open milestone **v.0.5.0**
  issues (#12, #17, #21, #100, #101, #210, #221) stay out of this release.
- “Depends on: issues with milestone this release” — there is no `v0.4.9`
  milestone; payload is the current `[Unreleased]` bullets already landed
  on `main`.
- Do not invent features in this PR — release hygiene + docs only.
- Tag / `gh release create` only **after** the bump PR is on `main`
  (squash-merge world).

### Prior art

- `docs/developing.md` — “Publishing a new version” playbook (stale
  examples still show `uv version 0.2.0`).
- `.issueflows/04-designs-and-guides/this-project.md` — Release & version
  bump (uv static).
- `.issueflows/04-designs-and-guides/release-strategies.md` (#125).
- `issue-flow agent version-plan --bump patch` → `0.4.9` /
  `uv version --bump patch`.
- `/iflow-close` + `iflow-history-update` — promote `[Unreleased]` when
  bumping.
- `.github/workflows/publish.yml` — triggers on GitHub release.
- **HISTORY drift:** `## [0.4.8]` section missing; GitHub `v0.4.8` notes
  cite #214/#216 while `#214` still sits under `[Unreleased]` — clean
  during promote.

## Approach

1. **Doc pass (comment #224)** — Update `docs/developing.md` release
   steps to match current practice: `uv version --bump <level>`, HISTORY
   promote via close / Keep a Changelog, then `gh release create vX.Y.Z
   --generate-notes` (keep alias note). Skim `README.md` /
   `docs/index.md` for stale release instructions only — no drive-by
   rewrites of unrelated pages. Scaffolded `docs/issue-workflow.md` /
   config docs already cover recent features; no template churn unless a
   clear stale release instruction surfaces.
2. **HISTORY hygiene** — Before/during bump:
   - Add a short `## [0.4.8] - 2026-07-26` section from the GitHub release
     notes (#214, #216) if still missing.
   - Drop any Unreleased bullet already shipped in 0.4.8 (notably #214).
   - Keep remaining Unreleased bullets for 0.4.9 (#213, #218–#220, #228,
     and any other post-0.4.8 items still listed).
3. **Bump + promote** — `uv version --bump patch` (verify `0.4.9`);
   promote `[Unreleased]` → `## [0.4.9] - <today>`, open empty
   `[Unreleased]`. Prefer doing this in the release PR commit (same as
   `/iflow-close bump patch` would).
4. **Sanity** — `uv run pytest`, `uv run ruff check src/ tests/`.
5. **Land** — Commit on `224-release`, push, PR (`Closes #224`), merge
   when green.
6. **Post-merge (required to finish the issue)** — On updated `main`:
   `gh release create v0.4.9 --generate-notes` (or `release` alias).
   Confirm `publish.yml` run starts. `/iflow-cleanup` for branch hygiene.

## Files to touch

| Path | Change |
|------|--------|
| `docs/developing.md` | Refresh release steps to uv `--bump` + HISTORY + tag |
| `HISTORY.md` | Backfill 0.4.8 if needed; promote Unreleased → 0.4.9 |
| `pyproject.toml` (+ `uv.lock` if changed) | `0.4.8` → `0.4.9` |
| `README.md` / `docs/index.md` | Only if release instructions are stale |

## Test strategy

- `uv run pytest` and `uv run ruff check src/ tests/` before the release
  commit.
- After GitHub release: confirm Actions `publish` workflow for `v0.4.9`.

## Open questions

1. **Target version** — Issue says **0.4.9** (patch). Confirm (vs wait for
   more work / jump to 0.5.0). **Recommend: ship 0.4.9 now.**
2. **Milestone dependency** — Treat “this release” as Unreleased-on-main,
   not v0.5.0 open issues. **Recommend: yes.**
3. **Who creates the GitHub release?** — Plan includes post-merge
   `gh release create` in this issue’s closeout (after PR merge), not
   inside the bump commit. OK?
