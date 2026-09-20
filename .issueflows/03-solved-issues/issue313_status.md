# Status: #313 Iterative fixes: workspace docs

Interactive `/iflow-fix` session.

- [x] Done

## Iterative fixes log

- 2026-09-20: User-facing workspace how-to (`docs/how-to/workspaces.md`) with copy-paste `bootstrap` / `init` / `update` recipe; wired into how-to nav, getting-started, CLI reference (`workspace update` heading + synopsis), editors, README, and workflow doc.
- 2026-09-20: `/iflow-init` skill + command templates point at https://issue-flow.readthedocs.io/how-to/workspaces/ and the same bootstrap / init / update table so agents follow the public recipe.
- 2026-09-20: CLI reference opens with grouped glance tables (setup / workspace / inspect / config / agent) and fold-away full synopsis; command headings have stable anchors.
- 2026-09-20: Enable Typer shell completion on the root app (`issue-flow --install-completion`); document it; keep nested apps without the extra flags.

## What's done

- Session captured.
- First doc pass: parent-folder workspace recipe is findable from the docs home, getting started, CLI, editors, and README.
- `/iflow-init` now sends agents to that how-to.
- CLI reference overview is grouped tables, not a flag dump.
- Tab completion: `issue-flow --install-completion` (bash / zsh / fish).
- Closed as 0.5.6.post1.

## Remaining work

None.
