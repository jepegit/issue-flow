# Plan — Issue #179: Review docs

## Goal

Make the published docs (and README) accurately describe today’s workflow —
especially **epics**, **cycles**, and **reviews** — with enough concrete
examples that a new user can run those flows without reading skills. Then
**bump patch** on close for a release.

## Constraints

- Site docs live under `docs/` (Zensical / RTD); scaffolded project overview is
  `src/issue_flow/templates/docs/issue-workflow.md.j2` (dogfooded into
  `docs/issue-workflow.md` via `issue-flow update`). Edit the **template** for
  workflow content that ships to user projects.
- Hand-maintained site pages: `docs/index.md`, `README.md`,
  `docs/configuration.md`, `docs/cli.md`, etc. — update in place.
- Prefer expanding existing pages over a large new IA; one optional short
  recipes section is OK.
- Do not invent new product behaviour — documentation only (+ patch bump at
  close).
- Keep tone consistent with current docs (direct, example-led).

### Prior art

| Hit | Path | Stance |
| --- | --- | --- |
| Scaffolded workflow doc | `templates/docs/issue-workflow.md.j2` | **Primary** surface for epic/cycle/review walkthroughs |
| Site home + README | `docs/index.md`, `README.md` | **Update** off-path lists + recipes |
| Design notes | `04-designs-and-guides/label-driven-flows.md`, `issue-review-labelling.md`, `parallel-cycle.md` | **Cite** in examples; don’t duplicate full design |
| CLI reference | `docs/cli.md` (`agent epic-status`, `queue`, `label-*`) | **Cross-link** from cycle/epic/review sections |
| Toolbox | `00-tools/` | None for docs writing |

### Audit findings (read-only)

Gaps that this issue should close:

1. **`docs/index.md` / `README.md`** — quick-start off-path lists omit
   `/iflow-epic`, `/iflow-cycle`, `/iflow-review`, `/iflow-doctor`.
2. **`issue-workflow.md` (template)** — has `/iflow-review` section (§11) but
   **no dedicated epic or cycle sections** with steps/examples; Agent Skills
   table omits `iflow-epic` / `iflow-cycle`; “Not auto-dispatched” list omits
   epic/cycle; end-to-end detours omit epic.
3. **Examples** — no worked recipe for: epic draft→confirm→publish; cycle
   `yolo` / `label:…`; review → cycle handoff.
4. **Release** — issue explicitly asks for **patch bump** at close.

## Approach

1. **`issue-workflow.md.j2`**
   - Add numbered sections for **`/iflow-epic`** and **`/iflow-cycle`** (with
     When / What you pass / What the assistant does / Off-path / Result),
     including short **Example** blocks (commands + expected outcomes).
   - Keep/refresh **`/iflow-review`** section; add example
     `iflow review yolo` → confirm → `iflow cycle yolo`.
   - Fix Agent Skills table rows for epic + cycle; fix “Not auto-dispatched”
     and Detours to include epic/cycle/doctor as appropriate.
   - Renumber archive section if needed after inserts.
2. **`docs/index.md`**
   - Extend off-path list in Quick start.
   - Add a **Recipes** subsection (3–5 bullets): linear issue; yolo one-shot;
     review+cycle all yolo; epic stage publish; pick front door — each 2–4
     lines with commands.
3. **`README.md`**
   - Mirror the off-path list + a short “See docs for epics/cycles/reviews”
     pointer (keep README lean; full examples live on the site).
4. **Light touch elsewhere** (only if clearly stale while editing above):
   - `configuration.md` label-driven-flows blurb → mention cycle `yolo` alias
     and `/iflow-review` if missing.
   - Dogfood: `uv run issue-flow update . --skip-dep-check` so
     `docs/issue-workflow.md` matches the template.
5. **Close** with `/iflow-close bump patch` (HISTORY promote + version bump).

### Out of scope

- Rewriting developing.md / graphify.md / full CLI rewrite.
- New skill/command behaviour.
- Multi-language docs or video tutorials.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Epic + cycle sections, examples, table/list fixes |
| `docs/issue-workflow.md` | Via `issue-flow update` (dogfood) |
| `docs/index.md` | Off-path list + Recipes |
| `README.md` | Off-path list + docs pointer |
| `docs/configuration.md` | Optional one-paragraph cross-links |
| `tests/test_templating.py` or `test_init.py` | Light asserts that scaffolded workflow mentions epic/cycle examples |
| Close: `pyproject.toml` / lock / `HISTORY.md` | Patch bump |

## Test strategy

- `uv run pytest` — add/adjust template contract tests that rendered
  `issue-workflow.md.j2` contains `/iflow-epic`, `/iflow-cycle yolo`, and an
  example-ish invocation (`iflow review yolo` or `iflow cycle yolo`).
- Manual: skim RTD build locally if easy (`uv run zensical build`) — optional,
  not blocking if env lacks zensical extras.
- No behaviour tests beyond docs contracts.

## Open questions

_Resolved 2026-07-18 — plan accepted with recommended defaults:_

1. **Recipes on `docs/index.md`** (no new nav page) — confirmed.
2. **Short epic recipe** in workflow doc (no sample plan file) — confirmed.
3. **Patch bump same PR** via `/iflow-close bump patch` — confirmed.

**Status:** accepted — ready for `/iflow-start`.
