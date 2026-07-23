# Issue #99 — status

- [ ] Done

## What's done

- Plan accepted and implemented
- `[issueflow] early_pr` wired in `config.py` / `modes.py` (default `false`, env `ISSUEFLOW_EARLY_PR`)
- `/iflow-build` early-PR step + trailing `early`/`pr`/`noearly`
- `/iflow-close` draft token formalized (`--draft`, `gh pr ready`, skip yolo merge)
- Yolo/docs/rules/history-update cross-refs; design docs `early-pr.md` + knobs/changelog updates
- Tests + `verify_scaffold.py` markers; `uv run pytest` green (553)

## Remaining work

- `/iflow-close` to land HISTORY + final PR body (`Closes #99`)
