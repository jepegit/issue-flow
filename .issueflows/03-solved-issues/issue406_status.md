# Status — issue #406

- [x] Done

## What's done

- **Command surface:** 30 lifecycle skills → 11 commands with modes (`iflow`, `setup`, `pick`, `plan`, `build`, `pause`, `close`, `cleanup`, `run`, `issue`, `status`). Mode content lives in side files next to each `SKILL.md` (progressive disclosure). `gh-ci`, `comments`, `version-bump`, `history-update` became mode files.
- **Context diet:** rule body ~4,500 → ~680 words; `CLAUDE.md` imports `AGENTS.md`; Cursor `.mdc` is a pointer; scaffolded workflow doc ~8,400 → ~640 words; 26 full command copies replaced by one wrapper template (opencode only; Claude Code is skills-first). Shared partials (project-root resolution, noob footer, default-sync recovery) compressed. References to this repo's internal design docs and issue numbers removed from templates; the auto review criteria are inlined.
- **Migration:** `issue-flow update` prunes retired folders and command files (project, canonical store, stamped user-global), rewrites retired stems in `config.toml` (modes, step profiles; conservative `remove` semantics), drops stale stamps, and upserts the Linguist block. `doctor` reports kept retired folders as `retired_editor_skill`. Verified end to end: scaffolded a demo with the `main` release (`-e all`), ran the new `update` once, second run is a no-op.
- **Repo noise:** Linguist block marks editor copies and archived issue folders `linguist-generated`; `graphify-out/` gitignored and untracked here; 52 design docs consolidated into 12 topic files (content kept, links updated); decision recorded in `lifecycle-and-commands.md`.
- **Docs:** README, concepts, editors, configuration, CLI, getting-started, how-to pages, `llms.txt` updated; site builds clean.
- **Tests:** new `test_command_surface.py` (surface, word budgets, no retired names) and `test_migrate.py`; obsolete content tests replaced. `uv run pytest` (946 passed) and `uv run ruff check src/ tests/` pass.

## Remaining work

- None for this issue. Follow-ups worth considering: collapse the three issue files into one; trim `cycle.md` / `epic.md` further.
