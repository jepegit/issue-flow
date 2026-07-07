# Multi-root Cursor workspaces

Context: issue #67 — sibling repositories in one editor workspace each carry their
own `.issueflows/` scaffold; lifecycle commands must not silently target the
wrong repo.

## Recommended layout

- Open a **multi-root workspace** with one folder per repository (e.g.
  `cellpy-core/` and `cellpy/` as siblings).
- Run **`issue-flow init`** (or `update`) **in each repo** — each gets its own
  `.issueflows/`, `AGENTS.md` block, and `.cursor/rules/issueflow-rules.mdc`.
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

## Out of scope (follow-ups)

- **`workspace.toml` registry** — central list of roots; cross-repo `/iflow-pick`
  ranking (Phase 2).
- **Cross-repo linked issues** — paired issues, shared labels (Phase 3; extends
  #12).
- **Multi-repo status dashboard** — single view across roots (Phase 4; extends
  #20).

## Manual cross-repo work (until Phase 3)

For paired changes (engine + consumer):

1. Create matching GitHub issues in each repo; cross-reference in bodies.
2. Use the same label/milestone in each repo manually.
3. Run `/iflow-init`, `/iflow-plan`, `/iflow-start`, `/iflow-close` **per repo**
   with explicit `root:` or `repo:` hints (or resolve via active file).

## Alternatives considered

- **Single top-level `.issueflows/` for the whole workspace** — rejected; breaks
  the one-repo-one-tracker model and git remotes.
- **Always-on rules with repo prefixes only** — insufficient; toolchain conflicts
  still merge. Path-scoped `.mdc` is the primary fix.
