# Dirty `.issueflows/` directories

_Issue: #47._

## What “dirty” means

A dirty tree has filesystem state that makes the issue-flow lifecycle
(`/iflow`, init/start sweeps, focus resolution) behave inconsistently or stall.
These conditions are **machine-checkable** — the same rules power
`issue-flow doctor`, `issue-flow agent audit`, and `/iflow-doctor`.

| Code | Condition | Severity | Auto-repair |
| --- | --- | --- | --- |
| `multi_focus` | More than one `issue<N>_*` group in `01-current-issues` while focus is ambiguous (no `N-slug` branch) | error | partial — pass `--except N` or switch branch |
| `leftover_in_current` | Issue group in `01` that is not the resolved focus | warn | yes — sweep to `02`/`03` |
| `duplicate_across_folders` | Same issue number in two of `01`/`02`/`03` | error | no — manual merge |
| `done_still_in_current` | Focus issue in `01` with `- [x] Done` | warn | no — run `/iflow-close` |
| `incomplete_group` | `issue<N>_plan` or status file without `issue<N>_original` in that folder | warn | no — run `/iflow-init` |
| `orphan_file` | Unexpected file in a lifecycle folder (allowlist: `cycle_status.md`) | info | no |
| `missing_tree_folder` | Expected `.issueflows/` subfolder absent | info | yes — `mkdir` |

## CLI

```bash
issue-flow doctor              # audit; exit 1 on error-level findings
issue-flow doctor --json
issue-flow doctor --fix        # mkdir + sweep non-focus groups
issue-flow doctor --fix --dry-run --except 47
issue-flow agent audit         # same as doctor (agent fast path)
issue-flow agent repair        # same as doctor --fix
```

Repairs never delete issue markdown — they only create missing folders and
move whole groups using the same rules as `issue-flow agent sweep`.

## Agent skill

`/iflow-doctor` (off-path) runs audit, presents findings, and on confirmation
applies `--fix`. Manual fallback steps live in the skill template when the CLI
is not installed.
