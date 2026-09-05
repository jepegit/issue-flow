# Plan — Issue #243: `/iflow-cleanup` cannot prune squash-merged branches

## Goal

Make `/iflow-cleanup` actually prune local branches in a squash-merge repo:
classify locals deterministically (`reachable` / `squash_landed` /
`merged_pr_divergent` / `unique_work` / `skipped`), allow `git branch -D` for
**verified-landed** branches behind a dedicated confirm that lists tip SHAs,
and fix the docs that currently promise something `-d` cannot do.

## Constraints

- **Templates are the source of truth** (`src/issue_flow/templates/`), and the
  skill/command pair must stay in parity. Re-render this repo's own copies with
  `issue-flow update .` during build.
- **This relaxes a shipped safety rule.** "Never `git branch -D`" is currently
  stated in the cleanup skill, the cleanup command, `rules/_body.md.j2`, the
  yolo skill/command ("no `-D`"), and the workflow doc. Every scaffolded
  project inherits the new wording, so the relaxation must be narrow and
  explicit: `-D` only for branches proven landed, only after its own confirm,
  never from yolo/cycle/auto chains, never for `unique_work`.
- **Deletes stay in the skill, not the CLI** — the [#163
  decision](../04-designs-and-guides/github-branch-audit.md) (§4) that the
  helper is read-only and confirm-gated actions live in the skill still holds.
- Recoverability is part of the contract: print `name  <tip-sha>` before any
  `-D` so `git branch <name> <sha>` restores it.
- Python 3.13 / `uv`; `uv run pytest`, `uv run ruff check src/ tests/`.

### Prior art

- **`agent branches` / `run_branches`** (`agent.py` L235–410) — the remote
  audit from #163 does exactly this shape of work: bucketed payload, `notes`,
  read-only, text renderer. The local classifier should **mirror** it and share
  the PR-splitting helper `_pr_bucket` (L209) rather than re-deriving buckets.
- **`.issueflows/04-designs-and-guides/github-branch-audit.md`** — records the
  bucket rules, the two-confirm split, and "deletes stay in the skill". The new
  local behaviour must not contradict it. **Follow.**
- **`gitutils`** already has `list_origin_branches`, `cherry_unique_count`,
  `unique_commit_onelines`, `unique_diff_shortstat`, `gh_prs_for_head`,
  `branch_is_protected`. **Gotcha:** `cherry_unique_count` and
  `unique_commit_onelines` hardcode `origin/<branch>`, so they cannot compare a
  *local* branch as-is — they need generalizing to explicit refs (see Approach).
- **`gitutils.repo_root` / `rebase_*` / `unmerged_paths`** — added in #240;
  nothing to reuse here beyond the `_run`/`_stdout` idiom.
- **`tests/test_template_cli_consistency.py`** auto-pins any new
  `issue-flow agent <sub>` string in a template against the Typer app.
- **`tests/test_agent_sync_branch.py`** (#240) — the pattern for real-temp-repo
  integration tests (`_git` helper, `GH` monkeypatched off PATH,
  `pytestmark` skip when git is missing). **Mirror** it for the squash fixture.
- **Graph:** `graphify query` returned only `docs/issue-workflow.md` section
  nodes and unrelated workspace-test nodes — no code edges into cleanup, so
  nothing extra surfaced.
- **`.issueflows/00-tools/`** — only `verify_scaffold.py`; nothing reusable.

## Approach

### A. Generalize two `gitutils` comparators

`cherry_unique_count(cwd, default, branch)` and
`unique_commit_onelines(cwd, default, branch)` currently build
`origin/<default>` / `origin/<branch>` internally. Change both to take
**explicit refs** (`base_ref`, `target_ref`) and update the two `run_branches`
call sites to pass `f"origin/{default}"` / `f"origin/{name}"`. Same for
`unique_diff_shortstat`. This is the smallest change that lets one classifier
serve both local and remote branches; `tests/test_gitutils.py` argv assertions
get updated with it.

Add:

- `list_local_branches(cwd)` — `git for-each-ref refs/heads`.
- `is_ancestor(cwd, ref, upstream)` — `git merge-base --is-ancestor`, the
  reachability test `-d` itself uses (exit 0 / 1 / `None` on error).
- `branch_tip(cwd, branch)` — short SHA for the recovery line.
- `delete_branch(cwd, branch, *, force=False)` — `git branch -d|-D`,
  returning `(ok, error)` like the other mutating wrappers.
- `gh_prs_by_head(cwd, repo, *, limit=100)` — **one** `gh pr list --state all
  --json number,title,state,url,mergedAt,headRefName` call, indexed by head.
  `run_branches` makes one `gh` call *per branch*; for 15 local branches that
  was ~20 s tonight. One call keeps the new command fast.

### B. New `issue-flow agent local-branches [--json] [--no-fetch]`

`agent.py: run_local_branches`, registered on `agent_app`. Read-only. For each
local branch except the current one and the default:

| Bucket | Rule |
|---|---|
| `reachable` | `is_ancestor(branch, origin/<default>)` → plain `-d` works today |
| `squash_landed` | not reachable, but `git cherry` reports **0** unique commits → provably nothing to lose |
| `merged_pr_divergent` | not reachable, has unique commits, **and** a merged PR exists for that head → landed logically, but the tip differs from what was squashed |
| `unique_work` | unique commits and no merged PR (or an open PR) |
| `skipped` | current branch, default branch, protected, or comparison failed |

Every entry carries `name`, `tip` (short SHA), `reason`; the divergent and
unique buckets also carry `unique_commits`, `commits` (onelines, capped), and
`shortstat` so the skill can show the user what would be lost. Exit 0 on a
successful classification, 1 only when git is missing or locals cannot be
listed.

`merged_pr_divergent` exists because tonight's run produced exactly it:
`137-epic-publish` (PR #147), `138-epic-status-cli` (#148) and
`237-doctor-editor-scaffold` (#238) all had merged PRs *and* non-equivalent
patches. Folding them into `squash_landed` would delete on a weaker proof;
folding them into `unique_work` would strand them forever.

### C. Cleanup skill/command rewiring

Phase A step 4 becomes two prompts instead of one:

1. **Confirm A1 (unchanged in spirit)** — `git switch <default>`,
   `git pull --ff-only`, `git fetch --prune`, and `git branch -d` for every
   `reachable` branch.
2. **Confirm A2 (new, only when the classifier found any)** — lists
   `squash_landed` branches as `name  <tip-sha>` plus, separately,
   `merged_pr_divergent` branches with their unique-commit subjects and PR
   links, and states plainly that these need `git branch -D` because a squash
   merge leaves no reachable tip. On yes, delete **only** the listed names and
   report the recovery line for each. Declining leaves every branch.
   `unique_work` is never offered here.

Fast path: `issue-flow agent local-branches --json`; manual fallback documented
with `git merge-base --is-ancestor` + `git cherry` + `gh pr list`.

### D. Documentation truth-up

Every place that claims `-d` covers squash merges gets corrected, and the
`-D` prohibition narrowed to "not without the A2 confirm":

- `skills/iflow_cleanup/SKILL.md.j2` — frontmatter description, step 4,
  constraints.
- `commands/iflow-cleanup.md.j2` — intro (L7), step (L49), constraints (L81).
- `rules/_body.md.j2` — lifecycle bullet (L133) and branch-hygiene bullet
  (L264).
- `docs/issue-workflow.md.j2` — pitfalls (L91) and cleanup section (L259).
- `skills/iflow_yolo/SKILL.md.j2` + `commands/iflow-yolo.md.j2` — "no `-D`"
  becomes "never the A2 force-delete confirm" (chains must not force-delete).
- `docs/cli.md` — document `agent local-branches`.
- New design doc `04-designs-and-guides/local-branch-cleanup.md`, cross-linked
  from `github-branch-audit.md`.

## Files to touch

| Path | Change |
|---|---|
| `src/issue_flow/gitutils.py` | generalize the three comparators to explicit refs; add `list_local_branches`, `is_ancestor`, `branch_tip`, `delete_branch`, `gh_prs_by_head` |
| `src/issue_flow/agent.py` | **new** `run_local_branches` + text renderer; pass explicit refs from `run_branches` |
| `src/issue_flow/cli.py` | register `agent local-branches`; update the `agent_app` help |
| `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2` | classifier fast path, A1/A2 confirms, constraints, description |
| `src/issue_flow/templates/commands/iflow-cleanup.md.j2` | parity |
| `src/issue_flow/templates/rules/_body.md.j2` | two `-D` claims |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | pitfalls + cleanup section |
| `src/issue_flow/templates/skills/iflow_yolo/SKILL.md.j2`, `templates/commands/iflow-yolo.md.j2` | chains never force-delete |
| `tests/test_agent_local_branches.py` | **new** — temp repo with a real `git merge --squash`: reachable / squash_landed / merged_pr_divergent / unique_work / skipped |
| `tests/test_gitutils.py` | updated argv assertions + new helpers |
| `tests/test_init.py` | scaffold assertions: A2 confirm wording, tip-SHA recovery line, no stale `-d`-covers-squash claim |
| `docs/cli.md` | `agent local-branches` row + `--json` note |
| `.issueflows/04-designs-and-guides/local-branch-cleanup.md` | **new** design record |
| `.issueflows/04-designs-and-guides/github-branch-audit.md` | cross-link |
| `HISTORY.md` | `[Unreleased]` bullet (at close) |

## Test strategy

- `uv run pytest`; `uv run ruff check src/ tests/`.
- **Integration (real git, mirroring #240's fixture):** build an upstream +
  clone, then produce one branch of each kind — a fast-forward-merged branch
  (`reachable`), a `git merge --squash`-landed branch (`squash_landed`), a
  squash-landed branch with an extra amended commit plus a faked merged-PR
  lookup (`merged_pr_divergent`), an untouched branch with real work
  (`unique_work`), and the current/default branches (`skipped`). Assert the
  payload buckets and that the command **deletes nothing**.
- **`gh` isolation:** monkeypatch `gitutils.GH` off PATH for the git-only
  cases, and stub `gh_prs_by_head` for the PR-dependent bucket, so tests never
  need network or auth.
- Manual smoke: run `issue-flow agent local-branches` in this repo (currently
  `main` + `review-improvements`, which must land in `unique_work`), and
  scaffold a throwaway project to eyeball the rendered cleanup skill.

## Open questions

1. **Keep `merged_pr_divergent` as its own bucket?** *Recommend yes* — it is
   what tonight's run actually produced, and collapsing it either deletes on
   weaker proof or strands the branches. Cost: a fifth bucket and a longer A2
   prompt.
2. **New `agent local-branches` vs `--local` on `agent branches`?**
   *Recommend the new command.* The payload shapes differ (`reachable` /
   `squash_landed` vs `deletable`), and the rendered skills already in the wild
   consume today's `agent branches` payload — extending it risks breaking them
   for a cosmetic saving.
3. **Should the CLI ever delete (e.g. `--delete --force`)?** *Recommend no*,
   per #163 §4: the helper stays read-only and the confirm-gated delete stays
   in the skill.
4. **Retrofit `run_branches` to the batched `gh_prs_by_head`?**
   *Recommend not in this issue* — it is a behaviour-neutral speedup to
   already-shipped code; note it as a follow-up rather than widening the diff.
5. **Are you comfortable relaxing the shipped "never `-D`" rule?** *Recommend
   yes, as scoped above* (verified-landed only, dedicated confirm, tip SHAs
   printed, never from yolo/cycle/auto). This is the one decision that changes
   behaviour for every project issue-flow scaffolds, not just this repo.
