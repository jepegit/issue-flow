# Skills and response styles

How the skills are written, and the optional behaviour skills. Each section below was a separate design note; they are grouped here so the folder stays small (issue #406).

<a id="skill-authoring"></a>

## Skill authoring — house rules

Context: issue [#117](https://github.com/jepegit/issue-flow/issues/117). We adopted
mattpocock's **writing-great-skills** reference as the standard for every skill
issue-flow ships. Issue [#268](https://github.com/jepegit/issue-flow/issues/268)
refreshed it: upstream renamed it **writing-for-agents** (`1fc6573`,
2026-07-31). It is now vendored verbatim (MIT) from `5beb35b` at
`.cursor/skills/writing-for-agents/`, as `SKILL.md` + `SKILL-MECHANICS.md`, with
`disable-model-invocation: true` added. Read it before editing any template
under `src/issue_flow/templates/skills/`.

### Decision

All shipped skills follow the vendored reference. Templates are the single
source of truth; edit `SKILL.md.j2`, then re-render with `issue-flow update`.

### House rules (distilled for issue-flow templates)

- **Invocation.** Lifecycle skills (`iflow-*`) are **user-invoked**
  (`disable-model-invocation: true`): their `description` is a one-line,
  human-facing summary — no trigger lists ("Use when the user mentions…"),
  those belong only to model-invoked skills. Only `caveman` and `grill-me`
  are model-invoked and keep trigger-rich descriptions.
- **No trigger-bait "When to use" sections in user-invoked skills.** Keep
  genuinely behavior-bearing lines (e.g. "off-path: never auto-dispatch from
  /iflow"); drop lines that only restate invocation triggers.
- **Single source of truth.** Shared material lives in one place and is
  reached by a context pointer (e.g. `iflow-init` points at `iflow-comments`
  instead of inlining a rules summary).
- **Prune no-ops and sediment.** Sentence-level test: does the line change
  behavior versus the model's default? If not, delete the sentence (e.g.
  "Use UTF-8 for markdown output").
- **Positive target over prohibition** (#268, writing-for-agents *Negation*).
  A "do not X" primes X. State what to do instead. Keep a "never" only as a hard
  guardrail (destructive git, a skipped confirm, a silent pick), next to its
  positive target. Tests pin the positive wording.
- **Do not cache the environment** (#268). A line that restates `--help`,
  config, or the directory layout goes stale. Point at the lookup unless it is
  expensive, e.g. the dropped "`issue-flow` is only present when the user
  installed it" aside.
- **Reference one hop from the router** (#268, Agent Skills spec + Anthropic
  best practices). A mode file must not send the agent to read another mode
  file for reference: the router names both (`iflow-pick` → `capture.md` and
  `comments.md`). Delegating a whole procedure to another mode ("follow
  `yolo.md`") is fine; that is composition, not nested reference.
  `tests/test_skill_lint.py` pins this.
- **Branch-only reference stays on its branch.** A block only one mode uses
  goes in that mode file, or shrinks to a one-liner inside the step it serves
  (`_gh_body_file_short.md.j2` in the `pick` and `build` routers).
- **Contents list on long side files.** A mode file over 100 rendered lines
  opens with a `**Contents:**` line, so a partial read still sees the whole
  shape.
- **Third-person, tag-free descriptions.** User-invoked descriptions stay one
  human-facing line, written "Drafts…", "Implements…". Avoid `<N>`-style
  placeholders: they read as XML tags, which Anthropic's validator rejects.
- **The lint is the gate.** `issue-flow doctor` lints every editor skill
  folder (`skill_lint.py`: name regex + folder match, description ≤1024 with no
  tags, known keys, length hints). `test_every_packaged_skill_is_spec_clean`
  renders every packaged skill for every editor and requires zero errors or
  warnings.
- **Sharpen completion criteria.** Prefer checkable, exhaustive bounds
  ("every group moved and reported") over vague ones ("handle the folder").
- **Behavior is sacred.** Pruning must preserve workflow semantics:
  confirmations, off-path markers, `- [x] Done` rules, file-movement rules,
  output contracts.
- **Jinja stays intact.** Keep `{{ issueflows_dir }}`-style variables and the
  `_model_directive.md.j2` include; verify rendering with
  `uv run .issueflows/00-tools/verify_scaffold.py`.

### Alternatives considered

- Scaffolding the reference into target projects: rejected — it guides
  maintainers of this repo, not users of scaffolded projects.
- Plain doc under `04-designs-and-guides/` instead of a vendored skill:
  rejected — placing it under `.cursor/skills/` keeps it reachable while an
  agent edits skill templates, at zero context load (user-invoked).

### Decision record — #268 refresh (2026-10-24)

- **Context.** The upstream reference was renamed and restructured. It gained
  *Negation*, *environment as source of truth*, and sharper completion
  criteria. The Agent Skills spec and Anthropic's best practices add checkable
  rules: name/folder match, description limits, no XML tags, one-level
  references, a contents list for files over 100 lines. The #275 survey asked
  for a mechanical lint.
- **Decision.** Vendor `writing-for-agents`. Lint inside `issue-flow doctor`
  (packaged = error, user skill = warn, hints = info) plus a pytest guard. One
  template pass: positive phrasing on the 13 routers, caveman, grill-me and the
  shared partials; third-person tag-free descriptions; capture/comments flattened
  to one hop; contents lists; short body-file line in pick/build; CLI-install
  sediment dropped. Router prohibitions went from 102 to 32; what remains are
  guardrails.
- **Alternatives.**
  - A separate `issue-flow lint-skills` command: rejected. #406 just cut
    surface, and doctor already audits editor skill dirs.
  - PyYAML for frontmatter: rejected. It is a new runtime dependency for three
    shapes we can parse by hand.
  - The same pass over all 26 mode files (195 more prohibitions): deferred to #410
    so this diff stays reviewable.
  - Flattening mode-to-mode delegation (`drive` → `epic` → `auto` → `cycle` →
    `yolo`): rejected. That is composition, and flattening means a restructure.
- **Not reviewed.** The YouTube talk linked on #268 was dropped at the user's
  request; its captions were rate-limited.

### Known debt

- `templates/commands/*.md.j2` duplicate skill content wholesale (~1070
  lines) — a single-source-of-truth violation. Tracked as a follow-up issue
  candidate; do not fold command restructuring into unrelated PRs.

<a id="skillbook-lessons"></a>

## Skillbook lessons (issue #275)

Context: [kurochenko/skillbook](https://github.com/kurochenko/skillbook)
(MIT, Bun/TS CLI). Surveyed `master` on 2026-09-17 (shallow clone). This note
is the durable record of what we learned and what we chose to steal. Follow-up
implementations live on the GitHub issues listed at the bottom — not in #275.

### What skillbook is

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

### What issue-flow is (contrast)

issue-flow ships **product** lifecycle skills as Jinja templates
(`src/issue_flow/templates/skills/`). `init` / `update` / `workspace update`
render them into editor trees. Modes pick which stems exist. pstack is a
curated vendor pin (`vendor_pstack.py`), not a user library.

Different job. Skillbook is “my skills, many repos, many harnesses.”
issue-flow is “this product’s workflow, deterministic scaffold, tested
templates.” Default: **coexist**, do not merge the CLIs.

### Harness map vs our `EditorProfile`

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

### Ideas vs issue-flow (survey)

| Idea | Skillbook | issue-flow today | First-pass verdict |
| --- | --- | --- | --- |
| Personal library + project copies | `~/.skillbook` ↔ `.skillbook` + push/pull | Packaged Jinja + `update` | **Later / cite #269** — user-global config + update-all + lock is the same product space. Do not build a second library here. |
| Lockfile hash + version | `skillbook.lock.json` | pstack SHA pin only; no hash of rendered output | **Candidate** — detect local edits that `update` will overwrite |
| `verify` | Hash mismatch, missing, unlocked, harness drift | `issue-flow doctor` = dirty `.issueflows/` folders only | **Candidate** — fold wording into doctor or a sibling `agent` check |
| `lint` Agent Skills spec | Name `^[a-z0-9]+(-[a-z0-9]+)*$`, required `name`+`description`, dir match, description ≤1024, body >500 warn, unknown frontmatter warn | writing-great-skills + [skill-authoring.md](./skill-authoring.md); no CLI linter | **Done in #268** — `skill_spec_*` findings in `issue-flow doctor` |
| `scan` unmanaged skills | TUI walk of harness dirs | None | **Candidate** — list `.cursor/skills/*` (etc.) not in `SKILL_DIRS` |
| Harness symlink vs copy | Default symlink; copy fallback persisted in lock | Always render/copy | **Skip** — Jinja must render; symlink would skip templates |
| Multi-file skill trees | First-class | Almost all single `SKILL.md`; pstack vendor refuses multi-file | **Later** — only if we vendor a multi-file skill |
| Extra harness (Pi) | Yes | No | **Skip / fold** into editor-profile work |
| Depend on skillbook CLI | N/A | None | **Skip** |
| `--json` + typed findings | Widespread | Already our agent-CLI style | **Steal style**, not a feature |

### Collision / coexistence (verified in our code)

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

### Strongest steals (pending grill)

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

### Decisions (grill)

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

### Follow-up issues

| # | Title | Notes |
| --- | --- | --- |
| [#276](https://github.com/jepegit/issue-flow/issues/276) | update: warn or skip when a packaged skill path is not last render | implemented: warn+skip, `--force` overwrites |
| [#277](https://github.com/jepegit/issue-flow/issues/277) | doctor: report unmanaged editor skills | `yolo` |
| [#268](https://github.com/jepegit/issue-flow/issues/268) | Improve skills | lint folded in via [comment](https://github.com/jepegit/issue-flow/issues/268#issuecomment-5718825658); implemented as doctor `skill_spec_*` |
| [#269](https://github.com/jepegit/issue-flow/issues/269) | system wide settings and update | cited only |

### Alternatives considered

- Ignore skillbook entirely — rejected as the issue’s Task 1/2; the survey
  still pays for coexistence (name collision is real).
- Optional hard interop (detect `.skillbook` and skip those harness paths) —
  parked for grill; more product than a lessons PR.
- Adopt skillbook as the user-skill backend and keep Jinja only for
  lifecycle — large architecture change; out of scope for #275.

<a id="caveman-skill"></a>

## Caveman skill

Context: issue #81 — ship an optional "caveman" response-style skill (terse,
token-greedy; keep technical substance, drop filler). Full mode only, English
only — no intensity table, no multi-language.

### Decision

- The caveman behavior ships as a regular Agent Skill template at
  `src/issue_flow/templates/skills/caveman/SKILL.md.j2`, registered as the
  `caveman` stem in `SKILL_DIRS` (templating.py).
- It is part of the `standard` mode (which selects `skills = "all"`) and is
  excluded from `simple` (whose explicit skill list omits it). Mode membership —
  not a new CLI flag — gates whether it is scaffolded. `_prune_excluded_surfaces`
  already iterates `SKILL_DIRS`, so switching `standard -> simple` removes it.
- Stem name is `caveman` (no `iflow_` prefix) -> output folder `skills/caveman/`,
  because it is a behavior skill, not a workflow command.
- Unlike the workflow skills, its frontmatter is **model-invocable** (no
  `disable-model-invocation: true`): it is dormant until the user asks for it
  ("caveman" / "token greedy") and turns off via "stop caveman" / "normal mode".
- It is **registered in the rules managed block** (`rules/_body.md.j2`, shared by
  `AGENTS.md`, `CLAUDE.md`, and the always-applied `.mdc` rule) as a short,
  membership-gated *pointer* (`{% if "caveman" in included_skills %}`). The
  pointer documents existence + toggle words only; the always-on behavior text
  lives in the skill, so the always-applied rule never forces caveman on.

### Alternatives considered

- A dedicated CLI flag (`--with-caveman`) or a separate built-in caveman mode —
  rejected in favor of "in standard mode" per issue clarification (simpler, no
  new persisted concept).
- Inlining the full caveman ruleset into `AGENTS.md` — rejected: the shared body
  feeds an `alwaysApply: true` rule, so it would force caveman on by default.

Link: https://github.com/jepegit/issue-flow/issues/81

### Follow-up: opt-in always-on default (issue #91)

Context: users wanted a per-project way to make caveman the default style,
without re-asking every session.

#### Decision

- New **opt-in** config key `[issueflow].caveman_default` (bool, default
  `false`), with an `ISSUEFLOW_CAVEMAN_DEFAULT` env fallback. Resolution order
  mirrors `mode`: persisted `config.toml` > env > default. The persisted value
  beats the env so a stray env var can't flip it on `update`
  (`Settings.resolve_caveman_default`; reader `modes.read_caveman_default`).
- Surfaced to templates as the `caveman_default` context key. The caveman block
  in `rules/_body.md.j2` now branches: when `caveman_default` is true (and
  `caveman` is in `included_skills`) it renders an **always-on** pointer; the
  pointer reaching the `alwaysApply: true` rule is exactly what re-arms caveman
  each session. Default stays off-by-default, preserving #81 behavior.
- This intentionally revisits the #81 rejection of "force caveman on by default":
  it is no longer the default — it only happens when a project explicitly opts in,
  so the always-applied rule stays inert unless the user asked for it.

#### Alternatives considered

- A `--caveman-default` CLI flag — rejected to match the existing config-key
  pattern (`mode`) and keep the toggle editable in `config.toml` + re-`update`,
  not re-`init`.
- A paste-in snippet for the user's unmanaged `AGENTS.md` — viable but not
  discoverable; the config key plus managed-block rendering keeps it consistent
  across `AGENTS.md` / `CLAUDE.md` / `.mdc`.

Link: https://github.com/jepegit/issue-flow/issues/91

<a id="grill-me-skill"></a>

## Grill-me skill

Context: issue #32 — ship mattpocock's `grill-me` design-review skill as an
issue-flow skill, tuned to our workflow. It should not be active in `standard`
mode by default, but a project should be able to turn it on during planning, and
custom modes should be able to include it.

### Decision

- The grilling behavior ships as a regular Agent Skill template at
  `src/issue_flow/templates/skills/grill_me/SKILL.md.j2`, registered as the
  `grill_me` stem in `SKILL_DIRS` (templating.py) -> output folder
  `skills/grill-me/` (underscores -> hyphens; matches the `name: grill-me`
  frontmatter).
- It is part of the `standard` mode (which selects `skills = "all"`) and excluded
  from `simple` (whose explicit skill list omits it). Mode membership — not a new
  CLI flag — gates whether it is scaffolded, mirroring `caveman`.
- Like `caveman` (and unlike the workflow skills), its frontmatter is
  **model-invocable** (no `disable-model-invocation: true`): it is dormant until
  the user asks for it ("grill me") and turns off via "stop grilling" /
  "normal mode".
- Adapted to issue-flow philosophy: it is a **planning** aid. One question at a
  time, each with a recommended answer; explore the code/issue/designs instead of
  asking when answerable; resolve the decision tree, then feed the agreed
  decisions into `issue<N>_plan.md`. It questions and aligns — it does not write
  code (that stays with `/iflow-build`).

### On-by-default toggle (mirrors caveman #91)

This directly mirrors the `caveman_default` mechanism from issue #91 (see
`skills-and-styles.md#caveman-skill`), per the request to "set it on by default in config.toml like
caveman".

- New **opt-in** config key `[issueflow].grill_me_default` (bool, default
  `false`), with an `ISSUEFLOW_GRILL_ME_DEFAULT` env fallback. Resolution order
  mirrors `mode` / `caveman_default`: persisted `config.toml` > env > default.
  The persisted value beats the env so a stray env var can't flip it on `update`
  (`Settings.resolve_grill_me_default`; reader `modes.read_grill_me_default`).
- Surfaced to templates as the `grill_me_default` context key. Two membership-
  gated surfaces branch on it (both gated on `"grill_me" in included_skills`):
  - `rules/_body.md.j2` — a "Planning aids" pointer (always-on vs available-on-
    request). The pointer reaching the `alwaysApply: true` rule is what arms
    grilling each session.
  - `skills/iflow_plan/SKILL.md.j2` — step 5a: when on, run a grilling pass
    before drafting the plan; when off, note that grilling is available on
    request.
- Default stays off-by-default, honoring the issue's "not active in standard by
  default" while still letting projects opt in and custom modes include it.

### Alternatives considered

- Keeping `grill_me` out of `standard` entirely (install only via custom mode) —
  rejected: a default-on flag needs the skill installed to point at, and caveman
  parity (dormant-in-standard + a `_default` flag) satisfies every clause of the
  issue without a new persisted "install" concept.
- A dedicated CLI flag (`--with-grill` / `--grill-default`) — rejected to match
  the existing config-key pattern (`mode`, `caveman_default`), editable in
  `config.toml` + re-`update` rather than re-`init`.

Link: https://github.com/jepegit/issue-flow/issues/32

<a id="pstack-skills"></a>

## pstack skills (opt-in vendored subset)

Context: issue [#249](https://github.com/jepegit/issue-flow/issues/249) — "the
skills library pstack is popular; allow also installing pstack (the relevant
parts)". [pstack](https://github.com/cursor/plugins/tree/main/pstack) is Lauren
Tan's (poteto) MIT-licensed Cursor plugin: ~45 skills, playbooks, agents, and
scripts built around its own `poteto-mode` lifecycle.

### Decision

- **Vendor, don't fetch.** A curated subset is copied into
  `src/issue_flow/templates/skills/pstack_<name>/SKILL.md.j2` at issue-flow
  release time by `.issueflows/00-tools/vendor_pstack.py` (sparse clone of
  `cursor/plugins`, `--check` for drift). No network in `init` / `update`,
  deterministic tests, and a layout change upstream breaks the tool, not users.
- **Verbatim bodies.** Upstream frontmatter + body are wrapped in
  `{% raw %} … {% endraw %}`; the only additions are the automatic
  `issue-flow-version` stamp and one provenance comment
  (`vendored verbatim from cursor/plugins pstack v<ver> @ <sha> (MIT)`). Re-sync
  is a diff review, never a rewrite. Upstream MIT text ships as
  `templates/skills/_pstack_LICENSE.txt`; attribution rows in `README.md` and
  `docs/acknowledgements.md`.
- **Curation criteria (v1).** Single `SKILL.md` (the manifest emits one file per
  skill dir), no Cursor multi-model subagents, no bundled scripts, no MCP
  fan-out, no dependency on `/setup-pstack` model config, no competing lifecycle.
  Result: `unslop`, `tdd`, `blast-radius`, `technical-writing`, `bro`,
  `principle-prove-it-works`, `principle-subtract-before-you-add`,
  `principle-fix-root-causes`, `principle-test-behavior-not-implementation`.
  Excluded on purpose: `poteto-mode`, `setup-pstack`, `interrogate`, `arena`,
  `swarm`, `no-comments` (Comment Sicko agent), `why` (MCP), `how` / `reflect` /
  `architect` (reference files), automations, agents.
- **Optional stems.** `templating.py` now has `DEFAULT_SKILL_DIRS` (what a
  mode's `skills = "all"` expands to) and `OPTIONAL_SKILL_DIRS`
  (= `PSTACK_SKILL_DIRS`); `SKILL_DIRS` is the union so manifest / prune /
  canonical loops keep working. `modes._expand("all")` uses the default set,
  `_validate` the full set, so `standard` is byte-identical and custom modes may
  still `add = ["pstack_tdd"]`.
- **Selector: `[issueflow].pstack_skills`.** List of upstream names or `"all"`;
  env fallback `ISSUEFLOW_PSTACK_SKILLS` (comma list / `all`); precedence
  `config.toml` > env > none, like every sibling knob. The union into
  `Mode.skills` happens once, in `modes.resolve_mode(..., pstack_skills=...)`
  (`Settings.resolve_mode` and `run_init` pass the resolved value; a bare
  `resolve_mode(id, cfg_path)` reads the persisted key). Everything downstream —
  `build_manifest`, `build_canonical_manifest`, `_prune_excluded_surfaces`,
  `included_skills`, `manifest.json` — therefore agrees.
- **Output folders keep upstream names** (`skills/unslop/`) via
  `SKILL_OUTPUT_NAMES`, so `/unslop` matches pstack's docs and the `name:`
  frontmatter. If the full Cursor plugin is also installed the same-named skills
  coexist; documented, not prevented.
- **Surfaces.** `rules/_body.md.j2` renders a membership-gated "pstack skills"
  section (one line per installed skill, how to change the selection). Soft
  nudges, all "suggest / offer, never run unasked": `iflow_close` step 1
  (`blast-radius`) and step 8 (`unslop` on PR body + changelog bullet, skipped
  under `yolo`); `iflow_build` step 7 (`tdd` for bug-shaped issues). Mirrored in
  the duplicated command templates (known debt, not restructured here).
- **Step profiles.** Vendored stems are excluded from `LIFECYCLE_SKILL_STEMS`
  (no MODEL & EXECUTION DIRECTIVE injected — bodies stay verbatim).

### Alternatives considered

- Scaffold-time download from GitHub — rejected: network in `update`,
  non-deterministic tests, upstream layout drift lands on users.
- Prefixed output folders (`skills/pstack-unslop/`) — rejected: diverges from
  pstack's own invocation docs and would require editing the `name:` frontmatter,
  breaking the verbatim rule.
- Custom-mode `add` only, no `pstack_skills` key — works after the universe split
  but is undiscoverable and needs `init --mode`; kept as a power-user path.
- Adapting the skill bodies to issue-flow vocabulary (as done for `caveman` /
  `grill-me`) — rejected for now; verbatim keeps re-sync trivial and honours
  "fork it, make it yours" without silently diverging.

### Re-sync procedure

```bash
uv run .issueflows/00-tools/vendor_pstack.py --check   # drift report
uv run .issueflows/00-tools/vendor_pstack.py           # rewrite templates
uv run pytest tests/test_templating.py -k pstack
```

If an upstream skill stops being single-file, the tool exits non-zero naming
it; either drop it from `CURATED` + `PSTACK_SKILL_NAMES` (add the stem to
`RETIRED_SKILLS` so `update` prunes it) or extend the manifest to multi-file
skills first.

Link: https://github.com/jepegit/issue-flow/issues/249
