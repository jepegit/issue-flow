# Plan — Issue #24: utilize the tools folder and status files better

## Goal

Make agents actually (a) use and contribute to `.issueflows/00-tools/`, and
(b) keep `issue<N>_status.md` alive *during* the work rather than only at
`/iflow-close`. Both nudges live in the **templates** (source of truth), so
scaffolded projects pick them up via `issue-flow init` / `update`.

## Current state (old issue — partially addressed already)

- **Status files (part 2): mostly done.** `/iflow-start` already creates/updates
  the status file mid-work:
  - command [`iflow-start.md.j2`](src/issue_flow/templates/commands/iflow-start.md.j2) step 3
  - skill [`iflow_start/SKILL.md.j2`](src/issue_flow/templates/skills/iflow_start/SKILL.md.j2) step 6
  Both say "after meaningful progress, update (or create) `issue<N>_status.md`".
  Remaining gap: it's not created **up front**, and "re-read it when iterating"
  isn't emphasized.
- **00-tools (part 1): not done.** No command/skill mentions `00-tools`. Only a
  generic blurb in [`rules/_body.md.j2`](src/issue_flow/templates/rules/_body.md.j2)
  (line ~128). The scaffolded folder gets only a `.gitkeep`
  ([`init.py` `_create_issueflow_dirs`](src/issue_flow/init.py)), so agents have
  no in-folder signal about when to use or add tools.

## Constraints

- Edit **templates** under `src/issue_flow/templates/`, never the rendered
  `.cursor/` copies (those refresh via `issue-flow update`).
- Keep wording terse and consistent with existing command/skill voice.
- Keep template tokens (`{{ tools_folder }}`, `{{ issueflows_dir }}`, etc.) — no
  hard-coded `00-tools`.
- Don't expand scope into unrelated lifecycle commands.

### Prior art

- `iflow-start` command step 3 / skill step 6 — already creates/updates the
  status file. **Strengthen, don't duplicate.**
- `rules/_body.md.j2` ~line 128 "Scripts that can help us…" — existing tools
  blurb. **Strengthen in place** (check-first + contribute-with-usage-note).
- `iflow-plan` skill/command step 4 "Prior-art discovery" — natural hook to add
  "also check `00-tools/`".
- `init.py` `_create_issueflow_dirs` (~line 631) + `config.py` `tools_folder` —
  hook for scaffolding a `00-tools/README.md` instead of a bare `.gitkeep`.

## Approach

**Part 1 — make `00-tools` discoverable and used:**

1. **Self-describing folder.** Add a `00-tools/README.md` template rendered at
   init that states: what the folder is for, when an agent should look here
   first, and the convention for adding a tool (drop the script + a one-line
   "when to use" entry). Wire it into `_create_issueflow_dirs` so the tools
   folder gets a README (keep `.gitkeep` behaviour for the other subdirs).
2. **Check-first nudge.** In `/iflow-plan` prior-art discovery (step 4) and
   `/iflow-start` implement step, add: "before writing a helper/script, check
   `{{ tools_folder }}/` for an existing one."
3. **Contribute-back nudge.** In `/iflow-start` (command + skill): when you've
   built something reusable, save it into `{{ tools_folder }}/` and add a
   one-line usage note to its README index.
4. **Strengthen rules blurb** in `_body.md.j2` to phrase both directions
   (check-first, contribute-with-note) actionably.

**Part 2 — keep status files alive:**

5. In `/iflow-start` (command + skill): create a **skeleton** `issue<N>_status.md`
   up front (right when implementation begins) with the `- [ ] Done` checkbox,
   and explicitly "re-read and update it each iteration" so iterating agents use
   it. Light wording change; mechanics already exist.

## Files to touch

- `src/issue_flow/templates/tools/README.md.j2` *(new)* — self-describing
  `00-tools/` README (final name/location of token TBD — see Open questions).
- `src/issue_flow/init.py` — render the tools README in `_create_issueflow_dirs`.
- `src/issue_flow/templates/commands/iflow-start.md.j2` — check-first +
  contribute-back + up-front status skeleton.
- `src/issue_flow/templates/skills/iflow_start/SKILL.md.j2` — same nudges.
- `src/issue_flow/templates/commands/iflow-plan.md.j2` + `skills/iflow_plan/SKILL.md.j2`
  — add `00-tools` to prior-art discovery.
- `src/issue_flow/templates/rules/_body.md.j2` — strengthen tools blurb.
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — reflect the tools
  convention if it documents the folder.
- `tests/` (`test_init.py` / `test_templating.py`) — assert the tools README is
  scaffolded and that start/plan output mentions the tools folder.

## Test strategy

- `uv run pytest` (full suite).
- `uv run ruff check src/ tests/`.
- New/updated tests: tools-README is rendered at init; rendered `iflow-start` /
  `iflow-plan` mention `{{ tools_folder }}`.
- Manual smoke: scaffold a throwaway project and confirm `00-tools/README.md`
  appears and reads sensibly.

## Addendum — version-bump enhancement (folded into this issue/PR)

Per user request (2026-06-28), extend the version-bump workflow alongside the
00-tools / status-file work, since it is a docs-only change (no Python code
parses bump levels — verified via grep; the skills just instruct the agent to
run `uv version --bump <level>`):

- Support **all** `uv version --bump` levels: `major`, `minor`, `patch`,
  `stable`, `alpha`, `beta`, `rc`, `post`, `dev` (not just patch/minor/major).
- **Pre-release-aware default** when no level is given: stay on the current
  channel (alpha→alpha, beta→beta, rc→rc, dev→dev) or `patch` when already
  stable. Verified semantics via `uv version --dry-run` against `0.4.1a4`.

Touched: `templates/skills/iflow_version_bump/SKILL.md.j2` (rewrite),
`templates/commands/iflow-close.md.j2` + `templates/skills/iflow_close/SKILL.md.j2`
(token mapping), `templates/docs/issue-workflow.md.j2`, plus tests in
`tests/test_init.py`.

## Decisions (confirmed)

1. **Scaffold a `00-tools/README.md`** — yes. Add the new template + init wiring
   + tests.
2. **Part 2** — strengthen wording **and** create an up-front status skeleton in
   `/iflow-start`. Do **not** seed the status file in `/iflow-plan` / `/iflow-init`.
3. **Scope** — single PR covering both parts.
