# Issue #392: feat: workspace-wide cleanup (`issue-flow workspace cleanup` / `/iflow-cleanup all`)

Source: https://github.com/jepegit/issue-flow/issues/392

## Original issue text

## Context

In a multi-root workspace (\`issueflow-workspace.toml\`), a day of Epic work leaves squash-landed branches in 3–5 sibling repos. Today \`/iflow-cleanup\` is strictly per-repo — step 10 of the skill says "each scaffolded repo needs its own \`/iflow-cleanup\` — do not loop automatically". The workspace CLI has read-only/non-destructive members only (\`workspace status|doctor|dirty|update|git status|git fetch\`).

Real example (2026-09-26, cellpy + batbase workspaces): 5 repos, 0 \`reachable\`, 17 \`squash_landed\`, 4 \`merged_pr_divergent\`, 2 \`unique_work\` branches. Five separate skill invocations, each with its own A1 + A2 confirm, to do the same thing.

## Spec

Add an opt-in workspace loop that reuses the existing classification (\`issue-flow agent local-branches\`) and keeps the safety model intact:

- **CLI:** \`issue-flow workspace cleanup [--json] [--dry-run]\` — for every scaffolded member: \`git fetch --prune\`, \`default-sync\` classification, \`local-branches\` buckets, linked-worktree list. Output one table grouped by member. Read-only unless \`--apply\` (see below).
- **Skill:** \`/iflow-cleanup all\` (or trailing \`workspace\` token) → runs the loop. Confirms are **consolidated across members but still split by phase**:
  - Phase A1 (one confirm): per member \`switch <default>\`, \`pull --ff-only\`, \`branch -d <reachable…>\`. Members whose default cannot fast-forward are listed with the \`default-sync\` \`action\` and skipped, never pulled/pushed.
  - Phase A2 (second confirm, never implied by A1): per member the \`squash_landed\` and \`merged_pr_divergent\` lists with \`<name> <tip>\` + merged PR, recovery line \`git branch <name> <tip>\`. \`unique_work\` never offered.
  - Phase B (GitHub remote audit) stays opt-in per today's tokens; if enabled, a third confirm, grouped by member.
- **Refuse-to-loop cases** (report and skip that member, continue with the rest): dirty product-code tree, detached HEAD, branch currently checked out in a linked worktree with unique work, missing \`origin\`.
- Members outside the registry (e.g. a repo in a *different* workspace root) are out of scope; accept extra \`root:<path>\` hints to include them.
- \`--apply\` on the CLI is only for non-interactive callers and must require an explicit \`--yes-delete-squash-landed\` for the \`-D\` bucket; default CLI behaviour is classify-only, mirroring \`agent local-branches\`.

## Acceptance criteria

- [ ] \`issue-flow workspace cleanup --json\` returns per-member buckets identical to running \`agent local-branches\` in each member.
- [ ] Skill \`/iflow-cleanup all\` performs at most three confirms for the whole workspace (A1, A2, optional B) and reports tip SHAs for every \`-D\`.
- [ ] A member with non-ff default is skipped with the \`default-sync\` classification printed; the other members are still processed.
- [ ] \`unique_work\` branches are never listed in any confirm.
- [ ] Docs: \`multi-repo-workspaces.md\` and the cleanup skill mention the new path; the "do not loop" sentence in step 10 becomes "…unless invoked with \`all\`".
