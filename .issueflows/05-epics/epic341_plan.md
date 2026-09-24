# Epic #341: Make the documentation easier to use

Anchor: https://github.com/jepegit/issue-flow/issues/341
Status: confirmed

## Goal

A first-time reader of <https://issue-flow.readthedocs.io/en/latest/> can
find the right entry point, understand the core concepts, and reach any page
without hitting a 404. Scaffolded projects also ship working doc links. The
epic is done when: (1) the built site has no broken internal links and CI
enforces this; (2) the navigation is grouped by what the reader is trying to
do, with a Concepts/glossary page; (3) the home page and Getting started
share one quick start; (4) the reference pages (command reference,
configuration) are editor-neutral and easy to scan.

Source of findings: [docs-usability-review.md](../04-designs-and-guides/docs-usability-review.md)
(§1–§13).

## Constraints

- **Docs and doc templates only.** No change to command behaviour or skill
  logic.
- **Templates first.** Pages rendered from templates (`docs/issue-workflow.md`
  ← `src/issue_flow/templates/docs/issue-workflow.md.j2`) and links inside
  skill/command templates are fixed in `src/issue_flow/templates/`, then
  re-rendered. Never hand-edit only the rendered copy.
- **Keep URLs stable.** Moving pages in the nav should not rename files
  under `docs/`. When a rename is unavoidable, add a redirect.
- **Stay on Zensical + Read the Docs.** Use only extensions already enabled
  in `zensical.toml`, unless an issue says otherwise (for example Mermaid).
- The review doc must be committed (with the first Stage 1 PR) so the
  issues can link to it.
- Epics decompose into the normal issue lifecycle (branch + PR).

## Stage 1 — Fix broken links and add a guard

Fix every broken link first and add a CI check that fails on broken links,
so Stage 2's restructuring can't break links without anyone noticing.
Retires the most user-visible defect for little effort.
- Goal: built site has zero broken internal links; CI fails on new ones.

### Issue: docs: fix Read the Docs URLs missing /en/latest/

- Spec: Links of the form `https://issue-flow.readthedocs.io/<path>/` (without `/en/latest/`) return 404. They appear in `docs/llms.txt` (6), `README.md` (1), `docs/issue-workflow.md` (1), `src/issue_flow/templates/docs/issue-workflow.md.j2` (1), `src/issue_flow/templates/commands/iflow-init.md.j2` (2) and `src/issue_flow/templates/skills/iflow_init/SKILL.md.j2` (3). Rewrite them to `/en/latest/…`. Also set `site_url` in `zensical.toml` to the versioned base. Re-render this repo's own scaffold (`uv run scripts/update_issueflow_setup.py`) so `docs/issue-workflow.md` matches the template. Optionally add a test that fails if any template contains the unversioned pattern. See review §1.
- Goal: `grep -rE 'readthedocs\.io/[a-z]' docs src README.md | grep -v /en/` returns nothing, and every rewritten URL returns HTTP 200.
- Model: fast
- Depends on: none
- yolo: yes — mechanical search-and-replace, low blast radius, and the template tests catch rendering regressions.
- Published: #342

### Issue: docs: replace links into .issueflows/ and apply small wording fixes

- Spec: `docs/configuration.md` links to `../.issueflows/04-designs-and-guides/*.md`, which is outside the published site (404). Replace each with the GitHub blob URL, or summarise the decision inline. Where plain-text mentions of `.issueflows/04-designs-and-guides/…` refer to the reader's scaffolded project, say so explicitly. Also apply the wording fixes from review §13: the unclear "folded at the bottom of this page intro" sentence in `cli.md`; mark the `agent …` helpers as "called by skills"; state prerequisites and expected time at the top of `getting-started.md`. Commit `docs-usability-review.md` in this PR if the previous issue did not. See review §2, §13.
- Goal: the built `site/` contains no relative links to `.issueflows/`, and the three wording fixes are in.
- Model: fast
- Depends on: none
- yolo: yes — a few targeted text edits in docs only, no code paths touched.
- Published: #343

### Issue: ci: add a link check on the built docs site

- Spec: Add a CI job (in `ci.yml` or a new docs workflow) that runs `uv run zensical build` and then a link checker (e.g. `lychee` via its GitHub Action) on `site/`. Internal links must be checked and must fail the job. External links should be checked with retries, or reported only as warnings, so flaky third-party sites don't block PRs. Document how to run the check locally in `docs/developing.md`. See review §2 "Guard".
- Goal: a PR that introduces a broken internal doc link fails CI; the current `main` passes.
- Model: default
- Depends on: #342, #343
- yolo: no — new CI tooling that needs judgement about external-link flakiness and job placement.
- Published: #344

## Stage 2 — Restructure navigation and entry points

Reorganise the site around what the reader is trying to do before rewriting
any long page. The new Concepts page is where terms get defined, so later
stages can link to it instead of re-explaining them.
- Goal: grouped nav, one canonical quick start, and every core term defined in one place.

### Issue: docs: regroup navigation and the How-to index

- Spec: In `zensical.toml`, regroup the nav into Getting started (with Choose a mode and Editor support moved in), Concepts (placeholder until the next issue), How-to guides (sub-groups Everyday / Faster / Bigger changes / Team and repos), Reference (Commands, CLI, Configuration, Graphify), For agents, and Project (Developing, Changelog, Acknowledgements). Do not rename files. Rewrite `docs/how-to/index.md` as grouped tables that match the new nav. Evaluate `navigation.tabs` and enable it if it makes the sidebar shorter. See review §4.
- Goal: the nav matches the grouping above, no file under `docs/` is renamed, and the link check passes.
- Model: default
- Depends on: #344
- yolo: no — grouping and labels are judgement calls the user should see.
- Published: #346

### Issue: docs: add a Concepts page with glossary

- Spec: Create `docs/concepts.md` covering: the lifecycle (capture → plan → build → close → cleanup) and the file each step writes; the `.issueflows/` layout and how issue groups move between 01/02/03 (move the file tree here from the home page); on-path vs off-path commands; where the agent always stops to ask; and a glossary table (focus issue, off-path, dispatcher, parked, sweep, yolo, epic, stage, epoch, adversarial review, squash-landed, mode vs skill level vs noob, managed block, harness, worktree-first). Explain once that "command" and "skill" refer to the same thing depending on the editor. Optionally add glossary tooltips site-wide via `abbr` + snippets. See review §5, §13.
- Goal: every term above is defined on one page, and the other pages link to it at first use on Home, Getting started, and the How-to index.
- Model: deep
- Depends on: #346
- yolo: no — new explanatory content; accuracy needs careful review.
- Published: #347

### Issue: docs: slim the home page and unify the quick start

- Spec: Rewrite `docs/index.md` as: a concrete benefit statement (replacing the current "Why" section), a small lifecycle overview, three entry points (New to issue-flow → Getting started; Want to do X → How-to; AI agent → For agents / llms.txt), and an install one-liner. Move the recipes into the How-to index. Use one canonical quick start (`iflow pick → plan → build → close → cleanup`) on Home, Getting started and README. Make the file tree editor-neutral, or put it in tabs per editor (`pymdownx.tabbed`). See review §3, §12.
- Goal: the home page fits roughly one screen plus the entry points, and Home, Getting started and README show the same quick start.
- Model: deep
- Depends on: #347
- yolo: no — the home page is the project's front door, so wording and tone need the user's judgement.
- Published: #348

## Outcome (drive run, 2026-09-24)

Run with `/iflow-drive 341` (draft already confirmed; Stage 2 published during the drive). Run records: `01-current-issues/auto_status.md`, `03-solved-issues/drive_status_2026-09-24_epic341.md`, and `03-solved-issues/cycle_status_2026-09-24_epic341-*.md`.

- **Stage 1:** done. #342 → PR #350, #343 → PR #351, #344 → PR #352.
  - The adversarial review (loop 1) found 6 dead external links, including `iflow-graphify.net` in the shipped templates. Blocker #353 → PR #354. Loop 2: clear.
- **Stage 2:** done. #346 → PR #355, #347 → PR #356, #348 → PR #357. Adversarial review: clear.
- **Epic goal:** parts (1)–(3) met. Part (4) (reference pages) is still open.
- **Final review:** created the remaining work as issues. They cover goal part (4) and the anchor's acceptance items. These supersede the "Later" bullets below.
  - #358 — command reference restructure, editor-neutral (goal part 4)
  - #359 — configuration page reorder + full knob table (goal part 4)
  - #360 — troubleshooting page
  - #361 — diagrams
  - #362 — how-tos for fix / issue / split / ops / drive
  - #363 — annotated sample session
- **Tool bug found during the run:** #364. `agent queue` reported Stage 2 as blocked by the closed Stage 1 issue #344, so the stage order was derived by hand.
- **Design note:** [docs-link-check.md](../04-designs-and-guides/docs-link-check.md).

## Later (unstaged)

_Superseded by #358–#363 (see Outcome)._


- **Command reference restructure (§6):** make the site render of
  `issue-workflow.md.j2` editor-neutral, retitle it "Command reference",
  drop the `0a/1a/8b` numbering, group commands (Core loop / Starting work /
  Helpers / Automation / Maintenance), keep one table (command · purpose ·
  on/off path · modes), give every command the same section layout
  (When / Arguments / What it does / What it asks you / Result / Related), and
  remove changelog wording. Large; likely 2 issues (template restructure,
  then site-specific render or tabs).
- **Configuration page (§7):** start with a "Common changes" table, then a
  full table of every setting (generated from code if feasible), move
  precedence / user-global / registry to the end, and drop issue-number
  references.
- **Troubleshooting page (§8):** symptom → cause → fix entries for common
  first-hour failures.
- **Diagrams (§9):** lifecycle state machine, folder moves, epic flow.
  Decide between Mermaid and committed SVGs.
- **Missing how-tos (§10):** fix, issue, split, ops, drive.
- **Sample session (§11):** annotated transcript of pick → plan → build →
  close, with an example `issue<N>_plan.md`.
