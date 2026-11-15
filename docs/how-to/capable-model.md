---
title: Prepare for a capable model
---

# Prepare for a capable model

## Goal

Re-render a project's skills for **Claude Fable 5.2** and similar models:
finish the task, post one-line progress on long turns, and end with a recap
that stands alone.

## Steps

1. From the project root, after `issue-flow init`:

   ```bash
   issue-flow prep fable
   ```

   Confirm once (or pass `--yes`). This sets `capable_model = true`, sets
   `caveman_default = false`, and re-renders the skills.

2. The rendered rule then tells the agent to:

   - Finish work that is independent of an open question. Diagnose an ordinary
     tool failure and continue. A deliberate blocker, or a risky or destructive
     action, still stops.
   - Say one line before the first tool call, then a one-line update every few
     tool calls.
   - End a long turn with a recap that stands alone: what you found, what you
     did, and what is next.
   - Keep `/iflow-plan` waiting for Accept. `/iflow-run direct` still skips
     the plan file, because that invocation is the confirm.
   - On close, name an unrelated path and stop. Report the CI snapshot and
     leave the watch command for you.
   - On bookkeeping steps, leave the model's effort at the editor setting.

   Scope stays on the issue. The skill cannot set the API effort parameter.

3. Check or turn it off:

   ```bash
   issue-flow prep        # print capable_model
   issue-flow prep off    # clear the posture and re-render
   ```

   `off` leaves `caveman_default` as it is.

`fable` also accepts `capable` and `on`. `off` also accepts `standard`.

## Related

- [CLI — `issue-flow prep`](../cli.md#issue-flow-prep)
- [Configuration — `capable_model`](../configuration.md#all-settings)
- [Command reference](../issue-workflow.md) — `/iflow-run direct`
- [Choose a mode](choose-a-mode.md) — which commands are installed
