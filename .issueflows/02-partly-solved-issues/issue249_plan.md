# Plan — Issue #249: use parts of pstack

Source: https://github.com/jepegit/issue-flow/issues/249

## Goal

Let a project opt in to a curated subset of the [pstack](https://github.com/cursor/plugins/tree/main/pstack)
skills library (MIT, by Lauren Tan / poteto) through issue-flow, so `issue-flow init` /
`update` scaffold those skills next to the `iflow-*` skills for **every** supported
editor (Cursor, Claude Code, opencode, Codex), not only via Cursor's `/add-plugin pstack`.

## Constraints

- Templates are the source of truth (`src/issue_flow/templates/skills/`); scaffold
  behaviour changes go there, never into rendered copies.
- Off by default. `standard` must keep rendering exactly today's surface; `simple` /
  `novice` untouched. Nothing new is ever auto-invoked by the lifecycle skills.
- Config-key pattern, not a new CLI flag (mirrors `caveman_default`, `grill_me_default`,
  see `04-designs-and-guides/caveman-skill.md`, `grill-me-skill.md`,
  `skill-behaviour-knobs.md`): `config.toml` > `ISSUEFLOW_*` env > default, baked at
  `issue-flow update`.
- Vendored content stays **verbatim** (only frontmatter/provenance touched) so re-syncing
  against upstream is a diff, not a rewrite. Attribution + MIT licence text shipped.
- Precedent for vendoring: `writing-great-skills` (verbatim, repo-only) and the adapted
  `caveman` / `grill-me` (see `skill-authoring.md`; `docs/acknowledgements.md`).
- Only **single-file, subagent-free, editor-neutral** pstack skills in v1. The manifest
  emits one `SKILL.md` per skill dir; skills with `references/` / `scripts/`, Cursor
  multi-model subagents (`interrogate`, `arena`, `swarm`, `no-comments` → Comment Sicko
  agent), MCP fan-out (`why`), or a competing lifecycle (`poteto-mode`, `setup-pstack`)
  are out of scope.
- Keep `graphify-out/` untouched unless the user asks for a rebuild.

### Prior art

- `caveman` / `grill_me` / `gh_ci` stems in `SKILL_DIRS` (`templating.py`) — optional
  behaviour skills registered as plain stems; **mirror** for pstack stems.
- Membership-gated pointers in `templates/rules/_body.md.j2`
  (`{% if "caveman" in included_skills %}`) — **mirror** for a "pstack skills" section.
- `modes._expand("all")` / `_validate` / `_resolve_sets` — the `"all"` universe is
  every `SKILL_DIR`; needs a **default-vs-optional** split so pstack stays out of
  `standard` yet remains a valid `add = [...]` target for custom modes.
- `modes.read_caveman_default` + `Settings.resolve_caveman_default` +
  `write_default_config` / `_commented_issueflow_table` — **mirror** for the new key.
- `init._prune_excluded_surfaces` iterates `SKILL_DIRS` × `skill_output_name` — works
  unchanged once pstack stems are in `SKILL_DIRS` and `mode.skills` reflects the key.
- `.issueflows/00-tools/verify_scaffold.py` — end-to-end render check; **extend** with a
  pstack group.
- Toolbox has no vendoring helper — **new** `00-tools/vendor_pstack.py`.

## Approach

### 1. Curated v1 set (upstream `cursor/plugins` @ `9bd4a82`, pstack `0.15.1`)

| upstream name | stem | why it fits issue-flow |
|---|---|---|
| `unslop` | `pstack_unslop` | PR bodies, `HISTORY.md` bullets, `/iflow-issue` specs |
| `tdd` | `pstack_tdd` | bug-fix path in `/iflow-build` / `/iflow-fix` |
| `blast-radius` | `pstack_blast_radius` | "what else breaks" before `/iflow-close` opens the PR |
| `technical-writing` | `pstack_technical_writing` | docs, READMEs, commit / PR text |
| `bro` | `pstack_bro` | plain-language restate; pairs with `caveman` |
| `principle-prove-it-works` | `pstack_principle_prove_it_works` | verification before `- [x] Done` |
| `principle-subtract-before-you-add` | `pstack_principle_subtract_before_you_add` | planning discipline |
| `principle-fix-root-causes` | `pstack_principle_fix_root_causes` | build / fix discipline |
| `principle-test-behavior-not-implementation` | `pstack_principle_test_behavior_not_implementation` | test strategy |

All nine are single `SKILL.md`, contain no Jinja delimiters, and reference no
subagent, script, or `/setup-pstack` model config (checked). `blast-radius` mentions
`how` / `why` as companions in prose only — acceptable.

### 2. Vendoring layout

- `src/issue_flow/templates/skills/pstack_<name>/SKILL.md.j2` — upstream body wrapped in
  `{% raw %} … {% endraw %}` (future-proof against Jinja chars), frontmatter kept as
  upstream (`name`, `description`, `disable-model-invocation: true`; the
  `issue-flow-version` stamp is injected by `render_template`), plus one provenance
  line under the frontmatter:
  `<!-- vendored verbatim from cursor/plugins pstack v0.15.1 @ 9bd4a82 (MIT) -->`.
- `src/issue_flow/templates/skills/_pstack_LICENSE.txt` — upstream MIT text (packaged
  data, not rendered).
- Output folder = **upstream name** (`skills/unslop/`, `skills/tdd/`, …) via
  `SKILL_OUTPUT_NAMES`, so `/unslop` etc. match pstack's own docs and the `name`
  frontmatter. Document the collision if a user also installs the full Cursor plugin.
- `PSTACK_SKILL_DIRS: list[str]` in `templating.py`; `SKILL_DIRS` gains them (so
  manifest/prune/canonical loops keep working) but a new `DEFAULT_SKILL_DIRS`
  (= `SKILL_DIRS` minus optional) feeds `"all"` expansion.
- `PSTACK_NAME_TO_STEM` mapping (`"unslop" -> "pstack_unslop"`) exported for config
  parsing and docs.

### 3. Selection: `[issueflow].pstack_skills`

- Value: `[]` (default), a list of upstream names (`["unslop", "tdd"]`), or `"all"`
  (every vendored pstack skill). Unknown names → clear error listing valid ones.
- Env fallback `ISSUEFLOW_PSTACK_SKILLS` (comma-separated or `all`); precedence
  `config.toml` > env > default, same as siblings.
- Wiring point: `modes.resolve_mode(mode_id, cfg_path)` unions the mapped stems into the
  resolved `Mode.skills` after `_resolve_sets`. One place → `build_manifest`,
  `build_canonical_manifest`, `_prune_excluded_surfaces`, `included_skills`, and the
  canonical `manifest.json` all see the same set. Custom modes may still `add`
  pstack stems directly.
- `modes.py`: `_expand("all")` uses the default universe; `_validate` accepts the full
  universe; `read_pstack_skills`, `DEFAULT_PSTACK_SKILLS`, `write_default_config` /
  `_commented_issueflow_table` gain a commented `pstack_skills = []` entry.
- `config.py`: `Settings.resolve_pstack_skills`, env parsing, render-context key
  `pstack_skills` (resolved upstream names, for the rules body).

### 4. Surfaces

- `templates/rules/_body.md.j2`: new "### pstack skills" section gated on
  `pstack_skills` non-empty: one line per installed skill (name → when to use), how to
  turn on more (`pstack_skills` + `issue-flow update`), attribution link. Renders into
  `AGENTS.md`, `CLAUDE.md`, `.mdc` like the caveman pointer.
- Soft, membership-gated nudges only (never auto-run):
  `iflow_close/SKILL.md.j2` — if `pstack_unslop` installed, suggest an unslop pass
  over PR body + changelog bullet; if `pstack_blast_radius`, suggest it before the PR.
  `iflow_build/SKILL.md.j2` — if `pstack_tdd`, mention it for bug-shaped issues.
  Same gating pattern as the grill-me step 5a. Mirror the same lines in the
  duplicated `commands/iflow-close.md.j2` / `iflow-build.md.j2` (known-debt
  duplication; do not restructure).

### 5. Tooling, docs, attribution

- `.issueflows/00-tools/vendor_pstack.py`: sparse-clone `cursor/plugins` (`pstack/`),
  copy the curated list into `templates/skills/pstack_*/SKILL.md.j2` with the raw
  wrapper + provenance line (version from `.cursor-plugin/plugin.json`, short SHA),
  refresh `_pstack_LICENSE.txt`, print a diff summary; `--check` mode exits non-zero
  when vendored copies drift from upstream. Add row to `00-tools/README.md`.
- `docs/configuration.md`: "## pstack skills" section (key, env, names, collision
  note, licence). `docs/acknowledgements.md` + `README.md` acknowledgements table: add
  `cursor/plugins` (pstack, MIT). `docs/index.md` one-liner. `HISTORY.md` entry is
  `/iflow-close`'s job.
- New design doc `.issueflows/04-designs-and-guides/pstack-skills.md`: decision,
  curated-set criteria, verbatim rule, re-sync procedure, alternatives.

## Files to touch

- `src/issue_flow/templating.py` — `PSTACK_SKILL_DIRS`, `DEFAULT_SKILL_DIRS`,
  `SKILL_OUTPUT_NAMES` entries, `PSTACK_NAME_TO_STEM`.
- `src/issue_flow/modes.py` — universe split, `read_pstack_skills`, union in
  `resolve_mode`, default config comment/entry, `DEFAULT_PSTACK_SKILLS`.
- `src/issue_flow/config.py` — `resolve_pstack_skills`, env fallback, render context.
- `src/issue_flow/templates/skills/pstack_*/SKILL.md.j2` (9 new) +
  `templates/skills/_pstack_LICENSE.txt`.
- `src/issue_flow/templates/rules/_body.md.j2` — gated pstack section.
- `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2`, `iflow_build/SKILL.md.j2`,
  `templates/commands/iflow-close.md.j2`, `iflow-build.md.j2` — gated one-line nudges.
- `tests/test_templating.py`, `tests/test_modes.py`, `tests/test_config.py`,
  `tests/test_init.py` / `tests/test_update.py` — see below.
- `.issueflows/00-tools/vendor_pstack.py`, `00-tools/README.md`,
  `00-tools/verify_scaffold.py` (new group).
- `docs/configuration.md`, `docs/acknowledgements.md`, `docs/index.md`, `README.md`.
- `.issueflows/04-designs-and-guides/pstack-skills.md` (new).

## Test strategy

`uv run pytest` and `uv run ruff check src/ tests/` (project commands), plus
`uv run .issueflows/00-tools/verify_scaffold.py` for the end-to-end render.

New / extended tests:

- `test_templating.py`: every `pstack_*` template renders; `_MODE_CONTEXT` gains
  `pstack_skills: []`; default Cursor manifest has **no** pstack entries; a mode whose
  skills include `pstack_unslop` emits `{agent_dir}/skills/unslop/SKILL.md`; rendered
  pstack skill carries the `issue-flow-version` stamp and provenance line.
- `test_modes.py`: `standard` (`"all"`) excludes pstack stems; custom mode
  `add = ["pstack_tdd"]` validates; `pstack_skills = ["unslop","tdd"]` unions the two
  stems into `resolve_mode(...)`; `"all"` selects all nine; unknown name raises with
  the valid list; default config renders the commented key.
- `test_config.py`: precedence `config.toml` > `ISSUEFLOW_PSTACK_SKILLS` > `[]`; env
  parsing (`"unslop, tdd"`, `"all"`).
- `test_init.py` / `test_update.py`: init with the key writes `skills/unslop/`; removing
  the key and running `update` prunes it (existing `_prune_excluded_surfaces` path);
  `_body` output contains the pstack section only when enabled; `standard` rendered
  surface unchanged (snapshot-style assertions already present).
- `verify_scaffold.py`: new group flips `pstack_skills` in the throwaway
  `config.toml`, re-runs `update`, asserts folders appear then disappear.

## Open questions

1. **Curated set size.** Nine skills (5 tools + 4 principles) recommended. Alternative:
   ship only the five tools and leave principles for a follow-up. Trimming is a
   one-line list edit either way.
2. **Output folder naming.** Recommended: upstream names (`skills/unslop/`) for
   `/unslop` parity with pstack docs, accepting a collision when the Cursor plugin is
   also installed. Alternative: `skills/pstack-unslop/` with prefixed `name:` (no
   collision, but diverges from upstream and breaks the verbatim rule for frontmatter).
3. **Selector shape.** Recommended: `pstack_skills` list under `[issueflow]` (baked at
   `update`, mirrors sibling knobs). Alternative: rely solely on custom-mode `add`
   (already works after the universe split; less discoverable, requires `init --mode`).
4. **Lifecycle nudges.** Recommended: two soft membership-gated lines (close: unslop /
   blast-radius; build: tdd). Alternative: none — pure install, zero lifecycle touch.
5. **Scaffold-time fetch instead of vendoring** (download from GitHub during
   `init`/`update`) — rejected in this plan: needs network in `update`, breaks
   deterministic tests, and pstack's layout can move under us. Re-sync via
   `vendor_pstack.py` at issue-flow release time instead. Flag if you disagree.
