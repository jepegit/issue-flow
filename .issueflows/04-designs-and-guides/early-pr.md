# Early pull request

**Issue:** [#99 — Create pull request early](https://github.com/jepegit/issue-flow/issues/99)
**Status:** decided 2026-07-23.

## Context

PRs were opened only in `/iflow-close`. Sometimes teams want a draft PR
earlier (CI + review while build continues). Close must stay idempotent and
still own HISTORY.

## Decisions

1. **`[issueflow] early_pr = false`** by default — today's close-only create.
2. **Trailing overrides on `/iflow-build`:** `early` / `pr` force on;
   `noearly` force off. Precedence: trailing > baked config > default.
3. **When:** after the first successful push of an issue branch (or when a
   remote tip exists with no open PR). Always **draft**
   (`gh pr create --draft`) with `Refs #N`.
4. **Close:** list-before-create updates the existing PR; writes HISTORY in
   step 3 even if a draft already exists; marks ready (unless `draft` token)
   before yolo merge.
5. **Formalize close `draft`:** trailing `draft` → `--draft` on create; skips
   yolo merge.

## Alternatives considered

- Open at plan confirm / init — rejected (no commits yet).
- Ready (non-draft) early PR — rejected (noisier; draft is the safe default).
- New slash command — rejected (timing option, not a new lifecycle step).

## Link

Knobs table: [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).
Changelog ownership: [changelog-timing.md](./changelog-timing.md).
List/reuse contract: [gh-list-and-watch.md](./gh-list-and-watch.md).
