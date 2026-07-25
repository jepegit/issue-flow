# `gh repo view` takes a positional repo

**Context.** Issue #216: agents (and one skill template) called
`gh repo view --repo owner/name`, which fails with `unknown flag: --repo`.
Separately, Windows locale decoding in `gitutils._run` crashed on UTF-8
`gh issue view` output.

**Decision.**

- Document and teach: `gh repo view <owner/repo> --json …` (positional).
- Keep `--repo <owner/repo>` for other `gh` commands (`issue`, `pr`, `label`, …).
- Scaffolded resolve-root snippet and `/iflow-cleanup` skill state the exception
  explicitly; `gitutils._run` always uses `encoding="utf-8", errors="replace"`.

**Alternatives considered.**

- Wrap every default-branch lookup in `issue-flow agent preflight` only —
  rejected as sole fix; agents still shell out to `gh` in manual fallbacks.
- Force `PYTHONUTF8=1` / `PYTHONIOENCODING` in the environment — helpful but
  not under our control on every machine; fix the wrapper instead.

**Link.** Issue #216, `issue216_plan.md`.
