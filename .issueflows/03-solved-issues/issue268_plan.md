# Plan — Issue #268: Improve skills

## Goal

Bring issue-flow's shipped skills in line with current skill-writing guidance:
refresh the vendored reference, add a mechanical Agent Skills lint to `doctor`
(the folded-in #275 ask), and apply the concrete findings to the templates.
Workflow behaviour stays identical.

## Sources reviewed (2026-10-24)

- **mattpocock/skills @ `5beb35b`** (2026-10-19). `writing-great-skills` was
  renamed and restructured into **`writing-for-agents`** (commit `1fc6573`,
  2026-07-31): `SKILL.md` (universal: pointers, two loads, hierarchy,
  completion criteria, leading words, pruning) + `SKILL-MECHANICS.md`
  (invocation, router skills). New since our vendored `d11147d`:
  - **Negation** failure mode: prohibitions prime the banned behaviour. State the positive target, and keep a "never" only as a hard guardrail paired with that target.
  - **Environment as a source of truth.** A doc that restates config, `--help` or the directory layout is a *cache*. Cache only what a lookup cannot reveal.
  - **Completion criteria** need *clarity* and *demand*. Hiding later steps works only across a real context boundary.
  - Scope widened to every agent-read doc (AGENTS.md, rule bodies), not just skills.
- **Agent Skills spec** (agentskills.io/specification):
  - `name` is 1–64 chars, lowercase alphanumerics and hyphens, with no leading, trailing or consecutive hyphens, and it **must match the parent directory**.
  - `description` is 1–1024 chars.
  - The other known keys are `license`, `compatibility` (≤500), `metadata` and `allowed-tools`.
  - Keep the body under 500 lines / ~5000 tokens, and keep file references **one level deep**.
- **Anthropic skill best practices** (platform.claude.com):
  - No XML tags in `name` or `description`.
  - Descriptions are written in third person.
  - References go one level deep, and reference files over 100 lines get a table of contents.
  - Use one term consistently, and avoid time-sensitive text.
  - Use checklists and validate→fix loops for complex workflows.
  - Prefer scripts for deterministic steps.
- **YouTube "Claude Code Skills from First Principles"** (Agentic Lab,
  n9CSSSir3fE): **not reviewed**. The page has no description text, and caption download hit HTTP 429. See Open questions.

## Constraints

- Templates are the source of truth (`src/issue_flow/templates/skills/`); the
  rendered `.cursor/skills/` copies are refreshed with `issue-flow update`.
- Behavior is sacred: confirmations, off-path markers, `- [x] Done` rules,
  file-movement rules, output contracts, and Jinja variables stay intact.
- Word budgets in `tests/test_command_surface.py` (rule 900, SKILL 1600,
  side 3000) must still pass; this work should only shrink files.
- Vendored pstack bodies stay verbatim; the lint treats them as data. They
  pass the spec (checked: names are valid and match their output folders).
- No new runtime dependency (no PyYAML): the lint reads the frontmatter with
  a small parser that handles the shapes we emit (`key: value`, quoted
  strings, `>-` folded blocks).

### Prior art

- `agent.audit_editor_scaffolds` / `audit_unmanaged_editor_skills`
  (`src/issue_flow/agent.py`) — doctor already walks every editor's
  `skills/` dir and emits `tracking.DirtyFinding`s. **Mirror**: the lint is a
  third `audit_*` function, appended in `_audit_payload`.
- `templating.stamp_skill_version` — existing frontmatter slicing (`---`
  delimiters). **Reuse** its delimiter logic for the parser.
- `templating.packaged_skill_output_names` / `skill_output_name` — the
  dir-name source for "name matches directory".
- `tests/test_command_surface.py` — the budget tests render every lifecycle
  skill with a "loud" context. **Mirror** that fixture for a test that lints every
  rendered skill (lifecycle + caveman/grill-me + pstack).
- `.issueflows/00-tools/verify_scaffold.py` — end-to-end render check; run it
  after the template pass.
- `.cursor/skills/writing-great-skills/` — the vendored reference to replace.

## Approach

1. **Refresh the vendored reference.** Replace
   `.cursor/skills/writing-great-skills/` with
   `.cursor/skills/writing-for-agents/` (`SKILL.md`, `SKILL-MECHANICS.md`,
   verbatim from `5beb35b`, MIT provenance comment, and
   `disable-model-invocation: true` kept so it stays user-invoked at zero context
   load). Skip upstream's `agents/openai.yaml`. Update the pointers in
   `skills-and-styles.md`.

2. **House rules update** (`skills-and-styles.md#skill-authoring`). Add these
   distilled rules, each with its source:
   - **Positive over prohibition.** Each "do not / never" either becomes the positive target or stays as a hard guardrail paired with that target.
   - **Do not cache the environment.** Point at `--help`, config or code instead of restating it, unless the lookup is expensive.
   - **References one level deep.** A mode file must not send the agent to a second mode file.
   - **TOC for side files over 100 lines.**
   - **Lint is the gate.** `issue-flow doctor` and the pytest guard must be clean.

   Record the decision, the alternatives and a link to #268.

3. **Skill lint (`src/issue_flow/skill_lint.py`).** Pure functions:
   - `parse_frontmatter(text) -> dict[str, str] | None`
   - `lint_skill(skill_dir: Path) -> list[LintFinding]`

   It checks the following:

   | Check | Severity |
   |---|---|
   | `SKILL.md` exists and has frontmatter | error |
   | `name` present and matches `^[a-z0-9]+(-[a-z0-9]+)*$`, ≤64 | error |
   | `name` equals the directory name | error |
   | `description` present, non-empty, ≤1024 chars, no `<tag>` | error |
   | unknown frontmatter key (allowlist = spec keys + `disable-model-invocation`, `issue-flow-version`, `user-invocable`, `argument-hint`, `model`) | warn |
   | body > 500 lines | info |
   | side file > 100 lines without a contents list | info |

   Wiring:
   - `agent.audit_skill_spec(project_root, settings)` maps the results to `DirtyFinding`s with codes `skill_spec_<check>`. It runs over every editor's `skills/*/`, managed and unmanaged.
   - The new audit is appended in `_audit_payload`, so `issue-flow doctor`, `agent audit` and `/iflow-status doctor` all get it, with no new command.
   - Doctor exits 1 only on `error` findings, as it does today.

4. **Template pass** (each item is checkable):
   1. **One-level references.** `iflow_pick/capture.md.j2` sends the agent to
      `comments.md`, two levels deep. Make `iflow_pick/SKILL.md.j2` point at
      `comments.md` directly next to its `capture.md` pointer, and have
      `capture.md` say "triage per `comments.md`" (no second-level read).
      `iflow_run/cycle.md.j2` → `yolo.md` is a peer mode file of the same
      skill; give it the same treatment through the router. *Done when* no side
      file instructs reading another side file (grep-checked in a test).
   2. **Branch-only reference out of routers.** The PowerShell / `--body-file`
      block (`_gh_body_file.md.j2`, included in 9 templates) moves out of every
      `SKILL.md` router whose only user of it is one mode. It goes into that mode
      file, and the router keeps a pointer. *Done when* each include sits where the `gh … create/edit` step it serves is.
   3. **Negation pass on the 13 routers + caveman/grill-me.** For every
      `do not / don't / never / must not` sentence, either restate it as the
      positive target or keep it as a guardrail with the positive target
      beside it. *Done when* every hit is accounted for in the status file
      (converted / kept-as-guardrail). Mode files are out of scope for this
      pass (see Open questions).
   4. **Sediment.** The "CLI fast path (optional) … only present when the
      user installed it, e.g. `uv tool install issue-flow`" paragraph is
      repeated per skill. Collapse it to one line that points at the CLI,
      and drop the install explanation (it caches the environment).
   5. **Descriptions.** Rewrite the 11 lifecycle descriptions in third person
      ("Drafts…", "Implements…"), still one human-facing line with no
      triggers. Leave the caveman/grill-me trigger descriptions alone.
5. Re-render (`uv run issue-flow update .`), run lint, tests, and
   `verify_scaffold.py`.

## Files to touch

- `.cursor/skills/writing-great-skills/` → removed;
  `.cursor/skills/writing-for-agents/{SKILL.md,SKILL-MECHANICS.md}` added.
- `.issueflows/04-designs-and-guides/skills-and-styles.md` — pointers, new
  house rules, #268 decision record.
- `src/issue_flow/skill_lint.py` — new.
- `src/issue_flow/agent.py` — `audit_skill_spec`, wired into `_audit_payload`.
- `src/issue_flow/templates/skills/iflow_*/SKILL.md.j2` (13) and
  `caveman`, `grill_me` — negation pass, descriptions, sediment.
- `src/issue_flow/templates/skills/iflow_pick/{SKILL,capture}.md.j2`,
  `iflow_run/{SKILL,cycle}.md.j2` — one-level references.
- Templates that include `_gh_body_file.md.j2` — relocate includes.
- `.cursor/skills/**` — re-rendered output.
- `tests/test_skill_lint.py` — new.
- `docs/` — one line under the doctor reference for the new finding codes (if a
  doctor findings table exists).

## Test strategy

- `uv run pytest`, `uv run ruff check src/ tests/`.
- New `tests/test_skill_lint.py`:
  - Parser unit tests (plain, quoted, `>-` folded, missing frontmatter).
  - One test per check: a bad name, consecutive hyphens, a dir mismatch, a missing or oversize description, an XML tag, an unknown key (warn), and our own keys (no finding).
  - The **guard**: render every packaged skill (standard + `pstack_skills = "all"`) for every editor into `tmp_path`, lint them, and assert zero error and zero warn findings.
  - The one-level-reference test: no rendered side file names another side file of its skill as something to read.
  - A doctor integration test: a broken skill under `.claude/skills/` shows up in `issue-flow doctor --json` with exit 1.
- Existing `test_command_surface.py` budgets still pass (they should drop).
- `uv run .issueflows/00-tools/verify_scaffold.py`.
- Manual: `uv run issue-flow doctor` on this repo is clean.

## Open questions

1. **Lint surface.** My recommendation is to fold it into **`issue-flow doctor`**, which already
   audits editor skill dirs, plus the pytest guard. The alternative is a separate
   `issue-flow lint-skills` command. That adds surface, and #406 just cut it.
2. **The video.** I could not get its content (no description, captions
   rate-limited). The options are:
   - (a) You paste the key points or transcript and I fold them in.
   - (b) I retry the caption download during build.
   - (c) Drop it from #268 and track it as a note.

   Recommended: **(b), then (a) if it fails**.
3. **Negation pass scope.** Routers plus caveman/grill-me only (recommended:
   102 hits, reviewable), or also the 26 mode files (195 more, a much bigger
   diff)? With routers only, the mode files would go to a follow-up issue.
4. **Third-person descriptions.** Apply it (recommended; cheap, spec-aligned), or
   keep the current imperative summaries?
5. **Scope / split.** This is one PR with 4 independent parts (reference, lint,
   template pass, docs). It's still cohesive ("improve skills"). Should I keep one PR (recommended),
   or `/iflow-issue split` lint vs. template pass?
