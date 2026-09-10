# pstack skills (opt-in vendored subset)

Context: issue [#249](https://github.com/jepegit/issue-flow/issues/249) — "the
skills library pstack is popular; allow also installing pstack (the relevant
parts)". [pstack](https://github.com/cursor/plugins/tree/main/pstack) is Lauren
Tan's (poteto) MIT-licensed Cursor plugin: ~45 skills, playbooks, agents, and
scripts built around its own `poteto-mode` lifecycle.

## Decision

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

## Alternatives considered

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

## Re-sync procedure

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
