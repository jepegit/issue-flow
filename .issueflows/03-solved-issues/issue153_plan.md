# Issue #153 plan: possible misplacement of mode information

## Goal

Resolve whether the **Scaffolding modes** sub-chapter in [docs/developing.md](../../docs/developing.md) belongs there, and fix doc placement so user-facing mode docs live in one place while contributor docs stay contributor-focused.

## Constraints

- Docs-only change — no code or template behaviour changes.
- [docs/configuration.md](../../docs/configuration.md) is already the canonical **user** reference for modes (linked from [docs/index.md](../../docs/index.md) and README).
- [docs/developing.md](../../docs/developing.md) audience is **contributors to issue-flow itself** (clone, `uv sync`, test, release) — not end users choosing `--mode simple`.
- Preserve accurate contributor pointers to `modes.py`, `modes.toml`, and template membership gating; do not delete information that exists nowhere else in published docs.
- Keep tone and formatting consistent with neighbouring developing.md sections (horizontal rules, `uv run` examples where relevant).

### Prior art

- [docs/configuration.md § Modes](../../docs/configuration.md#modes) — full user-facing modes reference (standard vs simple, persistence, resolution order, custom modes). Added/refined in later docs work (#127 area); now the right home for “what is a mode?”
- [docs/developing.md § Scaffolding modes](../../docs/developing.md) — ~45 lines added in #48 commit `a4d9a0d`; largely duplicates configuration.md plus a “Defining modes (developers)” tail. Listed explicitly in [issue48_status.md](../03-solved-issues/issue48_status.md) as intentional at ship time, but redundant after configuration.md matured.
- [docs/developing.md § Project structure](../../docs/developing.md) — already lists `modes.py` and `modes.toml` in the tree (good; keep).
- [.issueflows/04-designs-and-guides/modes.md](../04-designs-and-guides/modes.md) — internal design note for #48; not published; too deep for developing.md but useful background for this plan.
- `tests/test_modes.py` — mode registry/resolution/persistence tests; mention in dev section as “where to test changes”.
- Toolbox + graph checked — no reusable helper; graph communities touch modes tangentially only.

## Approach

**Verdict:** placement in developing.md was **intentional when #48 landed**, but is **now a mistake** — duplicate user docs that belong in configuration.md. The section should be **replaced**, not deleted wholesale.

1. **Remove** the duplicated user content from developing.md:
   - standard vs simple bullet list
   - `init --mode simple` usage example
   - persistence / resolution-order paragraph (already in configuration.md)
   - “Custom modes (users)” TOML example (already in configuration.md)

2. **Replace** `## Scaffolding modes` with a short **`## Working on scaffolding modes`** (or similar) contributor subsection (~12–18 lines):
   - One-line pointer: end-user semantics → [Configuration → Modes](configuration.md#modes).
   - **Package maintainers:** built-in mode definitions in [`src/issue_flow/modes.toml`](../../src/issue_flow/modes.toml); resolver/registry/persistence in [`src/issue_flow/modes.py`](../../src/issue_flow/modes.py).
   - **Templates:** surfaces gate on `included_skills` / `included_commands` membership, not mode id — when adding a skill/command, update templates accordingly (see existing design note mentally; no need to link `.issueflows/` from published docs).
   - **Smoke test:** `uv run issue-flow init /tmp/test-project --mode simple` (already echoed in Quick reference; optional one-liner here).
   - **Tests:** `uv run pytest tests/test_modes.py` (and related init/update tests if touching manifest filtering).

3. **No change** to configuration.md content unless a cross-link back to developing is desired (optional; see Open questions).

4. **No nav change** — `zensical.toml` already separates Configuration vs Developing correctly.

## Files to touch

| File | Change |
| --- | --- |
| [docs/developing.md](../../docs/developing.md) | Replace `## Scaffolding modes` block (lines 84–126) with trimmed contributor subsection + link to configuration.md |
| [docs/configuration.md](../../docs/configuration.md) | Optional one-line “Package maintainers: see [Developing → Working on scaffolding modes](developing.md#working-on-scaffolding-modes)” under `## Modes` |

## Test strategy

- `uv run zensical build` — confirm docs site builds and anchor links resolve (if zensical is in dev deps; else manual review of markdown links).
- No pytest changes expected (docs-only).
- Visual skim: developing.md reads as contributor guide; configuration.md still complete for users.

## Open questions

1. **Section title / depth** — OK to replace with slim “Working on scaffolding modes” as above, or prefer **zero** dedicated section (rely only on Project structure tree + configuration link)?
2. **Reverse cross-link** — add maintainer pointer from configuration.md → developing.md, or keep configuration user-pure?
