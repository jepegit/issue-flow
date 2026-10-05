# Status — issue #402

- [x] Done

## What's done

- `issue-flow mode hands-off` writes `[issueflow].hands_off` and re-renders skills. `issue-flow mode` prints the value. `issue-flow mode standard` (alias `off`) turns it off. Turning it on asks once unless `--yes`.
- While the knob is on, `/iflow-drive`, `/iflow-yolo`, `/iflow-cycle`, and `/iflow-auto` skip their up-front confirms. A short description on drive runs grill-me, creates one epic anchor, then drives that number. AST graphify runs before the epic draft and each child plan. A spent auto loop budget records accept.
- Direct `/iflow-pick`, `/iflow-plan` Accept, `/iflow-build`, and ordinary `/iflow-close` still ask.
- Design note: `.issueflows/04-designs-and-guides/hands-off-mode.md`.
- Version `0.5.17` → `0.6.0` (`uv version --bump minor`). `HISTORY.md` promoted to `0.6.0`.
- Planned GitHub release: `v0.6.0`. Requested at close (`bump minor and release`). Create it after this PR merges onto `main` with `gh release create v0.6.0 --generate-notes`. Do not tag the issue branch. That release starts `.github/workflows/publish.yml`.
- Essential review: new tests left unmarked (text and config contracts). `test_all_settings_table_lists_every_config_key_once` stays essential and covers the new knob. Registry updated.
- `uv run pytest -m essential`: 24 passed. Full suite earlier this session: 969 passed. `ruff check`: clean.
- Graphify rebuild outputs (`GRAPH_REPORT.md`, `manifest.json`, `.graphify_labels.json`, `.graphify_root`) left unstaged. `.graphify_root` is a local worktree path.

## Remaining work

- After the PR merges, create the GitHub release `v0.6.0` (PyPI publish), then `/iflow-cleanup`.
