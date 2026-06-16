# Plan for issue #58: Allow for not using uv

## Goal

Make the scaffolded issue-flow rules **defer to a project's existing, documented
Python toolchain** instead of hard-mandating `uv`. In particular, when a project
uses **conda**, the rules must tell agents to run Python (including `pytest`)
inside the **activated conda environment** rather than via `uv run`.

## Constraints

- The single source of truth for the rules body is
  [`_body.md.j2`](../../src/issue_flow/templates/rules/_body.md.j2); it is included by
  `AGENTS.md.j2`, `CLAUDE.md.j2`, and `issueflow-rules.mdc.j2`, so editing it once
  updates all three editor outputs (see
  [`editor-profiles.md`](../04-designs-and-guides/editor-profiles.md)). Keep it
  editor-neutral (no `{{ editor_name }}` in the body) so shared `AGENTS.md`
  content stays identical across editors.
- Keep changes terse and proportional — the issue asks to "modify the rules a
  bit", not to add a config system. **No new config var or templating plumbing**
  (see Open questions for the rejected alternative).
- `uv` stays the recommended **default/example** (this very repo is uv-managed),
  but must be framed as *one* option, conditional on what the project documents.
- This repo *is* the tool and dogfoods its own scaffold: the managed block in
  the root `AGENTS.md`, plus `.cursor/rules/issueflow-rules.mdc`, are generated
  from these templates and must be regenerated after the template edits.
- Edit **templates**, never the already-rendered copies, except via the
  regeneration step.

### Prior art

- `_body.md.j2` "Running python" / "Package Management with `uv`" sections
  (`src/issue_flow/templates/rules/_body.md.j2`) — convention: prescriptive
  "use uv exclusively, never pip/poetry". New work: **rewrite in place** to be
  deferential + conda-aware; this is the primary change.
- `EditorProfile` / `template_context` (`src/issue_flow/editors.py`,
  `src/issue_flow/config.py`) — convention: per-editor differences via profile
  fields; body stays editor-neutral. New work: **coexist** — no new context keys.
- Hard `uv run pytest` references already softened elsewhere: `issue-yolo`
  ("or the repo's documented test command"), `issue-close` ("e.g. `uv run
  pytest`"). New work: **mirror** that "e.g. / or the project's documented
  command" phrasing in the remaining prescriptive spots.
- `scripts/update_issueflow_setup.py` → `run_update(repo_root)` — the supported
  way to refresh this repo's own scaffold from templates. New work: **reuse** it
  in the regeneration step.

## Approach

1. **Rewrite the "Running python" + "Package Management" sections of
   `_body.md.j2`** into a single deferential block, roughly:
   - Lead with: *"Respect the project's existing tooling. If the project already
     documents a Python toolchain (in its README, `AGENTS.md`, `CLAUDE.md`,
     `.cursor/rules`, `environment.yml`, `pyproject.toml`, etc.), follow that."*
   - **conda** branch: if the project uses conda, run all Python commands —
     scripts **and `pytest`** — inside the **activated conda environment**
     (e.g. `conda activate <env>` first, or `conda run -n <env> ...`); do **not**
     substitute `uv run`.
   - **uv** branch (default/example): keep the existing `uv run` / `uv add` /
     `uv sync` guidance, but framed as "if the project uses uv (the default for
     projects scaffolded fresh)".
   - **other** (plain venv / pip / poetry): use whatever the project documents;
     don't force uv.
   - Keep "don't call bare `python ...`; use the project's runner" as the
     tool-neutral principle.
2. **Lightly soften the most prescriptive hard-`uv` phrasings** in the
   command/skill templates so they consistently say "the project's documented
   Python toolchain (e.g. `uv run pytest`, or inside the activated conda env)":
   - `skills/issueflow_issue_start/SKILL.md.j2` "Project conventions" (currently
     "Run Python via **`uv run`** … Manage dependencies with **`uv …`** only").
   - `commands/issue-start.md.j2` step 2 parenthetical.
   - `commands/issue-plan.md.j2` + `skills/issueflow_issue_plan/SKILL.md.j2`
     "Test strategy" examples.
   - Leave **version-bump** templates (`uv version --bump`) as-is for now — that
     is genuinely uv-specific tooling, gated behind an opt-in `bump` argument and
     a "skip if no bumpable pyproject" escape hatch; flag in Open questions.
3. **Regenerate this repo's own scaffold** so the dogfooded rules match the new
   templates: run `uv run python scripts/update_issueflow_setup.py` (equivalently
   `uv run issue-flow update .`). This refreshes the managed block in `AGENTS.md`
   and `.cursor/rules/issueflow-rules.mdc`.
4. **Add a short design note** under
   `.issueflows/04-designs-and-guides/` recording the "rules defer to existing
   project tooling (esp. conda)" decision, linked to issue #58.

## Files to touch

- `src/issue_flow/templates/rules/_body.md.j2` — rewrite "Running python" +
  "Package Management with `uv`" into a deferential, conda-aware block. (primary)
- `src/issue_flow/templates/skills/issueflow_issue_start/SKILL.md.j2` — soften
  "Project conventions" to defer to documented toolchain.
- `src/issue_flow/templates/commands/issue-start.md.j2` — soften step-2 `uv`
  parenthetical.
- `src/issue_flow/templates/commands/issue-plan.md.j2` — "Test strategy" example.
- `src/issue_flow/templates/skills/issueflow_issue_plan/SKILL.md.j2` — same.
- `.issueflows/04-designs-and-guides/python-toolchain-deference.md` — **new**
  short design note (created during `/issue-start`).
- Regenerated (not hand-edited): root `AGENTS.md` managed block,
  `.cursor/rules/issueflow-rules.mdc` (via the update script).

## Test strategy

- Run the project's documented test command — here `uv run pytest` — before and
  after the change. No test currently asserts on the `uv` wording (grep of
  `tests/` for `uv`/`conda`/`exclusively` found nothing), so existing tests
  should stay green.
- `uv run ruff check src/ tests/` for lint.
- Manual check: render/update into this repo and eyeball the regenerated
  `AGENTS.md` block + `.mdc` for the new deferential wording, and confirm no
  literal editor-name leak into the shared body.
- Optional: a small new test asserting the rendered body contains "conda" and no
  longer says "Use `uv` exclusively" (decide during `/issue-start`; see Open
  questions).

## Open questions

1. **Wording-only vs config toggle.** Recommended: wording-only (deferential
   rules), matching "value the project's existing rules". Rejected alternative:
   an `ISSUEFLOW_PYTHON_RUNNER` (uv|conda|pip) config var driving rendered
   examples — more machinery than "a bit", and deference is a runtime concern,
   not a scaffold-time toggle. OK to proceed wording-only?
2. **Version bump.** Leave `uv version --bump` references untouched (uv-specific,
   opt-in, already has a skip path), or also genericize them? Recommend leaving
   them for this issue.
3. **New regression test.** Add the small "body mentions conda / no longer
   mandates uv exclusively" test, or keep this docs-only? Recommend adding it.
