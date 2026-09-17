# Skillbook lessons (issue #275)

Context: [kurochenko/skillbook](https://github.com/kurochenko/skillbook)
(MIT, Bun/TS CLI). Surveyed `master` on 2026-09-17 (shallow clone). This note
is the durable record of what we learned and what we chose to steal. Follow-up
implementations live on the GitHub issues listed at the bottom — not in #275.

## What skillbook is

Lock-based **user-owned** skill management. A person (or team) keeps a central
library of Agent Skills and installs copies into many projects, then
materializes those copies into editor harness directories.

| Layer | Path | Role |
| --- | --- | --- |
| Library | `~/.skillbook/skills/<id>/` (override `SKILLBOOK_LIBRARY`) | Git-versioned personal/team store |
| Project canonical | `<repo>/.skillbook/skills/<id>/` | Committable project copy |
| Lockfile | `<repo>/skillbook.lock.json` | Per-skill `version` (int ≥ 1) + `sha256:…` hash + enabled harnesses + `symlink`/`copy` mode |
| Harness | `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.opencode/skill/`, `.pi/skills/` | Editor-facing materialization |

Skills may be a single `SKILL.md` or a directory tree (scripts / references /
assets). Hash is SHA-256 over every file: relative path + LF-normalized
content (`src/lib/skill-hash.ts`).

Project-vs-library status (`src/lib/lock-status.ts`): `synced` / `ahead` /
`behind` / `diverged` / `local-only` / `library-only`. `sync` pulls only
**behind** skills; diverged needs an explicit `resolve --strategy
library|project`. Agent-facing `--json` plus exit codes: `0` ok, `1`
usage/verify findings, `2` sync-state conflict.

Ships a default `skillbook` skill that teaches the CLI (do not edit
`~/.skillbook` by hand; edit the project copy, then push).

## What issue-flow is (contrast)

issue-flow ships **product** lifecycle skills as Jinja templates
(`src/issue_flow/templates/skills/`). `init` / `update` / `workspace update`
render them into editor trees. Modes pick which stems exist. pstack is a
curated vendor pin (`vendor_pstack.py`), not a user library.

Different job. Skillbook is “my skills, many repos, many harnesses.”
issue-flow is “this product’s workflow, deterministic scaffold, tested
templates.” Default: **coexist**, do not merge the CLIs.

## Harness map vs our `EditorProfile`

| Harness | Skillbook path | issue-flow today |
| --- | --- | --- |
| Claude Code | `.claude/skills/<id>/SKILL.md` | Yes (`editors.py`) |
| Codex | `.agents/skills/<id>/SKILL.md` | Yes |
| Cursor | `.cursor/skills/<id>/SKILL.md` (directory) | Yes (post-#79 skills-first) |
| OpenCode | `.opencode/skill/<id>/SKILL.md` (singular) | Yes |
| Pi | `.pi/skills/<id>/SKILL.md` | No — same class as Windsurf (#17) |

Older skillbook indexes still mention `.cursor/rules/<name>.md`. Current
`constants.ts` uses directory skills under `.cursor/skills/`; legacy rule
files remain **scannable** only (`LEGACY_HARNESS_PATTERNS` in
`src/lib/skills.ts`).

## Ideas vs issue-flow (survey)

| Idea | Skillbook | issue-flow today | First-pass verdict |
| --- | --- | --- | --- |
| Personal library + project copies | `~/.skillbook` ↔ `.skillbook` + push/pull | Packaged Jinja + `update` | **Later / cite #269** — user-global config + update-all + lock is the same product space. Do not build a second library here. |
| Lockfile hash + version | `skillbook.lock.json` | pstack SHA pin only; no hash of rendered output | **Candidate** — detect local edits that `update` will overwrite |
| `verify` | Hash mismatch, missing, unlocked, harness drift | `issue-flow doctor` = dirty `.issueflows/` folders only | **Candidate** — fold wording into doctor or a sibling `agent` check |
| `lint` Agent Skills spec | Name `^[a-z0-9]+(-[a-z0-9]+)*$`, required `name`+`description`, dir match, description ≤1024, body >500 warn, unknown frontmatter warn | writing-great-skills + [skill-authoring.md](./skill-authoring.md); no CLI linter | **Candidate / cite #268** |
| `scan` unmanaged skills | TUI walk of harness dirs | None | **Candidate** — list `.cursor/skills/*` (etc.) not in `SKILL_DIRS` |
| Harness symlink vs copy | Default symlink; copy fallback persisted in lock | Always render/copy | **Skip** — Jinja must render; symlink would skip templates |
| Multi-file skill trees | First-class | Almost all single `SKILL.md`; pstack vendor refuses multi-file | **Later** — only if we vendor a multi-file skill |
| Extra harness (Pi) | Yes | No | **Skip / fold** into editor-profile work |
| Depend on skillbook CLI | N/A | None | **Skip** |
| `--json` + typed findings | Widespread | Already our agent-CLI style | **Steal style**, not a feature |

## Collision / coexistence (verified in our code)

`issue-flow update` **re-renders** every packaged skill and **prunes** only
names in `SKILL_DIRS` that the active mode excludes
(`_prune_excluded_surfaces` in `init.py`). User folders with **other** names
under `.cursor/skills/` are left alone.

Collision: if skillbook (copy mode) writes a harness skill whose directory
equals an issue-flow output name (`iflow-plan`, `caveman`, `unslop`, …),
`update` overwrites it. Symlink mode would be worse (we would write through
the link into `.skillbook/` or the library).

Skillbook `lint` would **warn** on our shipped frontmatter keys
`disable-model-invocation` and `issue-flow-version` (unknown vs its
allowlist: `name`, `description`, `license`, `compatibility`, `metadata`,
`allowed-tools`, `disallowed-tools`). Our lifecycle skills also often exceed
the 500-line “progressive disclosure” warning — expected; do not blindly
adopt that cap as an error.

## Strongest steals (pending grill)

1. **Coexistence doc** (this file + a short pointer from README / project
   brief): skillbook is complementary; never put user skills in packaged
   output names; `update` owns those names.
2. **Optional `update` skip / warn** when a packaged output path is not
   “ours” (hash mismatch vs last render, or a `.skillbook` / symlink
   detected). Prevents clobbering.
3. **Agent Skills lint** as a doctor/CI helper, or as acceptance for #268 —
   adapted allowlist so issue-flow keys are known.
4. **Scan unmanaged skills** — report-only list for `doctor` / `status`.

Weak / rejected unless grill reverses:

- Replacing `issue-flow update` with skillbook.
- Storing lifecycle skills only in `~/.skillbook` (breaks `init`
  determinism and pytest).
- Shipping skillbook as a dependency or vendoring its Bun CLI.

## Decisions (grill)

Filled in during Task 2. Until then: plan defaults from #275.

| Decision | Status |
| --- | --- |
| Stance: inspiration + coexistence, **no** skillbook CLI dependency | **A** (2026-09-17) |
| #269: cite only; do not fold a personal library into #275 follow-ups | **A** cite only (2026-09-17) |
| #268: lint may feed that issue instead of a new one | **B** fold lint into #268 (2026-09-17) |
| `update` clobber protection (warn/skip if packaged path is not last render / symlink) | **A** file follow-up (2026-09-17) |
| Scan unmanaged skills | **B** separate small issue (2026-09-17) |
| Close #275 with this doc + spawned issues (no `src/` unless a one-line pointer) | **A** design doc only (2026-09-17) |
| Epic vs flat issues after pick count | **A** two flat `/iflow-issue` (2026-09-17) |
| `yolo` labels | **A** clobber no, scan yes (2026-09-17) |

## Follow-up issues

| # | Title | Notes |
| --- | --- | --- |
| [#276](https://github.com/jepegit/issue-flow/issues/276) | update: warn or skip when a packaged skill path is not last render | no yolo |
| [#277](https://github.com/jepegit/issue-flow/issues/277) | doctor: report unmanaged editor skills | `yolo` |
| [#268](https://github.com/jepegit/issue-flow/issues/268) | Improve skills | lint folded in via [comment](https://github.com/jepegit/issue-flow/issues/268#issuecomment-5718825658) |
| [#269](https://github.com/jepegit/issue-flow/issues/269) | system wide settings and update | cited only |

## Alternatives considered

- Ignore skillbook entirely — rejected as the issue’s Task 1/2; the survey
  still pays for coexistence (name collision is real).
- Optional hard interop (detect `.skillbook` and skip those harness paths) —
  parked for grill; more product than a lessons PR.
- Adopt skillbook as the user-skill backend and keep Jinja only for
  lifecycle — large architecture change; out of scope for #275.
