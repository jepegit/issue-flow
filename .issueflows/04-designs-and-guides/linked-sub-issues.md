# Linked sub-issues (`/iflow-split`)

**Issue:** [#12 — Create linked (sub) issues for over-ambitious issues](https://github.com/jepegit/issue-flow/issues/12)
**Status:** decided 2026-08-13, implemented in the same issue.
**Closes:** Phase B of #63 (pick used to mention-only).

## Context

`/iflow-epic` already splits large work into staged issues + a markdown task
list on the anchor. `/iflow-issue` creates one well-specified issue.
`/iflow-pick` only *mentioned* that an over-large issue could be broken up.

GitHub now has native parent/child sub-issues. Agents need a confirm-gated
recipe: `sub_issue_id` is the REST **database id**, not the issue number, and
`gh api -f` stringifies and 422s.

## Decisions

### 1. Name: `/iflow-split` (skill stem `iflow_split`)

New off-path surface. Rejected folding into `/iflow-issue` (that skill
creates *one* issue) and `/iflow-sub` (opaque).

### 2. Split vs epic

- **Split** — 2–5 flat children, each one branch / one PR. Parent stays
  **open** as the tracker.
- **Epic** — sequential stages, `Depends on`, yolo-fitness, publish
  idempotency. If a proposed split needs that, stop and point at
  `/iflow-epic`.

### 3. Offer-only from pick / issue / plan

Those surfaces mention `/iflow-split` or `/iflow-epic` and stop. They never
create children. `/iflow` never auto-dispatches split.

### 4. Native sub-issue + task-list fallback

Create with `gh issue create`, then
`issue-flow agent sub-issue-add <parent> <child>` (JSON `--input`).
Append `- [ ] #<M>` under `## Sub-issues` on the parent. If the sub-issue
API fails, keep the created issue and rely on the task list.

### 5. Local parent parks; children stay on GitHub

If `issue<N>_*` is the focus, move it to `02-partly-solved-issues/`.
Do not write child tracking groups at create time. Do not close the parent.

## Out of scope (v1)

- Retrofitting `/iflow-epic publish` to also call the sub-issues API.
- Auto-split without confirm; silent pick routing.
- GitLab; GraphQL `addSubIssue`.

## Link

Issue #12. Sibling: [create-non-epic-issue.md](./create-non-epic-issue.md).
