# Status — Issue #219: just build the thing when the plan is accepted

- [ ] Done

## What's done

- Plan accepted (`auto_plan` + `auto_build`, defaults true, `noplan`/`nobuild`).
- Knobs wired in `modes` / `config` / cli / agent blurb.
- Pick + plan templates (skill + command) + issue-workflow wording.
- `skill-behaviour-knobs.md` + `docs/configuration.md`.
- `.issueflows/config.toml` explicit `auto_plan` / `auto_build`.
- Dogfood `issue-flow update`; 574 tests passed.

## Remaining work

- HISTORY / ready-for-review via `/iflow-close`.
