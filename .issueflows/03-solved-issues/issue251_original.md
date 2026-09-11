# Issue #251: Support no-PR / ops work (e.g. staging → production)

Source: https://github.com/jepegit/issue-flow/issues/251

## Original issue text

## Problem / context

issue-flow lifecycle assumes code change → branch → PR (`/iflow-close`). Some real work does **not** deserve PR: promote staging→production, flip feature flag, run one-off deploy/ops checklist, tag-only release step with no issue-branch diff.

Today agents still get pushed toward branch/PR even when tree empty or change is outside this repo. `modes.md` deferred “no-PR close variant”; need first-class path.

## Spec

Add supported path for **ops / no-PR** work:

1. **Recognition** — clear signal (label and/or `/iflow-ops` / trailing token / config) so pick/dispatch/close know this issue skips PR.
2. **Close behaviour** — when no-PR: no branch required (or allow work on default), skip push/PR; still update local tracking (`_status`, move to solved/partly), optional confirm checklist (what ran, where, result).
3. **Safeguards** — refuse silent skip when dirty tree has product code changes; require explicit confirm that work was ops-only; document examples (staging→prod, flag flip, external deploy).
4. **Docs** — skill + workflow/rules: when to use vs normal/yolo; design note under `04-designs-and-guides/`.

## Acceptance criteria

- [ ] Documented way to mark/run an issue as no-PR/ops
- [ ] Close path completes without opening PR when marked
- [ ] Dirty product-code tree cannot silently take no-PR path
- [ ] Normal issues unchanged (still PR by default)
- [ ] Design doc records decision + examples

## Out of scope

- Full CD/deploy product (no built-in staging/prod CLI)
- Auto-detect “this is ops” from issue text alone without user/label signal
- Changing squash-merge / cleanup defaults for normal PRs
