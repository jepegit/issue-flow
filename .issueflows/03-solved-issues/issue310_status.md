# Status: #310 Global iflow initialisation

- [x] Done

## What's done

- CLI `issue-flow workspace bootstrap` — classify-only by default; `--yes` inits unscaffolded own-git children then `workspace init`.
- `classify_immediate_children` — own-git top-level only; skip non-git / enclosing / symlinks. No parent `.issueflows/`, no `git init` of children.
- `/iflow-init` skill + command: parent-folder branch, then single-project path. `iflow_init` is now a `both` stem.
- Design docs: `global-vs-local-skills.md`, `multi-repo-workspaces.md`, `iflow-init-vs-capture.md`, `user-global-config.md`.
- Tests: bootstrap classify / `--yes` / default-required / no-git; classify unit tests; skill still not capture. `uv run pytest` 798 passed.

## Remaining work

- None.
