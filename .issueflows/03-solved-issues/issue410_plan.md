# Plan: issue #410, positive phrasing across the lifecycle mode files

## Goal

Apply #268's *Negation* rule to the 26 `iflow_*/<mode>.md.j2` mode files. Each prohibition is converted to its positive target, removed as a duplicate, or kept as a guardrail beside its positive target. Behavior does not change, and every hit is accounted for in the status file.

## Constraints

- House rules: `.issueflows/04-designs-and-guides/skills-and-styles.md#skill-authoring`:
  - positive target over prohibition
  - behavior is sacred
  - Jinja stays intact
  - one-hop reference
- **Keep as a guardrail** only in these categories:
  - destructive git (`-D`, `--force`, rebase or push of the default branch, deleting the default branch, `--admin`, skipping CI);
  - skipped or merged confirms (an A1/A2 split, "ask once", "explicit yes");
  - silent picks or guesses;
  - merge and force-push scope;
  - editing `HISTORY.md` on the issue branch;
  - auto-chaining `/iflow-cleanup`.
  
  Each kept line also states the positive target.
- **Preserve:**
  - confirmations
  - off-path markers
  - `- [x] Done` routing
  - file-move rules
  - output contracts (the `comments.md` block shape, the JSON or field names that skills read)
  - `{{ … }}` / `{% … %}` blocks
- Word counts: no mode file grows, and the `SIDE_BUDGET = 3000` budget in `tests/test_command_surface.py` still holds.
- Out of scope: flattening the `drive → epic → auto → cycle → yolo` delegation, and the routers (#268 did those).
- Counting regex (case-insensitive, word-bounded): `do not|don't|never|must not`. Baseline is **204 hits in 20,067 words** (snapshot in the scratchpad). The issue's 195 used a looser count; the status tally uses 204.

### Prior art

- #268 negation pass over the routers, with a per-file tally in `03-solved-issues/issue268_status.md`. This pass mirrors its method and tally format.
- `.issueflows/00-tools/verify_scaffold.py` (just refreshed in #409): end-to-end render check, run after re-rendering.
- `tests/test_skill_lint.py::test_side_files_keep_references_one_level_deep` already guards mode files. No helper for counting prohibitions exists; this issue uses a one-off grep in the scratchpad.

## Approach

1. Work through the files heaviest first:
   - `issue/epic` (22)
   - `close/changelog`, `run/cycle` (17 each)
   - `run/auto` (15), `run/drive` (14), `close/version` (12)
   - `pick/comments` (10)
   - then the long tail of files with 1–9 hits
2. For each hit, decide:
   - **convert:** rewrite as the positive instruction. For example, "Do not edit HISTORY.md" becomes "Trailers only; `changelog release` writes HISTORY.md".
   - **remove:** the line duplicates the router, its own Constraints, or a sibling line, or changes nothing compared with the default behavior.
   - **keep:** a guardrail from the list above, rewritten as needed to sit next to its positive target.
3. Merge Constraints sections that only repeat steps into one positive scope line where possible, as #268 did for `plan`.
4. Update tests that pin wording. Found so far: `test_command_surface.py:264,269` and `test_init.py:367,690,769–781` look like guardrails (keep). Others will surface when the suite runs.
5. Re-render with `uv run issue-flow update`, which refreshes `.cursor/skills/**` and `skill-stamps.json`.
6. Record a per-file tally (hits → converted / removed / kept) in `issue410_status.md`, and add one line to the #268 decision record in `skills-and-styles.md`.

## Files to touch

- `src/issue_flow/templates/skills/iflow_*/*.md.j2`: all 26 mode files.
- `tests/test_*.py`: only where a pinned string changes.
- `.cursor/skills/**`, `.issueflows/agent/skill-stamps.json`: re-rendered output.
- `.issueflows/04-designs-and-guides/skills-and-styles.md`: the follow-up line goes from "deferred to #410" to done, with the counts.
- `.issueflows/04-designs-and-guides/test-registry.md`: only if a new test is added.

## Test strategy

- `uv run pytest`, including the budgets in `test_command_surface.py` and `test_skill_lint.py`.
- `uv run ruff check src/ tests/`
- `uv run issue-flow doctor`, which must report no `skill_spec_*` errors.
- `uv run .issueflows/00-tools/verify_scaffold.py`
- A before/after hit and word count per file, checked against the scratchpad baseline.

## Open questions

1. **Ratchet test?** Add a test that caps the total prohibitions in the mode files at the final count, so new ones can't creep back in. My recommendation is yes: one small test in `test_command_surface.py`, not marked essential.
2. **One PR?** The issue is one deliverable and the tally keeps the diff reviewable, so I recommend not splitting it.
