# Issue #317: Help agents watch until a PR is merge-ready

Source: https://github.com/jepegit/issue-flow/issues/317

## Original issue text

### Problem / context

After `/iflow-close` (no `yolo`), agents run a one-shot `gh pr checks` and stop. Pending CI is reported, then the session waits on the human. The `gh-ci` skill documents how to *watch checks*, not whether the PR is *allowed to merge* (draft, reviews, `mergeable` / `mergeStateStatus`, failed required checks). Agents invent `gh` JSON fields or poll badly.

### Spec

1. Add `issue-flow agent pr-ready <N>` (`--json`, `-C`, `--repo` if needed) that classifies an open PR:
   - `ready` — not draft, `mergeable` CLEAN (or equivalent), required checks pass/skipping, review gate not blocking
   - `pending` — checks or mergeability still in flight
   - `blocked` — red checks, CONFLICTING/DIRTY, draft, required reviews missing
   - `unknown` — `gh` empty / missing fields
2. Print a short human report + JSON (`state`, `pr`, `url`, `isDraft`, `mergeable`, `mergeStateStatus`, `reviewDecision`, failing/pending check names).
3. Optional `--watch` honouring `checks_watch_minutes` (same cap as close yolo): poll until `ready` / `blocked` / budget, then exit 0 only on `ready`.
4. Point `gh-ci` and `/iflow-close` (non-yolo snapshot step) at this command: after opening a PR, **offer** `pr-ready --watch` instead of a one-shot dump. Do **not** auto-merge from this helper; merge stays `/iflow-close yolo` or the user.
5. One line in `docs/llms.txt` / agent how-to so “is the PR ready?” hits this command.

### Acceptance criteria

- `issue-flow agent pr-ready --help` exists; `--json` schema documented in CLI reference.
- Tests cover ready / pending / blocked / missing PR (mocked `gh`).
- `gh-ci` and close skill mention `agent pr-ready`; yolo merge sequence unchanged (still `gh pr merge` after watch).
- No `--admin`, no skip-checks, no merge from `pr-ready`.

### Out of scope

- Changing yolo merge / `--auto` fallback policy.
- Auto-merging from `/iflow-close` without `yolo`.
- Slack/email notify.
