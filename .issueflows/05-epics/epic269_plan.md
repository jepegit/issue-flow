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
- Depends on: #281
- yolo: yes — mechanical once the path and precedence are fixed
- Published: #285

### Issue: Per-repo lock flag

- Spec: Persist `[issueflow] locked` per
  [user-global-config.md](../04-designs-and-guides/user-global-config.md)
  (#281): project `config.toml` only, default `false`, optional
  `ISSUEFLOW_LOCKED` process override. Bake into `config show`.
  Acceptance: seed + resolve tests; locked project documented.
- Goal: A repo can be marked locked and `config show` reports it.
- Model: fast
- Depends on: #285
- yolo: yes — existing knob pattern
- Published: #286

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
- Depends on: #286
- yolo: no — new CLI surface, multi-root I/O, failure aggregation
- Published: #287

## Stage 3 — User-global skill materialize

Close epic Goal item (3): `both` stems land in the editor's user-global
skill dir as well as the project copy. Local still wins. Honour #276
on the **user-global** tree. No skillbook library.
- Goal: `init` / `update` write `caveman`, `grill-me`, `gh-ci` to the
  verified per-editor global paths; project copies stay; stamps skip
  foreign global dirs unless `--force`.

### Issue: Confirm or skip opencode's user-global skill path

- Spec: #282 left opencode **unknown**. Verify the write target
  (`~/.config/opencode/skills` vs `~/.agents/skills` vs other) from
  current opencode docs / source, or record an explicit **skip** (no
  global writes for opencode until known). Update the editor table in
  [global-vs-local-skills.md](../04-designs-and-guides/global-vs-local-skills.md).
  No `src/` materialize in this issue. Acceptance: table row is
  `verified` or `skip` with a one-line reason.
- Goal: Stage 3 materialize never writes an opencode global path that
  we guessed.
- Model: deep
- Depends on: #282
- yolo: no — product / path judgment
- Published: #292

### Issue: Materialize `both` stems into per-editor user-global skill dirs

- Spec: On `init` / `update` (and each `update --all` member), write
  `both` stems (`caveman`, `grill-me`, `gh-ci`) to the **per-editor**
  user-global path from
  [global-vs-local-skills.md](../04-designs-and-guides/global-vs-local-skills.md)
  (#282): Cursor `~/.cursor/skills/`, Claude `~/.claude/skills/`,
  Codex `~/.agents/skills/`. Opencode: `#292` verified
  `~/.config/opencode/skills/` — write that path (not the compat
  `~/.claude` / `~/.agents` dirs). Keep the project-local copy (no
  `global`-only stems). Honour #276 on the user-global tree: stamps
  live under the user-global issue-flow dir (not
  `.issueflows/agent/skill-stamps.json` of a repo). `--force` on
  `update` / `update --all` is `overwrite_foreign` for those global
  dirs too. Do not write Cursor globals into `~/.claude/skills/`.
  Tests: tmp `HOME` / `XDG`; project copy still present; foreign
  global dir skipped without `--force`. Docs in `docs/configuration.md`
  + the two design docs. Not a skillbook library
  ([skillbook-lessons.md](../04-designs-and-guides/skillbook-lessons.md)).
- Goal: A machine that ran `update` has the three `both` skills in
  the editor global dir, and a project skill of the same name still
  wins.
- Model: default
- Depends on: #292
- yolo: no — home-dir writes, new stamp store, multi-editor I/O
- Published: #293

## Stage 4 — Registry hygiene + platform leftovers

Confirmed 2026-09-18.

Original Goal items (1)–(3) already shipped. This stage burns the
three Later leftovers from
[user-global-config.md](../04-designs-and-guides/user-global-config.md)
without reopening skill placement or lock/registry v1.
- Goal: overlapping workspace+registry roots update once when asked to
  union; discover is opt-in and confirmed; native Windows APPDATA is
  tested as a separate machine view (no WSL→`%USERPROFILE%` reads).

### Issue: Dedupe workspace update and the registry

- Spec: v1 left `workspace update` and `update --all` as different
  sets ([user-global-config.md](../04-designs-and-guides/user-global-config.md)
  / [multi-repo-workspaces.md](../04-designs-and-guides/multi-repo-workspaces.md)).
  Same absolute root in both can be refreshed twice in one session.
  Add a shared unique-by-resolved-path walk. Default command sets stay
  unchanged (`update --all` = registry only; `workspace update` =
  workspace members only). `issue-flow update --all --workspace`
  unions nearest `issueflow-workspace.toml` members with registry
  roots (locked / missing still skip). `workspace update` already
  listed twice in the workspace file updates once. Honour #276 per
  root; `--force` still `overwrite_foreign`. Docs: both design docs +
  `docs/cli.md`. Tests: overlapping tmp root appears once in the
  union; without `--workspace`, `update --all` does not walk the
  workspace file.
- Goal: `--workspace` union updates an overlapping root once; defaults
  stay two separate sets.
- Model: default
- Depends on: #287
- yolo: no — two CLI surfaces, easy to change default sets by accident
- Published: #296

### Issue: Opt-in discover of `.issueflows/` trees

- Spec: Epic constraint forbids a default whole-disk git scan. Add
  `issue-flow register --discover [START]` (START default = cwd): walk
  for directories that already contain the project's issueflows dir
  (bounded depth, no symlink escape), print the candidate list, write
  only after one confirm (or `--yes` in tests). Never run from
  `update --all` / `init` / `workspace update`. Missing / locked roots
  stay skip-and-report. Relative START is resolved; discovered roots
  stored absolute. Docs in `docs/cli.md` + user-global-config.md
  (strike “scanning is Later”). Tests: tmp tree with two scaffolds +
  one decoy; only scaffolds register; depth cap respected.
- Goal: `register --discover` adds only confirmed `.issueflows/`
  roots; `update --all` still never walks the disk.
- Model: default
- Depends on: #287
- yolo: no — disk walk + confirm UX; default-off is a product line
- Published: #297

### Issue: Native Windows APPDATA tests (not a WSL bridge)

- Spec: Contract already says WSL uses the Linux home and a native
  Windows install is a **separate machine view** — do **not** read
  `%APPDATA%` / `%USERPROFILE%` from WSL Python. Remaining work is
  proving the `sys.platform == "win32"` branch
  (`os_config_home` / `user_config_dir` / editor global skills) with
  monkeypatched `sys.platform` + `APPDATA` / `USERPROFILE`, plus a
  short note in `docs/configuration.md` and both design docs. No
  `/mnt/c/Users/…` lookup. No change to Linux/WSL behaviour.
- Goal: win32 APPDATA paths have tests; WSL still ignores Windows
  home.
- Model: fast
- Depends on: #285
- yolo: yes — mechanical tests + docs around an already-shipped branch
- Published: #298

## Later (unstaged)

None. Cross-repo pick / linked issues / workspace status dashboard
stay on [multi-repo-workspaces.md](../04-designs-and-guides/multi-repo-workspaces.md)
(out of this epic).
