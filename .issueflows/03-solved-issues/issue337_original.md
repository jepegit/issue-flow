# Issue #337: noob Recommended should follow epic session, not raw `next_command`

Source: https://github.com/jepegit/issue-flow/issues/337

## Original issue text

## Problem / context

When `noob = true`, each lifecycle skill ends by running
`issue-flow agent state --json` and printing `next_command` as
**Recommended**, plus a short stem list (`src/issue_flow/templates/skills/_noob_next.md.j2`).

`next_command` is only the linear capture→plan→build→close hint.
`#210` / `#333` leave it unset (or as `/iflow-capture`) in the epic gap
on purpose so `/iflow` does not silent-pick. The noob footer still
echoes that field.

Seen on batbase epic `#168` (`iflow epic start` → publish Stage 3):

- After start, unpublished Stage 3: **Recommended: `iflow capture`**,
  then a hedge that this is “not a good move.”
- After the session file was written: same Recommended, while the
  body correctly handed off to `iflow epic 168 publish`.
- After publish, on `chore/168-publish-stage-3` with `#465` unblocked:
  **Recommended: none** (`next_command` is `null`).

The “Also relevant” epic stem list (`/iflow`, `/iflow-pick`,
`/iflow-status`) was fine. The **Recommended** line contradicted the
handoff in the same turn.

## Spec

When `noob` is on and there is **no focus**, **Recommended** must
use `epic_session` + `epic_hint` (and unpublished-stage context
already printed by `/iflow-epic`) instead of blindly printing
`next_command`:

- Session on + `next_candidates` → recommend `/iflow` (one-and-ask)
  or `/iflow-pick` for the first candidate — not `none`, not capture.
- Session on + unpublished current stage (empty `next_candidates`) →
  recommend `/iflow-epic <N> publish`, not `/iflow-capture`.
- No session, no candidates, empty current issues → keep today's
  `/iflow-capture`.

Do **not** change `#210`: `agent state` `next_command` stays unset in
the epic gap so the dispatcher does not auto-dispatch pick.

Prefer teaching the noob footer (and a one-line why) to read the
existing state payload. Only extend `agent state` if the footer
cannot distinguish “unpublished stage” from “truly nothing to do”
without it.

Re-run `issue-flow update` after the template change so scaffolded
skills pick it up.

## Acceptance criteria

- With `noob` on, an epic session, and at least one
  `next_candidates` entry, the footer’s **Recommended** is `/iflow`
  or `/iflow-pick` — never `none` and never `/iflow-capture`.
- With `noob` on, a confirmed epic whose current stage is
  unpublished, **Recommended** is `/iflow-epic <N> publish` — never
  `/iflow-capture`.
- `agent state --json` `next_command` remains unset in the epic gap
  (existing `#210` / `#333` tests still pass).
- Footer still does not auto-dispatch.

## Out of scope

- Auto-dispatching `/iflow-pick` or publish from `/iflow` or noob.
- Changing yolo / cycle / auto / drive.
- Turning `noob` on in this repo’s `config.toml`.

Related: #307, #210, #333.
