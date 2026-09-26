# Plan — Issue #392: workspace-wide cleanup

Source: https://github.com/jepegit/issue-flow/issues/392

## Goal

Add an opt-in workspace loop for post-merge branch hygiene: a read-only-by-default
`issue-flow workspace cleanup` CLI that reuses the `agent local-branches`
classification per member, plus a `/iflow-cleanup all` skill path whose confirms are
consolidated across members but still split by phase (A1 / A2 / optional B).

## Constraints

- Safety model of [`local-branch-cleanup.md`](../04-designs-and-guides/local-branch-cleanup.md)
  is unchanged: `-d` only for `reachable`; `-D` only for `squash_landed` /
  `merged_pr_divergent`, only behind a **separate** A2 confirm, tip SHA always
  printed; `unique_work` / `skipped` never offered. Never rebase / force-push /
  push default ([`default-branch-diverge.md`](../04-designs-and-guides/default-branch-diverge.md)).
- Workspace CLI conventions from [`multi-repo-workspaces.md`](../04-designs-and-guides/multi-repo-workspaces.md)
  Phase 4/4b: subcommand under `workspace_app`, `_prepare_workspace_members`,
  continue-on-fail, locked members skipped, `--json` payload with
  `ok / workspace_root / members / ok_count / fail_count / skip_count`.
- Skill + command templates are the source of truth (`src/issue_flow/templates/`);
  rendered `.cursor/` copies are refreshed by `issue-flow update`, not hand-edited.
- Default CLI behaviour is classify-only (mirrors `agent local-branches`).
  `--apply` is for non-interactive callers; `-D` additionally needs
  `--yes-delete-squash-landed`.
- `uv` only; tests via `uv run pytest`; lint via `uv run ruff check src/ tests/`.

### Prior art

- `agent.run_local_branches` (`agent.py` ~L593) — the five-bucket classifier.
  **Migrate:** extract a console-free `classify_local_branches(project_root, *,
  fetch, commit_limit) -> dict` and have `run_local_branches` call it, so
  `workspace cleanup` shares the exact code path (AC1 by construction).
- `agent.run_switchback` (~L858) — switch + `pull --ff-only` + `classify_default_sync`
  with dirty-tree refusal and linked-worktree skip. **Mirror** its refusal rules
  for `--apply` A1; do not call it directly (it emits its own payload).
- `agent.run_workspace_git_status` / `run_workspace_git_fetch` (~L4238) — member
  loop skeleton (`_prepare_workspace_members`, locked skip, per-member
  `try/except`, count fields). **Mirror.**
- `gitutils.delete_branch(cwd, branch, force=)`, `switch_branch`, `pull_ff_only`,
  `fetch_prune`, `classify_default_sync`, `list_worktrees`, `remove_worktree`,
  `dirty_paths`, `remote_owner_repo`, `is_linked_worktree` — all reused as-is.
- `agent._dirty_class(paths, issueflows_dir)` — `clean / issueflows_only / mixed`
  classification for the refuse-to-loop gate. **Reuse.**
- `tests/test_workspace_actions.py::_make_members` / `_git_init` and
  `tests/test_agent_local_branches.py` fixtures (squash-landed / unique-work
  branch setups, `_no_gh`). **Reuse** for the new tests.
- Existing skill text already has a "Workspace walk" token paragraph (per-member
  confirms, "There is no mute `workspace cleanup` CLI") — **replace**, not add.
- Toolbox (`00-tools/`): nothing relevant. Graph: `graphify-out/graph.json` absent → skipped.

## Approach

### 1. Refactor: console-free classifier (`agent.py`)

- `classify_local_branches(project_root, *, fetch=True, commit_limit=20) -> tuple[dict, int]`
  returns today's payload and exit code; `run_local_branches` becomes a thin
  emit wrapper. No behaviour change for `agent local-branches`.

### 2. `issue-flow workspace cleanup` (`cli.py` + `agent.run_workspace_cleanup`)

```
issue-flow workspace cleanup [WORKSPACE_DIR] [--json] [--dry-run] [--apply]
                             [--yes-delete-squash-landed] [--no-fetch]
                             [--extra-root PATH ...]
```

Per member (after `_prepare_workspace_members`, plus `--extra-root` paths that
carry a `.issueflows/`; locked members skipped):

1. **Refuse-to-loop gate** → member `skipped: true, reason: <…>`; loop continues:
   - `git rev-parse` fails / not a repo → `not a git repo`
   - no `origin` remote (`remote_owner_repo` is None and `git remote` has no origin) → `missing origin`
   - detached HEAD (`current_branch` is None) → `detached HEAD`
   - `_dirty_class == "mixed"` → `dirty product-code tree` (paths listed).
     `issueflows_only` dirt: classify, but mark `switch_blocked: true` (A1 skips
     `switch`/`pull` for that member, deletes still allowed since they don't touch the tree).
2. `git fetch --prune` (unless `--no-fetch`).
3. `default_sync` = `classify_default_sync(root, fetch=False)` → keep
   `action / class / ahead / behind / ff_possible`.
4. `buckets` = `classify_local_branches(root, fetch=False)` (reachable,
   squash_landed, merged_pr_divergent, unique_work, skipped, tip on each).
5. `worktrees` = linked worktrees (`list_worktrees`, `is_main` false) with
   `branch`, `path`, and the bucket that branch falls in. A linked worktree whose
   branch is `unique_work` is reported under `refusals` (branch never touched);
   the member still proceeds (see Open questions).
6. **Plan** (always computed, even read-only):
   - `a1`: `switch_default` (bool + reason when blocked), `pull_ff_only`
     (only when `default_sync.action in {"even","ff_only"}`; else
     `pull_skipped_reason = default_sync.action`), `worktree_remove: [reachable
     worktrees]`, `branch_d: [reachable names]`.
   - `a2`: `branch_D: [{name, tip, bucket, merged_prs}]` for `squash_landed` +
     `merged_pr_divergent` **only**, each with `recover: "git branch <name> <tip>"`.
7. **Apply** (only with `--apply`, never with `--dry-run`):
   - A1: switch (if not blocked and not already on default) → pull ff-only (if
     planned) → `remove_worktree` (clean, reachable) → `delete_branch(-d)`.
     A `-d` refusal is recorded, never escalated.
   - A2: only with `--yes-delete-squash-landed`: `remove_worktree` (clean) →
     `delete_branch(-d)` first, `-D` on refusal; record `{name, tip, flag}` in
     `deleted`. Without the flag, `a2` stays a plan and `notes` says so.
   - Members that failed the gate or whose default cannot ff are never pulled/pushed.

Payload: `{ok, workspace_root, apply, dry_run, members: [{name, path, ok,
skipped, reason, branch, default_branch, dirty_class, default_sync, buckets,
worktrees, refusals, plan: {a1, a2}, applied: {a1: {...}, a2: {deleted: [...]}},
notes}], ok_count, fail_count, skip_count, totals: {reachable, squash_landed,
merged_pr_divergent, unique_work}}`.

Text render: one table grouped by member — `member  branch  default-sync
action  reachable/squash_landed/merged_pr_divergent/unique_work counts`, then
per member the named branches with tips per bucket, skipped members with their
reason, and a footer "classify-only — pass --apply …" or an apply summary.
Exit 0 when no member failed (skipped members are not failures), else 1.

### 3. Skill: `/iflow-cleanup all` (`templates/skills/iflow_cleanup/SKILL.md.j2` + `templates/commands/iflow-cleanup.md.j2`)

- Replace the "Workspace walk" Input paragraph: tokens `all`, `workspace`,
  `include workspace`; extra `root:<path>` hints → `--extra-root`. Point at the
  new CLI ("classify-only by default"). Self-update once at the start (keep).
- New step **4b — Workspace mode** (used instead of steps 2–6 when the token is
  present):
  1. `issue-flow workspace cleanup --json [--extra-root …]` from the workspace
     root (resolve via `agent resolve` → `workspace_root`); print the grouped table.
  2. **Phase A1 (one confirm for all members)** — list per member: `switch`,
     `pull --ff-only`, worktree removes, `branch -d <reachable…>`. Members with
     `default_sync.action` not in `even`/`ff_only` are listed with that action
     and **skipped** (never pulled/pushed); gate-refused members listed with
     reason. On yes: `issue-flow workspace cleanup --apply --json` (or the
     per-member git commands when the CLI is missing). `cleanup_yes_a1` honoured.
  3. **Phase A2 (second confirm, never implied by A1)** — only when any member
     has `squash_landed`/`merged_pr_divergent`; list per member `<name> <tip>`
     + merged PR, `merged_pr_divergent` separately with unique-commit subjects,
     recovery line. Never `unique_work`/`skipped`. On yes: `issue-flow workspace
     cleanup --apply --yes-delete-squash-landed --json`; report every
     `<name> <tip> <flag>`. `cleanup_yes_a2` honoured; `drive`/`landed` token
     narrows scope exactly as today.
  4. **Phase B** — unchanged enable rule; when on, run `agent branches` per
     member and a **third** confirm grouped by member.
  5. Folder sweep (step 7) and epic gate (step 8) run per member as today.
- Step 10: "each scaffolded repo needs its own `/iflow-cleanup` … — do not loop
  automatically **unless invoked with `all`**"; workspace runs report per member.
- Constraints: add "`--apply` / `--yes-delete-squash-landed` are only ever
  passed after the matching A1 / A2 yes".
- Command template mirrors the same in its terser form.

### 4. Docs

- `.issueflows/04-designs-and-guides/multi-repo-workspaces.md`: rewrite
  "Per-repo cleanup" → "Workspace cleanup (issue #392)"; add Phase 4c section
  (CLI shape, three confirms, refuse-to-loop list, `--apply` flag pairing).
- `docs/cli.md`: table row + `## issue-flow workspace cleanup` section
  (usage, flags, safety notes, exit codes).
- `docs/how-to/workspaces.md`: table row + one-liner in the command block;
  `docs/how-to/after-squash-merge.md`: one sentence pointing at `/iflow-cleanup all`.
- `HISTORY.md` bullet at `/iflow-close`.

### 5. Tests

- `tests/test_workspace_actions.py`:
  - two members with reachable / squash-landed / unique-work branches → `--json`
    buckets equal `agent local-branches --json` run in each member (AC1);
  - member whose default is ahead of origin (non-ff) → `plan.a1.pull_ff_only`
    false with `default_sync.action`, other member still classified (AC3);
  - `unique_work` names never appear in `plan.a1.branch_d` / `plan.a2.branch_D` /
    `applied` (AC4);
  - refuse-to-loop: detached HEAD, mixed-dirty tree, no `origin` → `skipped`
    with reason, loop continues, exit 0;
  - `--apply` deletes reachable with `-d`, leaves squash-landed; adding
    `--yes-delete-squash-landed` deletes it with `-D` and reports `tip`;
    `--dry-run --apply` mutates nothing;
  - `--extra-root` includes a scaffolded repo outside the registry; locked member skipped.
- `tests/test_cli.py`: `workspace --help` lists `cleanup`; `cleanup --help`
  documents `--apply` / `--yes-delete-squash-landed`.
- `tests/test_templating.py`: cleanup skill + command render `workspace cleanup`,
  "unless invoked with `all`", three-confirm wording, `--yes-delete-squash-landed`
  gated on A2; `test_agent_local_branches.py` still green after the refactor.
- Manual: `uv run issue-flow workspace cleanup` from
  `/home/jepe/scripting/issue-flow-workspace` (this repo is the only member).

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/agent.py` | extract `classify_local_branches`; add `run_workspace_cleanup` + text renderer |
| `src/issue_flow/cli.py` | `@workspace_app.command("cleanup")` |
| `src/issue_flow/gitutils.py` | small helpers if missing: `has_remote(cwd, name)`, `is_detached(cwd)` |
| `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2` | workspace mode step, token paragraph, step 10, constraints |
| `src/issue_flow/templates/commands/iflow-cleanup.md.j2` | mirror |
| `docs/cli.md`, `docs/how-to/workspaces.md`, `docs/how-to/after-squash-merge.md` | new command / path |
| `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` | Phase 4c + rewritten cleanup section |
| `tests/test_workspace_actions.py`, `tests/test_cli.py`, `tests/test_templating.py` | new tests |
| `HISTORY.md` | at close |

## Test strategy

`uv run pytest` (full suite) and `uv run ruff check src/ tests/`. New tests use
real temp git repos (as the existing workspace / local-branches tests do) with
`gh` monkeypatched away, so squash-landed detection relies on `git cherry` only.

## Open questions

1. **Linked worktree on a `unique_work` branch** — spec lists it as a
   refuse-to-loop case for the *member*. Recommended: report it under
   `refusals` and still process the member's other branches (the branch itself
   is `unique_work` and can never be offered). Skipping the whole member adds
   friction without adding safety. Literal-spec alternative: skip the member.
2. **`--apply` in v1** — spec asks for it; it is the only part that makes the
   CLI mutate git (precedent: `agent switchback`, `agent worktree-remove`).
   Recommended: ship it as planned (A1 with `--apply`, A2 only with
   `--yes-delete-squash-landed`), because it is what lets the skill do one
   command per phase. Alternative: classify-only CLI now, skill drives
   `git -C <member>` itself, `--apply` in a follow-up.
3. **`issueflows_only` dirt** — treat as *not* product-code dirt: classify and
   delete branches, but skip `switch`/`pull` for that member (recommended), vs.
   refuse the member like `mixed`.
