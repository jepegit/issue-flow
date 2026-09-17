# Epic #269: system-wide settings and update

Anchor: https://github.com/jepegit/issue-flow/issues/269
Status: confirmed

## Goal

A user can keep **one user-global issue-flow config**, **register** the
repos that use issue-flow on this machine, **lock** some of them so
bulk-update leaves them alone (default unlocked), and **refresh every
unlocked stack** in one command. Packaged skills that are not
project-specific can install into the **editor's user-global** skill
dir; project-local skills stay under `<repo>/.cursor/skills/` (local
wins). Done when: (1) a design doc records the contract; (2) lock +
registry + update-all work without a Cursor workspace file; (3) global
vs local skill split is decided and implemented for the default
harness. Not a skillbook clone.

## Constraints

- **Compose.** Reuse `config.toml` / `ISSUEFLOW_*` resolve, `issue-flow
  update`, and `issue-flow workspace update` (sibling workspace members
  only — see [multi-repo-workspaces.md](../04-designs-and-guides/multi-repo-workspaces.md)).
  System-wide is a **new layer above** workspace update, not a fork.
- **Not skillbook.** [skillbook-lessons.md](../04-designs-and-guides/skillbook-lessons.md)
  already cited #269 as “user-global config + update-all + lock” and
  rejected a personal skill library / CLI dependency. Honour #276
  clobber-protect and #277 unmanaged-skill scan when writing globals.
- **`.issueflows/` stays per-repo.** Tracking, epic plans, and project
  knobs do not move to `$HOME`.
- **Local wins.** A project skill dir with the same output name beats
  the user-global copy (editor resolution order, documented).
- **Lock default off.** Unlocked repos are updated; locked ones are
  listed and skipped.
- **Epics decompose into** the normal issue lifecycle (branch + PR).
- Cite: [skill-behaviour-knobs.md](../04-designs-and-guides/skill-behaviour-knobs.md),
  [editor-profiles.md](../04-designs-and-guides/editor-profiles.md),
  [modes.md](../04-designs-and-guides/modes.md).
- Non-goals for this epic: vendoring skillbook; scanning the whole
  disk for git repos; GitLab; making every skill global.

## Stage 1 — Design + skill split

Decide the contract before any user-global writes. Front-loads the
comment’s product questions (which skills are global, Cursor vs
`.claude`, registry vs workspace).
- Goal: merged design doc + skill-split table that later stages can
  implement without re-litigating policy.

### Issue: Design doc — user-global config, lock, registry, update-all

- Spec: Add `.issueflows/04-designs-and-guides/user-global-config.md`
  defining: XDG/user config path (and Windows/WSL note); precedence
  (project `config.toml` > user-global > env > default, or the reverse
  for “system-wide defaults” — pick one and justify); lock key on the
  **project** (`[issueflow] locked = true`, default false); registry
  file (list of roots, how a repo gets registered — `init` / explicit
  `register` / both); `update --all` (or named command) vs
  `workspace update` (workspace file optional); lock skip behaviour;
  interaction with #276 stamps when refreshing a registered repo.
  Cross-link knobs table. Acceptance: design doc merged; knobs table
  row(s); later Stage 2 issues cite it.
- Goal: One doc answers path, precedence, lock, registry, and
  update-all vs workspace.
- Model: deep
- Depends on: none
- yolo: no — policy / path / precedence decisions
- Published: #281

### Issue: Skill split — which packaged stems are global vs project-local

- Spec: Survey `SKILL_DIRS` (lifecycle vs behaviour vs pstack). Write a
  table in the design doc (or a sibling `global-vs-local-skills.md`):
  stem → `global` | `local` | `both` (global install + project override).
  Check whether Cursor user skills live under `~/.cursor/skills/` and
  whether Cursor also reads `~/.claude/skills/` (comment hypothesis —
  verify, do not assume). Record editor-profile implications. No `src/`
  install in this issue. Acceptance: table reviewed; every default
  stem classified; Cursor/Claude global paths verified or marked
  unknown with a follow-up under Later.
- Goal: Agreed stem list + verified (or explicitly unknown) global
  skill paths for Cursor and Claude.
- Model: deep
- Depends on: #281
- yolo: no — classification is a product judgment
- Published: #282

## Stage 2 — Config, lock, registry, update-all

Implement the original issue body on top of the Stage 1 contract.
- Goal: one command refreshes every unlocked registered repo; locked
  repos stay untouched; no workspace.toml required.

### Issue: User-global config file + resolve precedence

- Spec: Implement
  [user-global-config.md](../04-designs-and-guides/user-global-config.md)
  (#281). Read/write the user-global `config.toml` (create-on-first-set).
  Wire `Settings` so preference knobs resolve **project > user-global >
  env > default**. `issue-flow config show|set` grows `--global`. Tests:
  missing file = today’s behaviour; set global; project override.
  Acceptance: round-trip tests; docs in `docs/configuration.md`.
- Goal: `config show --global` and project resolve match the design
  doc’s precedence.
- Model: default
- Depends on: stage 1 issue 1
- yolo: yes — mechanical once the path and precedence are fixed

### Issue: Per-repo lock flag

- Spec: Persist `[issueflow] locked` per
  [user-global-config.md](../04-designs-and-guides/user-global-config.md)
  (#281): project `config.toml` only, default `false`, optional
  `ISSUEFLOW_LOCKED` process override. Bake into `config show`.
  Acceptance: seed + resolve tests; locked project documented.
- Goal: A repo can be marked locked and `config show` reports it.
- Model: fast
- Depends on: stage 2 issue 1
- yolo: yes — existing knob pattern

### Issue: Registry of issue-flowed projects + update-all

- Spec: Persist `registry.toml` per
  [user-global-config.md](../04-designs-and-guides/user-global-config.md)
  (#281). `init` and `issue-flow register` add the current root.
  `issue-flow update --all` walks the registry, skips missing and
  **locked** repos, runs `update` on the rest (forward `--force` /
  `--editor`; honour #276 stamps per root), aggregates like
  `workspace update`. No `issueflow-workspace.toml` required.
  Acceptance: register + update-all tests with one locked and one
  unlocked tmp project; docs/cli.md.
- Goal: `update --all` refreshes unlocked registered repos and skips
  locked ones.
- Model: default
- Depends on: stage 2 issue 2
- yolo: no — new CLI surface, multi-root I/O, failure aggregation

## Later (unstaged)

- Materialize **global** packaged skills on `init` / `update` / first
  install, honouring the Stage 1 table and #276 clobber-protect
  (user-global path).
- If Cursor does **not** read `~/.claude/skills/`, per-editor global
  dirs (Cursor `~/.cursor/skills`, Claude `~/.claude/skills`) instead
  of one shared tree.
- Opt-in disk discovery of `.issueflows/` trees (never default).
- `workspace update` calling through the registry when members are
  also registered (dedupe).
- Windows native paths beyond WSL.
