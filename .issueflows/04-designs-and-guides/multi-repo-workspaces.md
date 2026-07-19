# Multi-root Cursor workspaces

Context: issue #67 — sibling repositories in one editor workspace each carry their
own `.issueflows/` scaffold; lifecycle commands must not silently target the
wrong repo.

## Recommended layout

- Open a **multi-root workspace** with one folder per repository (e.g.
  `cellpy-core/` and `cellpy/` as siblings).
- Run **`issue-flow init`** in each repo — each gets its own `.issueflows/`,
  `AGENTS.md` block, and `.cursor/rules/issueflow-rules.mdc`.
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

After resolution, use `git -C <project_root> …`, `gh … --repo owner/name`, and
paths under `<project_root>/.issueflows/`.

### Scoped Cursor rules

Scaffolded `issueflow-rules.mdc` uses `alwaysApply: false` and `globs: ["**/*"]`
so each repo's rules apply only when editing files under that root. Re-run
**`issue-flow update`** in each repo to refresh an older always-on rule file.

### Per-repo cleanup

`/iflow-cleanup` runs against **one** project root. When `agent resolve` reports
`sibling_roots`, repeat cleanup in each repo after its PR merges.

## Phase 2 (issue #126) — workspace registry

Implemented as `issueflow-workspace.toml` at the **workspace root** (the folder
containing the member repos), created with **`issue-flow workspace init
[--default <member>]`** or by hand:

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

## Out of scope (follow-ups)

- **Cross-repo `/iflow-pick` ranking** across registry members (Phase 3a).
- **Cross-repo linked issues** — paired issues, shared labels (Phase 3; extends
  #12).
- **Multi-repo status dashboard** — `issue-flow status --workspace` aggregating
  the per-repo payloads across registry members (Phase 4; extends #20).

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
