# Issue #406: Cut noise: thin always-on context, merge commands into modes, quieter repo diffs

Source: https://github.com/jepegit/issue-flow/issues/406

## Original issue text

## Context

issue-flow has become noisy in three ways:

1. **Context noise.** The always-on rule (`templates/rules/_body.md.j2`) renders to ~4.5k words and loads into every agent session. About half of it re-describes off-path commands, there is a ~30-row chat-invocation table, and config knobs are explained inline. Several skills are huge (`close` 3.8k words, `cleanup` 3.0k, `cycle` 2.7k), so the important lines get buried. The scaffolded `docs/issue-workflow.md` is ~8.4k words.
2. **Command-surface noise.** 30 `iflow-*` skills (plus `gh-ci`). Several are one concept split by size or scope (`yolo`/`cycle`/`auto`/`drive`; `issue`/`fix`/`epic`/`split`; `status`/`doctor`/`workspace-git`), and some internal steps are exposed as commands (`comments`, `version-bump`, `history-update`).
3. **Repo/git noise.** Over the last 40 commits, `graphify-out/` churn (~13.7k lines) and `.issueflows/` (~5k) outweigh source changes. Rendered editor copies double every template diff in PRs. There are 52 design docs, roughly one per feature.

## Spec

Breaking changes are allowed. No aliases. **`issue-flow update` must migrate an existing project in one run** (prune retired skill/command files, rewrite config stems, refresh managed blocks) so the new version works with nothing else to do.

### Command surface (merged commands with modes)

| New | Absorbs | Modes |
|---|---|---|
| `iflow` | `iflow` | dispatcher |
| `iflow-setup` | `setup`, `init` | readiness + harness |
| `iflow-pick` | `pick`, `capture`, `comments` | `pick`, `pick <N>` |
| `iflow-plan` | `plan` | |
| `iflow-build` | `build` | |
| `iflow-pause` | `pause` | |
| `iflow-close` | `close`, `ops`, `version-bump`, `history-update`, `gh-ci` | `close`, `close yolo`, `close ops`, … |
| `iflow-cleanup` | `cleanup`, `pr-sync`, `archive` | `cleanup`, `cleanup prs`, `cleanup archive`, … |
| `iflow-run` | `yolo`, `cycle`, `auto`, `drive` | `run yolo <N>`, `run cycle <spec>`, `run auto <N>`, `run drive <N>` |
| `iflow-issue` | `issue`, `fix`, `epic`, `split`, `review` | `issue`, `issue fix`, `issue epic <N>`, `issue split <N>`, `issue review` |
| `iflow-status` | `status`, `doctor`, `workspace-git`, `graphify` | `status`, `status doctor`, `status git`, `status graph` |

Behaviour skills `caveman` and `grill-me` stay; optional pstack skills stay.

Merged skills use **progressive disclosure**: a short `SKILL.md` router plus mode files in the same skill folder, read only when that mode runs.

### Context diet

- Always-on rule body cut to the core: what `.issueflows/` is, the core loop, the Done checkbox, branch hygiene, a one-line chat-invocation rule, and a compact command list.
- Scaffolded workflow doc cut to a short reference.
- Word-budget tests guard the rule, each `SKILL.md`, each mode file, and the workflow doc.

### Repo noise

- The managed Linguist block marks rendered editor surfaces and archived issue folders `linguist-generated` (collapsed in PR diffs), and `update` refreshes the block in place.
- This repo: gitignore `graphify-out/` (via `graphify_gitignored`) and untrack it.
- This repo: consolidate `.issueflows/04-designs-and-guides/` into topic docs. Templates stop pointing at this repo's internal design docs.

## Acceptance criteria

- [ ] At most 11 lifecycle skills (plus `caveman`, `grill-me`, optional pstack) in the `standard` mode.
- [ ] `issue-flow update` on a project scaffolded by the previous release removes every retired skill/command folder that issue-flow owns, rewrites old stems in `config.toml` (custom modes, step profiles), and leaves a working scaffold. Covered by a test.
- [ ] The rendered always-on rule is ≤ 900 words with every optional section on. Covered by a budget test.
- [ ] Every `SKILL.md` ≤ 1,600 words and every mode file ≤ 3,000 words. Covered by a budget test.
- [ ] No template or doc references a retired command name.
- [ ] Linguist block covers editor surfaces and archived issue folders, and is upserted on update.
- [ ] Docs site updated for the new surface. `uv run pytest` and `uv run ruff check src/ tests/` pass.
