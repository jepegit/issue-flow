# Hands-off mode

**Issue:** [#402](https://github.com/jepegit/issue-flow/issues/402)
**Status:** decided 2026-10-05.

## Context

Drive already composes epic draft, publish, auto, final review, and
local cleanup. Each child skill still asks, and drive requires an
existing issue number. A full feature should run after one authorization,
including when the work starts as a short description.

## Decision

`[issueflow].hands_off` (default false) is a behaviour knob. It does not
add a scaffolding mode id. `issue-flow mode hands-off` sets the key and
re-renders skills through the same path as `issue-flow update`.
`issue-flow mode standard` (alias `off`) sets it false and re-renders.
`issue-flow mode` with no arguments prints the effective value for the
current project.

Turning the knob on is the authorization. The command prints that the
next drive may auto-merge (per `cycle_nonyolo`) and delete local
branches (`-d` reachable, `-D` squash-landed) and asks once unless
`--yes`.

While the knob is on:

- `/iflow-drive`, `/iflow-yolo`, `/iflow-cycle`, and `/iflow-auto` skip
  their up-front confirms. Child confirms those skills repeat (epic
  publish, auto overnight, cycle queue, yolo confirm, cleanup A1/A2
  when the `drive` token is passed) are already authorized.
- `/iflow-drive <short description>` runs grill-me, creates one
  epic-anchor issue (same shape as `/iflow-issue epic`), then drives
  that number. A non-integer still stops and asks for `<N>` when the
  knob is off.
- AST graphify (`issue-flow graphify -C <project_root>`, never
  `extract`) runs before the epic draft and before each child
  `/iflow-plan`, even when `auto_graphify_on_plan` and
  `graphify_gitignored` are false. A missing or failing graphify is
  reported; planning continues with grep.
- A spent auto loop budget records `accepted` and continues to the
  epoch gate and final review.

Interactive `/iflow-pick`, plan Accept, `/iflow-build`, and ordinary
close still ask. Safety stops stay: unfixable failure, refused merge,
non-fast-forward that `sync-branch` cannot resolve, dirty product tree,
and `abort` / `stop` / `cancel` / `halt`. Never weaken yolo safeguards.
Never `-D` `unique_work`. Never Phase B. Never rebase or force-push the
default branch. `yolo: no` stays a lane (`cycle_nonyolo`).

Precedence matches `grill_me_default`: project `config.toml`, then
user-global, then `ISSUEFLOW_HANDS_OFF`, then the default. The switch
is per project (the working directory), not a rewrite of every
registered repo.

## Alternatives

- A new `[modes.hands-off]` scaffolding id. Rejected: `mode` already
  chooses which skills exist (`standard` / `novice` / `simple`).
- Regex-rewrite of installed skill files. Rejected: Jinja plus
  `issue-flow update` already bake knobs.
- Keep yolo and cycle confirms unless the caller is drive. Rejected:
  those prompts live in the same rendered text.
- Stop the drive when graphify fails. Rejected: same continue-on-grep
  rule as the existing plan refresh.

## Link

Drive: [drive-mode.md](./drive-mode.md).
Knobs: [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).
Graphify: [graphify-integration.md](./graphify-integration.md).
