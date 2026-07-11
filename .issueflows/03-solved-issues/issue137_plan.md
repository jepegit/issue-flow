# Plan — Issue #137: publish a confirmed epic plan to GitHub issues

Part of epic #144 (staged planning mode), stage 1. Depends on #136 (stacked
on its branch).

## Goal

`/iflow-epic publish [stage <k>]` turns a **confirmed** epic plan into real
GitHub issues, stage by stage: `gh issue create` per unpublished spec,
yolo label per the recorded fitness judgment, a task list maintained on the
epic anchor issue, and published numbers recorded back into the plan file so
re-runs are idempotent.

## Constraints

- The **drafting** action stays write-free; `publish` is the only
  GitHub-writing path on this surface, and it is gated by one consolidated
  confirm (with a dry-run listing shown first).
- Publish only from a plan with `Status: confirmed`; refuse drafts.
- Stage-by-stage: default is the earliest stage with unpublished specs; a
  named stage publishes exactly that stage.
- Idempotent: specs that already carry a `Published: #<M>` line are skipped.
- Dependency resolution: create issues in dependency order within the stage;
  `stage <j> issue <k>` placeholders that point at already-published specs
  are rewritten to the real `#<M>`; placeholders at still-unpublished specs
  stay as placeholders with a note.
- The `yolo` label is applied only when it exists in the repo
  (`gh label list` check); otherwise note the gap and continue.
- Anchor-issue task list updates are **append/patch only** — never rewrite
  the user's own body text.

## Approach

1. Extend `templates/skills/iflow_epic/SKILL.md.j2` with an
   `## Action: publish` section implementing the above; soften the former
   "never creates GitHub issues" wording to "the drafting action never
   writes; `publish` is the single gated exception". Same for the command
   twin, workflow-doc row, and rules paragraph.
2. Plan-file contract addition: `- Published: #<M>` line per issue spec.
3. Tests: update the draft-only assertions; add publish-section assertions
   (consolidated confirm, dry-run, `Status: confirmed` gate, `Published:`
   recording, idempotent skip, yolo-label existence check).
4. HISTORY entry; scaffold regen.

## Test strategy

Template-contract tests only (this slice is prompt-side; the deterministic
epic-status parser is #138).
