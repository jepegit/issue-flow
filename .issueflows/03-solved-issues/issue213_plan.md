# Plan — Issue #213: option for using essential tests

## Goal

Ship opt-in **essential-tests** support for pytest projects: design contract,
config knobs (baked at `issue-flow update`), lifecycle + doctor skill hooks,
a durable test registry under designs, and optional dual CI workflow templates —
without forcing the paradigm on repos that do not want it.

## Constraints

- **Opt-in.** Feature off by default; no behaviour change until enabled in
  `config.toml` (+ `issue-flow update`).
- **pytest-only v1** (issue comment). `test_runner = "pytest"` only; other
  values → clear "unsupported — PRs welcome" message in skills/docs. No
  unittest/nose runners.
- **Compose, don't fork.** Reuse skill-behaviour knobs bake path
  (`modes.write_default_config` / templating context), same as
  `auto_plan` / `ruff_autofix`. Agents apply markers / registry edits; CLI
  does not auto-edit user test files.
- **Token budget.** Per-issue review covers **tests touched by this issue**
  only. Full-suite essential audit = `/iflow-doctor` (opt-in section), never
  every close.
- **Templates = source of truth.** Edit `src/issue_flow/templates/`, then
  regenerate this repo via update/dogfood path.
- **Back-compat.** Existing projects without knobs keep current
  "run full suite on close" behaviour.
- Cite: [skill-behaviour-knobs.md](../04-designs-and-guides/skill-behaviour-knobs.md),
  [python-toolchain-deference.md](../04-designs-and-guides/python-toolchain-deference.md),
  [dirty-issueflows.md](../04-designs-and-guides/dirty-issueflows.md) (doctor
  patterns), [this-project.md](../04-designs-and-guides/this-project.md).

### Prior art

- Knob bake: `modes.write_default_config` / `_commented_issueflow_table` /
  `init` env defaults / `docs/configuration.md` — **mirror** for new keys.
- Close/build sanity: `iflow_close` / `iflow_build` skill templates already say
  "run project test suite" via documented toolchain — **extend** with
  essential-review + optional `pytest -m <marker>` when enabled.
- Doctor: `iflow-doctor` + `issue-flow doctor` CLI today = folder hygiene only —
  **add** optional essential-registry sweep section in skill (no CLI repair of
  markers in v1 unless trivial).
- Designs seed: `templates/designs/` (e.g. `python-quality-tools.md.j2`) +
  never-overwrite pattern for user-owned designs — **coexist** with new
  `essential-tests.md` (contract) + once-seeded `test-registry.md` (living
  table).
- Toolbox: `verify_scaffold.py` — **extend** markers if rendered skills gain
  essential-tests wording.
- Graph: no existing "essential tests" nodes; CI community is
  `.github/workflows/ci.yml` (full `uv run pytest -v` today).
- None of existing knobs cover test selection.

## Approach

### Scope for this issue (recommended MVP)

Ship **one PR** that lands the contract + wiring so projects can turn the
paradigm on. Defer dogfooding a split of *this* repo's own CI (and any
graphify-assisted bulk classification) to a follow-up unless Open Q says yes.

1. **Design doc** `.issueflows/04-designs-and-guides/essential-tests.md`
   (also template under `templates/designs/` if we seed on init/update when
   missing — same never-overwrite as other guides). Define:
   - pytest marker name (default `essential`)
   - dual CI shape: PR/push → `pytest -m essential`; schedule/release → full
   - registry schema (`test-registry.md` columns)
   - when review runs (`close` / `build` / `both` / `never` + doctor)
   - agent duties: propose marker + registry row; user confirms before
     rewriting many files
   - non-goals: non-pytest runners; auto-rewriting unrelated tests; making
     essential the default for all new tests without judgment

2. **Config knobs** under `[issueflow]` (names provisional — confirm in Open Q):

   | Key | Default | Role |
   |-----|---------|------|
   | `essential_tests` | `false` | Master switch |
   | `test_runner` | `"pytest"` | Only `"pytest"` supported |
   | `essential_marker` | `"essential"` | pytest mark name |
   | `essential_review` | `"close"` | `close` \| `build` \| `both` \| `never` |

   Wire: env fallbacks `ISSUEFLOW_*`, `write_default_config`, templating
   context, `docs/configuration.md`, knobs table in
   `skill-behaviour-knobs.md`.

3. **Test registry** — seed once
   `{{ issueflows_dir }}/{{ designs_folder }}/test-registry.md` (empty table +
   instructions). Never overwrite on update. Close/build (when review on)
   append/update rows for **new/changed tests in the issue**. Doctor optional
   pass: scan suite vs registry, flag drift / suite-too-large, propose demotions.

4. **Skill hooks** (Jinja, gated on `essential_tests`):
   - **close** (and yolo close path via same template): if review includes
     close — triage tests added/changed this issue; recommend
     `@pytest.mark.<marker>` vs leave unmarked; update registry; for local
     sanity prefer `pytest -m <marker>` when workflows already split, else
     still run full suite if project has no essential CI yet (document).
   - **build**: same triage when `essential_review` is `build`/`both`.
   - **doctor**: new optional section "Essential tests audit" (off-path;
     only when master switch on) — full sweep guidance, consolidated
     confirm before bulk marker edits.
   - **rules/_body** or workflow doc: short pointer when enabled.

5. **CI helpers** (lightweight):
   - Document dual-workflow recipe in design doc.
   - Optional scaffold templates under e.g.
     `templates/workflows/ci-essential.yml.j2` +
     `ci-scheduled.yml.j2` **or** a small `issue-flow` subcommand /
     init opt-in — **prefer docs + copy-paste templates in designs** for v1
     (less CLI surface); Open Q if CLI `issue-flow workflows essential`
     wanted.
   - Do **not** silently rewrite consumer `.github/workflows/`.

6. **pytest marker registration hint** — skill/docs tell agents to ensure
   `[tool.pytest.ini_options] markers = ["essential: …"]` (or pytest.ini)
   exists when enabling; issue-flow does not own that file.

7. **Tests** — unit/round-trip for new knobs (resolve/seed/write/update bake);
   template/scaffold assertions that rendered close/doctor mention essential
   path when flag true and omit when false; extend `verify_scaffold.py` if
   cheap.

8. **HISTORY** Unreleased bullet on close.

### Explicitly out of this PR (follow-ups / mention in design)

- Bulk auto-classification of an existing huge suite via graphify.
- Changing **this** repo's CI to essential/full split (dogfood) — separate
  issue unless user wants it here.
- Non-pytest runners.
- Epic publish / auto-mode integration.

### Scope check

Issue lists four deliverables (review-on-issue, doctor sweep, CI dual
workflows, registry). Plan keeps all four as **skill/docs/config** in one
PR; avoids CLI workflow writer + dogfood CI rewrite to stay mergeable.
If that still feels fat → split: (A) design+knobs+skills+registry,
(B) CI templates/CLI, (C) dogfood. Prefer A+docs-CI in one PR.

## Files to touch

| Path | Change |
|------|--------|
| `.issueflows/04-designs-and-guides/essential-tests.md` | New contract (also template seed if applicable) |
| `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` | Add knobs rows |
| `src/issue_flow/templates/designs/test-registry.md.j2` (or similar) | Once-seed empty registry |
| `src/issue_flow/modes.py` | Defaults, read/write config keys |
| `src/issue_flow/init.py` / `cli.py` / `templating.py` | Env + context plumbing |
| `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` | Essential review + optional `-m` |
| `src/issue_flow/templates/skills/iflow_build/SKILL.md.j2` | Review when configured |
| `src/issue_flow/templates/skills/iflow_doctor/SKILL.md.j2` | Full-suite audit section |
| `src/issue_flow/templates/docs/…` / `docs/configuration.md` | Document knobs |
| `tests/test_modes.py` / templating / scaffold tests | Knob + bake coverage |
| `.issueflows/00-tools/verify_scaffold.py` | Optional marker asserts |
| Dogfood: `issue-flow update` / managed blocks | After template edits |

## Test strategy

- `uv run pytest` — new/updated knob + template render tests.
- `uv run ruff check src/ tests/`.
- Optional: `uv run .issueflows/00-tools/verify_scaffold.py` if scaffold
  markers change.
- Manual: scaffold throwaway with `essential_tests=true`, confirm skills
  mention review; with `false`, omit.

## Open questions

1. **Scope of this PR?** Recommend: design + knobs + skill hooks + registry
   seed + CI *documentation/templates in designs* (no CLI writer, no dogfood
   CI split). Accept that, or trim to design+knobs only, or expand to dogfood
   this repo's workflows?

2. **Knob names / defaults** — OK with
   `essential_tests=false`, `test_runner="pytest"`,
   `essential_marker="essential"`, `essential_review="close"`?
   Prefer review on `both` (build+close) instead?

3. **Local close command when enabled** — (a) always full suite until project
   has essential CI, (b) switch close sanity to `pytest -m essential` once
   flag on, (c) dual-run (essential required, full optional/remind)? Recommend
   **(c)** soft: run essential; remind full/scheduled exists.

4. **Registry filename** — `test-registry.md` under designs OK, or prefer
   `00-tools/` / separate folder?

5. **CI helper shape** — docs-only vs also `issue-flow` subcommand that writes
   workflow files on confirm?
