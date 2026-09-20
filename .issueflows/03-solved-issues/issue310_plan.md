# Plan: #310 Global iflow initialisation

## Goal

Let a user treat a **parent folder of related repos** as one workspace and
bootstrap issue-flow across those members from a **user-global `/iflow-init`**
(plus a CLI engine). First `init`/`update` on a machine still writes the
`both` skills; after that, `iflow init` works even when the current folder
has no project scaffold yet.

## Constraints

- **Compose.** Reuse `issue-flow init`, `issue-flow workspace init`, and
  `register` (already called from `init`). Do not invent a second scaffolder
  or a shared parent `.issueflows/` — rejected in
  [multi-repo-workspaces.md](../04-designs-and-guides/multi-repo-workspaces.md).
- **`/iflow-init` stays harness-only.** No issue capture, no branches. Honour
  [iflow-init-vs-capture.md](../04-designs-and-guides/iflow-init-vs-capture.md).
- **Lifecycle skills stay local — except `iflow-init`.**
  [global-vs-local-skills.md](../04-designs-and-guides/global-vs-local-skills.md)
  made every `iflow_*` stem `local` so versions do not skew. This issue
  carves **one** exception: `iflow_init` becomes `both` so the chicken-egg
  (need the skill to run init; need init to get the skill) is broken.
  `iflow-setup`, `iflow-pick`, and the rest stay `local`.
- **Confirm-gated mutations.** Skill never runs `init` / bootstrap without
  a yes. CLI stays headless (`--yes` for scripts).
- **Enclosing-repo guard.** Reuse the `readiness` / #246 rule: do not treat
  a folder inside another git work tree as its own repo without the user
  saying so.
- **No skillbook.** User-global `iflow-init` is one packaged stem, not a
  personal library ([skillbook-lessons.md](../04-designs-and-guides/skillbook-lessons.md)).

### Prior art

- `issue_flow.cli.workspace_init` / `run_workspace_init` — writes
  `issueflow-workspace.toml` from **already-scaffolded** children only;
  refuses when none exist.
- `issue_flow.init.run_init` — per-repo scaffold, user-global `both`
  materialize, `register_root`.
- `issue-flow register --discover` — finds existing `.issueflows/` trees;
  does **not** init missing ones.
- `issue-flow update --all` / `workspace update` — refresh, not first-time
  bootstrap.
- `/iflow-init` skill (`templates/skills/iflow_init/SKILL.md.j2`) — single
  project; guides `issue-flow init` after confirm.
- `/iflow-setup` + `agent setup-status` — env readiness for **one** new or
  existing project ([novice-onboarding.md](../04-designs-and-guides/novice-onboarding.md)).
- `BOTH_SKILL_STEMS` in `templating.py` + `materialize_user_global_both_skills`
  in `surfaces.py` — current `both` set is `caveman`, `grill_me`, `gh_ci`.
- `discover_issueflow_roots` / `list_scaffolded_siblings` in `project.py`.
- Tests: `tests/test_cli.py` (`test_workspace_init_*`),
  `tests/test_global_both_skills.py`, `tests/test_init.py` (iflow-init is
  not capture).

## Approach

### 1. CLI: `issue-flow workspace bootstrap [DIR]`

New command next to `workspace init` / `workspace update`. From the parent
folder (the common folder in the issue):

1. List **immediate child directories that are their own git top-level**
   (not nested work trees, not random non-git dirs).
2. Classify each: already scaffolded / git-but-unscaffolded / skipped
   (enclosing repo, not a dir).
3. Without `--yes`, print the plan and exit 0 with JSON when `--json`
   (classify-only). With `--yes` (or after the skill's confirm, which
   passes `--yes`):
   - `run_init` each unscaffolded git child (`--skip-dep-check` forwarded).
   - `run_workspace_init` for the parent (members now exist).
   - `--default <name>` required when more than one member and no flag
     (skill asks; CLI fails with the member list).
4. Do **not** write `.issueflows/` on the parent. Do **not** `git init`
   children (that stays `/iflow-setup`).
5. Aggregate ok / skip / fail like `workspace update`. One member failure
   does not abort the rest.

`workspace init` behaviour is unchanged (still requires existing
scaffolds). Bootstrap is the missing first-time path.

### 2. Skill: extend `/iflow-init` (no new slash name)

Add a **workspace / parent-folder** branch before the single-project path:

1. Resolve start dir (`root:` / `-C` / cwd).
2. If `issueflow-workspace.toml` already exists → say so; offer
   `workspace update` / per-member `update`. Do not re-bootstrap unless
   the user asks `--force` / re-init.
3. If the start dir has **two or more** immediate git children (or the
   user said "this folder of repos") → show the classified member list +
   proposed `--default`; on yes run
   `issue-flow workspace bootstrap <dir> --yes --default <name>`.
4. Else keep today's single-project flow (`issue-flow init .` after
   confirm).
5. After success: remind `/iflow-pick` **per repo** (or open the default
   member). Off-path; never auto-dispatch.

### 3. Make `iflow_init` a `both` stem

- Add `iflow_init` to `BOTH_SKILL_STEMS`.
- `materialize_user_global_both_skills` then writes
  `~/.cursor/skills/iflow-init/` (and the other editor globals) on every
  `init` / `update`.
- Update [global-vs-local-skills.md](../04-designs-and-guides/global-vs-local-skills.md):
  lifecycle table stays `local` except `iflow_init` → `both`, with the
  chicken-egg rationale. Local copy still wins inside a repo (version /
  mode-accurate).
- First machine still needs one CLI `init`/`update` (or `uvx issue-flow
  workspace bootstrap`) to plant the global skill. Document that in the
  skill + workflow doc.

### 4. Design-doc touch-ups (same PR)

- `multi-repo-workspaces.md` — bootstrap as the way to go from "folder of
  git siblings" to a workspace file.
- `iflow-init-vs-capture.md` — workspace branch; still not capture.
- `user-global-config.md` — no new knobs; registry still filled by `init`.

## Files to touch

- `src/issue_flow/cli.py` — `workspace bootstrap` command.
- `src/issue_flow/agent.py` — `run_workspace_bootstrap` (classify +
  optional mutate).
- `src/issue_flow/project.py` — helper to list immediate child git
  top-levels (reuse readiness enclosing-repo check if it already exists).
- `src/issue_flow/templating.py` — `BOTH_SKILL_STEMS` includes `iflow_init`.
- `src/issue_flow/templates/skills/iflow_init/SKILL.md.j2` — workspace
  branch.
- `src/issue_flow/templates/commands/iflow-init.md.j2` — same if it
  duplicates instructions.
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — one-line pointer.
- `.issueflows/04-designs-and-guides/global-vs-local-skills.md`
- `.issueflows/04-designs-and-guides/multi-repo-workspaces.md`
- `.issueflows/04-designs-and-guides/iflow-init-vs-capture.md`
- `tests/test_cli.py` — bootstrap classify / `--yes` / refuse no git
  children / default required.
- `tests/test_global_both_skills.py` — `iflow-init` lands in user-global.
- `tests/test_init.py` / `tests/test_templating.py` — skill still not
  capture; `both` list updated.

## Test strategy

`uv run pytest` plus targeted:

- `tests/test_cli.py` — new bootstrap cases (tmp parent with two `git
  init` children; one already scaffolded; `--json` classify-only does not
  write; `--yes` inits + writes toml; no parent `.issueflows/`).
- `tests/test_global_both_skills.py` — `iflow-init` in
  `editor_user_global_skills_root("cursor")`.
- Existing `test_workspace_init_*` still pass (bootstrap ≠ init).
- `uv run ruff check src/ tests/`.

## Open questions

1. **Slash name.** Recommend **extend `/iflow-init`** (matches the issue
   title). Alternative: new `/iflow-workspace` — only if you want init to
   stay single-repo forever.
2. **`iflow-init` as `both`.** Recommend **yes** (chicken-egg). Alternative:
   leave it `local` and only document `uvx issue-flow workspace bootstrap`
   — weaker "global skill".
3. **Children that are not git repos.** Recommend **skip** (point at
   `/iflow-setup` per folder). Alternative: bootstrap may `git init` empty
   dirs behind a second confirm — out of scope unless you want it.
4. **Split / epic.** This is one PR if the answers above stand. Split only
   if you want a design-doc issue first.
