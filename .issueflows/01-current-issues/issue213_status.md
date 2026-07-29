# Status — Issue #213: option for using essential tests

- [ ] Done

## What's done

- Plan accepted (recommended defaults).
- Design contract: `.issueflows/04-designs-and-guides/essential-tests.md` + once-seed templates.
- Living registry seed: `test-registry.md` (never overwrite on update).
- Knobs: `essential_tests`, `test_runner`, `essential_marker`, `essential_review` wired through modes/config/init/cli/docs.
- Skill/command hooks: close (sanity + review), build (review when build/both), doctor (optional full audit).
- Docs: `docs/configuration.md`, `skill-behaviour-knobs.md`.
- Tests: config/modes/templating/cli/init/update — full suite green (584).
- Dogfood: `issue-flow update .` refreshed scaffolds (feature off by default → wording gated).

## Remaining work

- HISTORY Unreleased bullet + PR via `/iflow-close`.
- Optional follow-ups (out of scope): dogfood CI split for this repo; workflow writer CLI.
