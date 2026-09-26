# Multi-root Cursor workspaces

User-facing recipe: [docs/how-to/workspaces.md](../../../docs/how-to/workspaces.md)
(issue #313).

Context: issue #67 — sibling repositories in one editor workspace each carry their
own `.issueflows/` scaffold; lifecycle commands must not silently target the
wrong repo.

## Recommended layout

- Open a **multi-root workspace** with one folder per repository (e.g.
  `cellpy-core/` and `cellpy/` as siblings).
- Run **`issue-flow init`** in each repo — each gets its own `.issueflows/`,
  `AGENTS.md` block, and `.cursor/rules/issueflow-rules.mdc`.
- **First-time folder of git siblings:** from the parent folder run
  **`issue-flow workspace bootstrap --yes --default <member>`** (or type
  `iflow init` / `/iflow-init` and confirm). That inits unscaffolded own-git
  children, then writes `issueflow-workspace.toml`. Classify-only (no
  `--yes`) prints the plan. Non-git folders are skipped — use
  `/iflow-setup` per folder if they still need `git init`. The parent never
  gets a shared `.issueflows/`.
- To refresh packaged skills/rules/commands after upgrading issue-flow, run
  **`issue-flow workspace update`** from the workspace root (or any member —
  it walks up for `issueflow-workspace.toml`). Per-repo **`issue-flow update`**
  remains valid when you only need one member.
- Put **repo-specific toolchain** instructions in each repo's
  `.issueflows/04-designs-and-guides/this-project.md` (conda vs uv, test
  commands, etc.) so merged agent context stays disambiguated.

## Phase 1 (issue #67) — resolution contract

Before any lifecycle command touches `git`, `gh`, or `.issueflows/`:

1. Explicit slash hints: `root:<path>`, `repo:<folder-basename>`, or
   `repo:owner/name`.
2. CLI: `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`
3. Exactly one repo on an issue-style branch (`^\d+-`) → that root.
4. Exactly one `.issueflows/` in the workspace → that root.
5. **Ambiguous → ask**; never guess.

After resolution, use `git -C <project_root> …`, an explicit repo on every `gh`
call, and paths under `<project_root>/.issueflows/`. Most `gh` commands take
`--repo owner/name`; **`gh repo view` is the exception** — repo is positional
(`gh repo view owner/name …`). Do not write `gh repo view --repo …` (rejected
flag; issue #216).

### Scoped Cursor rules

Scaffolded `issueflow-rules.mdc` uses `alwaysApply: false` and `globs: ["**/*"]`
so each repo's rules apply only when editing files under that root. Re-run
**`issue-flow update`** in each repo to refresh an older always-on rule file.

### Per-repo cleanup

`/iflow-cleanup` runs against **one** project root by default. Trailing
`all` / `workspace` / `include workspace` switches to workspace mode
(Phase 4c below). When `agent resolve` reports `sibling_roots` and no
workspace token was passed, remind the user to repeat cleanup per repo or
run `/iflow-cleanup all` — never loop without the token.

## Phase 2 (issue #126) — workspace registry

Implemented as `issueflow-workspace.toml` at the **workspace root** (the folder
containing the member repos), created with **`issue-flow workspace bootstrap`**
(first-time git siblings) or **`issue-flow workspace init [--default <member>]`**
(members already scaffolded), or by hand:

```toml
[workspace]
default = "cellpy"                 # the "parent repo" (must be a scaffolded member)
members = ["cellpy", "cellpy-core"]  # optional; auto-discovered when omitted
```

- The `default` member fills the **bottom** of the resolution order only: it
  replaces the final "stop and ask" step when a command runs from outside any
  scaffold (typically the workspace root). Explicit hints, the nearest
  scaffold, and the branch heuristic all still win.
- `issue-flow agent resolve --json` reports `workspace_root`,
  `workspace_default`, `workspace_members`, and
  `resolved_via_workspace_default`.
- A `default` that is not a scaffolded member is ignored (reported as a
  warning) so a typo can never redirect git operations.
- A single shared top-level `.issueflows/` remains rejected (see below): issue
  numbers are a per-repo namespace, the lifecycle is per-repo regardless, and
  archive recovery depends on tracking files being committed in their repo.
- `issue-flow update --all --workspace` (from a path under the workspace)
  unions these members with the user-global registry, unique by resolved
  path — see [user-global-config.md](./user-global-config.md) (#296).
  Default `update --all` still ignores this file.

## Phase 4 (issue #318) — workspace inspect

Shipped as `issue-flow workspace status|doctor|dirty` (subcommands, not a
flag on the single-repo commands). Same continue-on-fail loop as
`workspace update`. Locked members are skipped. `doctor` is audit-only;
`--fix` stays per-repo. After `workspace update`, `workspace dirty`
classifies each tree so agents can land scaffold dirt without guessing
cwd. Auto-commit / auto-push after update is a follow-up.

## Phase 4b (issue #381) — workspace git

`issue-flow workspace git status` (default verb) is a **git** snapshot
per member: branch, dirty paths, ahead/behind vs `origin/<default>`. It
does **not** fetch. `issue-flow workspace git fetch` is `git fetch
--prune` only. No pull, rebase, merge, or push. Agent path:
`/iflow-workspace-git` (`iflow git`). Distinct from `workspace status`
(issue-flow lifecycle) and `workspace dirty` (post-update dirt class).

## Phase 4c (issue #392) — workspace cleanup

Context: a day of epic work across 3–5 members left 17 `squash_landed` +
4 `merged_pr_divergent` branches; the old "walk" ran the full skill per
member, so five A1 + five A2 confirms for one decision.

**Decision.** `issue-flow workspace cleanup` is the CLI half; the skill's
`all` token consumes it. Confirms are **consolidated across members but
still split by phase**: one A1, one A2, optional one B — at most three.

- **Shared classifier.** `agent.classify_local_branches` is the
  console-free core of `agent local-branches`; `workspace cleanup` calls
  it per member, so buckets are identical by construction (AC1).
- **Classify-only default.** Same posture as `agent local-branches`.
  `--apply` runs Phase A1 (`switch`, `pull --ff-only` only when
  `default-sync` says `even` / `ff_only`, reachable worktree removes,
  `-d` on `reachable`). `-D` on `squash_landed` / `merged_pr_divergent`
  additionally needs `--yes-delete-squash-landed`. `--dry-run` overrides
  both. The skill passes those flags only *after* the matching yes.
  Precedent for a mutating CLI step: `agent switchback`,
  `agent worktree-remove`.
- **Refuse-to-loop** (member reported and skipped, loop continues):
  no `origin`, detached HEAD, dirty product-code tree (`mixed`), locked,
  not a repo. `issueflows_only` dirt is *not* a refusal — it only blocks
  that member's `switch` / `pull` (deletes never touch the tree).
- **Non-ff default** is not a refusal either: the member is listed with
  its `default-sync` `action`, never pulled / rebased / pushed, and its
  `-d` deletes still run (AC3).
- **Linked worktree on `unique_work`** is recorded under `refusals` for
  the member, not a member skip: the branch can never be offered anyway,
  and blocking the other landed branches adds friction without safety.
- **Payload** per member: `default_sync`, `buckets` (five), `worktrees`
  (with bucket + clean flag), `plan.a1` / `plan.a2` (with `recover`
  lines), and after `--apply` an `applied` block listing every
  `<name> <tip> <flag>`.
- **Extra roots.** `--extra-root <path>` / `root:<path>` includes a
  scaffolded repo outside the registry; unregistered siblings stay out.

Alternatives considered: keep the per-member walk (rejected — the confirm
count was the complaint); skill drives `git -C <member>` with no `--apply`
(rejected — one command per phase is what makes the consolidated confirm
cheap and auditable); refuse `issueflows_only` members like `mixed`
(rejected — doctor repairs routinely leave that dirt and it is unaffected
by branch deletes).

## Out of scope (follow-ups)

- **Cross-repo `/iflow-pick` ranking** across registry members (Phase 3a).
- **Cross-repo linked issues** — paired issues, shared labels (Phase 3; extends
  #12).
- **`workspace land`** — confirm + commit (chore branch on default) of
  `issueflows_only` dirt after `workspace update`.

## Separate editor windows (execution layout)

When parallel agents or heavy concurrent work on sibling repos would mix
rules/cwd in one multi-root window, open **one editor workspace per member
or worktree** instead. Registry + `agent resolve` stay unchanged — see
[separate-workspaces.md](./separate-workspaces.md) (issue #253) and
`issue-flow agent open-workspace`.

## Manual cross-repo work (until Phase 3)

For paired changes (engine + consumer):

1. Create matching GitHub issues in each repo; cross-reference in bodies.
2. Use the same label/milestone in each repo manually.
3. Run `/iflow-init`, `/iflow-plan`, `/iflow-build`, `/iflow-close` **per repo**
   with explicit `root:` or `repo:` hints (or resolve via active file).

## Alternatives considered

- **Single top-level `.issueflows/` for the whole workspace** — rejected; breaks
  the one-repo-one-tracker model and git remotes.
- **Always-on rules with repo prefixes only** — insufficient; toolchain conflicts
  still merge. Path-scoped `.mdc` is the primary fix.
