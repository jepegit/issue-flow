# `/iflow-issue`: create a normal (non-epic) issue

**Issue:** [#181 — create non-epic issue](https://github.com/jepegit/issue-flow/issues/181)
**Status:** decided 2026-07-19, implemented in the same issue.
**Scope:** new off-path slash command (`/iflow-issue`) + mirrored skill that
authors one well-specified GitHub issue and optionally starts the normal
lifecycle.

## Context

issue-flow already had two create-adjacent surfaces:

- `/iflow-pick fix` / `/iflow-fix` — general-fixes / iterative small-fixes buckets
- `/iflow-epic` — multi-issue staged work (requires an existing epic **anchor**)

There was no first-class way to file **one normal, well-specified** issue (real
body with acceptance criteria) and hand it into `/iflow-init` → `/iflow-plan`.

## Decisions

### 1. Name: `/iflow-issue` (skill stem `iflow_issue`)

Reads as the third creation mode beside fix / epic. Rejected `iflow-new` /
`iflow-create` as vaguer.

### 2. Off-path command + skill, same registration pattern as `/iflow-fix`

Ship `commands/iflow-issue.md.j2` and `skills/iflow_issue/SKILL.md.j2`, register
in `COMMAND_NAMES` / `SKILL_DIRS`, default step profile **reasoning** (drafting
quality). `/iflow` never auto-dispatches.

### 3. Structured draft body (not a full plan)

Propose **Problem / context**, **Spec**, **Acceptance criteria**, optional
**Out of scope**. Confirm before `gh issue create`. Over-large drafts: mention
`/iflow-epic` only — no auto-split.

### 4. Offer branch + `/iflow-init` after create; allow create-only

Default path mirrors `/iflow-pick` setup, then asks about `/iflow-plan` (never
auto-runs plan). Declining Phase 2 leaves a parked GitHub issue for later
`/iflow-pick` / `/iflow-init` — useful for epic anchors.

### 5. Epic-anchor hint: leading `epic`

`/iflow-issue epic <intent>` prefixes the title with `Epic:` and applies the
`epic` label when `gh label list` shows it. `/iflow-epic` points missing-anchor
cases here.

### 6. Coexist — do not merge with pick-fix or `/iflow-fix`

Different intents; docs cross-reference. No CLI `agent` helper in v1 (skills
call `gh` directly).

## Consequences

- Manifest +1 skill (all editors); +1 command for editors with `commands_dir`.
- Touch points: dispatcher off-path lists, rules body, workflow doc, README,
  review/fix/epic cross-links, templating tests.

## Notes for future work

- Optional labels/milestones beyond the epic-anchor label (user-asked only in v1).
- CLI `issue-flow agent issue-create` helper if agents need a deterministic path.
