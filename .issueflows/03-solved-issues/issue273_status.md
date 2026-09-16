# Issue #273 status

- [x] Done

## What's done

- Dropped skill/command open-window option. `open-workspace` print-only. CLI `--open` kept as manual hatch.
- Wired `auto_remove_worktree` (default `true`).
- Close step: `worktree-remove` from home after PR open or yolo merge. Skip `stay` / draft / failed or `--auto`-queued merge / dirty. Knob off → YES/NO. No branch delete.
- Docs + tests. Version `0.4.18`. `uv run pytest` 724 passed.

## Remaining work

- None.
