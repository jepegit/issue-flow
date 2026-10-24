# Issue #409: verify_scaffold.py is stale since #406 (38 checks fail on main)

Source: https://github.com/jepegit/issue-flow/issues/409

## Original issue text

## Problem / context

`.issueflows/00-tools/verify_scaffold.py` is the end-to-end render check the toolbox README tells agents to run before merging template changes. It still expects the pre-#406 surface, so it reports **38 failed checks on a clean `main`** and no longer catches real regressions. Found while verifying #268.

The failures fall into these groups:

- **Retired claude command files** (`.claude/commands/iflow-pick.md`, `iflow-close.md`, `iflow-build.md`, `iflow-yolo.md`, `iflow-ops.md`). About 22 checks.
- **Retired skill folders.** `iflow-yolo`, `iflow-ops` and, in the novice group, `iflow-capture` are now modes (`iflow-run yolo`, `iflow-close ops`, `iflow-pick capture`).
- **Markers moved from `SKILL.md` into mode files** in `iflow-close` / `iflow-pick`: `Ops close path`, `--squash --auto`, `publish-intent`, `Publish-on-success label`, `gh pr create --draft`, `Unslop (pstack, optional)`, `Label-driven yolo/ops flow`.
- **Changed rule body sections:** `### pstack skills`, `` **`unslop`** ``, and the `/iflow-setup` line in the novice rule.

## Spec

- Update every expected path and marker to the merged eleven-command surface. Point at the router `SKILL.md` or the right mode file (`ops.md`, `merge.md`, `version.md`, …), and assert the absence of retired names instead of their presence.
- Where a marker no longer exists, assert the current equivalent wording or drop the check, with a one-line reason in the commit.
- Consider deriving the expected file list from `COMMANDS` / `skill_side_templates()` in `templating.py` instead of hard-coding paths, so the next surface change can't silently rot it.

## Acceptance criteria

- `uv run .issueflows/00-tools/verify_scaffold.py` exits 0 on `main`.
- Reintroducing a known regression still fails. For example, removing `ops.md` from `iflow-close` or dropping the label-flow text from `pick` makes it exit non-zero.
- The `00-tools/README.md` entry still describes what the tool checks.
