---
name: iflow-cycle
description: >-
  Process many issues hands-off in a row: resolve a queue, then run each
  through the yolo chain under one up-front confirm. Stops only when input is
  strictly necessary.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — issue cycle (`/iflow-cycle`)

Follow this skill to **process a queue of issues hands-off**, one after another, with a **single up-front confirmation** — the batch equivalent of `/iflow-yolo`. Each issue runs the full yolo chain (`init → plan → start → close yolo`, PR auto-merged, switch back to default); the cycle interrupts you only when input is **strictly necessary**.

Use only when every queued issue is genuinely yolo-fit (small, low-risk, well-specified, test-guarded). A queue of risky changes belongs in the individual commands.

## Input — queue spec

- **explicit numbers** — e.g. `12 15 18`.
- **`label:<L>`** — every open issue carrying label `<L>`.
- **`epic <N> [stage <k>]`** — the current stage of epic `<N>` (or stage `<k>`).
- **`resume`** — reserved for the resumable cycle (a later slice); not yet available.
- **`max:<n>`** — raise the safety cap (default 10) for this run.
- **`stay`** — forward `stay` to each close so the working copy stays on each issue branch (rarely wanted in a cycle).


**Invoke:** type `iflow cycle` in chat, or `/iflow-cycle` from the slash menu (`iflow-cycle` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands. When the answer came from the workspace registry, the payload sets `resolved_via_workspace_default: true`.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Workspace default** — an `issueflow-workspace.toml` at the workspace root (created with `issue-flow workspace init`) may name a `default` member repo; use it when no scaffold matched above. Tell the user the default was used.
6. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** always `gh … --repo <owner/repo>` — never rely on `gh`'s implicit cwd default.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Instructions

1. **Resolve the queue.** Run `issue-flow agent queue <spec> --json` (numbers, `--label`, or `--epic`). Use its `queue` (ordered), `blocked`, and `skipped_closed` output as the source of truth — do not re-derive the order by hand. If it reports a dependency `cycle`, **stop** and show it; nothing runs. If the CLI is unavailable, fall back to reading the issues and ordering by `Depends on #N` lines yourself, but prefer the CLI.

2. **Cap check.** If the ordered queue is longer than **10** and the input did not pass `max:<n>` raising the limit, **stop** and ask the user to confirm a larger run explicitly. Long unattended runs compound risk.

3. **One consolidated confirm** (the only planned interruption). Present, in normal prose:
   - the **ordered** queue (numbers + titles), and which issues are **skipped** (closed) or **blocked** (open dependency outside the queue) with the reason;
   - that each issue runs the **full yolo chain** and its PR is **auto-merged**;
   - the failure policy (**stop on the first failure** — see below);
   - the default-branch preflight that must hold before starting (clean tree, tests passing).
   Require an explicit yes; anything else aborts before any work.

4. **Per-issue loop.** For each issue in order, from a clean default branch:
   - create/switch to its `<N>-<slug>` branch, then follow `.cursor/skills/iflow-yolo/SKILL.md` **verbatim** — including its own preflight (refuse on default branch, refuse with dirty unrelated changes, tests pass up front) and its consolidated-confirm step, which the up-front batch confirm in step 3 satisfies (do not re-ask per issue).
   - after the yolo close merges and switches back to the default branch, record the outcome (PR URL, merge result) and continue to the next issue.
   - Every yolo safeguard stays in force. A safeguard that trips is a **stop condition** (step 5), never a guard to skip.

5. **Strictly-necessary-input rule.** Between issues the cycle runs unattended. **Stop and ask only** when:
   a. tests or lint fail in a way you cannot fix within the current issue's scope;
   b. a merge is refused or a `git pull --ff-only` will not fast-forward (divergence);
   c. the issue spec is ambiguous, contradictory, or turns out **not** small (yolo's scope check aborts);
   d. an action would fall **outside the confirmed queue** (touching an unlisted issue, an unrelated dirty file, a destructive op).
   Anything else — routine implementation choices, passing tests, clean merges — proceeds without asking.

6. **Failure policy (default: stop).** On the first stop condition, **halt the cycle**: finish no further issues, leave the repo on the **default branch, clean** (the in-flight issue's branch stays as-is for the user to inspect), and report. Do not attempt the rest of the queue. (A skip-and-continue policy, `onfail:skip`, is a later slice.)

7. **Batch report.** Summarize the whole run: per issue — number, title, PR URL, merge result (merged / queued via `--auto` / not reached), and duration if tracked; then the queue items **skipped** (closed), **blocked** (with blockers), and — on a halt — the **stop reason** and which issues were **not reached**. End by reminding the user to run `/iflow-cleanup` once to prune the merged local branches.

## Constraints

- **Off-path**: `/iflow` never auto-dispatches to `/iflow-cycle`; it is an explicit, deliberate batch action.
- Never weaken a yolo safeguard to keep the cycle moving — safeguards are stop conditions, not obstacles.
- Never run `/iflow-cleanup` from this skill; batch branch deletion still needs the user to see the merged PRs first.
- One consolidated confirm covers the batch; never silently expand the queue beyond what was confirmed.
