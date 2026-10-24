# Issue #268 status: Improve skills

- [x] Done

Plan accepted 2026-10-24 with the recommended answers: lint in `doctor`, negation pass on routers only, third-person descriptions, one PR. The user dropped the video mid-build. Its captions returned HTTP 429 on two tries.

## What's done

- **Reference refresh.** Replaced the vendored `.cursor/skills/writing-great-skills/` with `.cursor/skills/writing-for-agents/` (`SKILL.md` + `SKILL-MECHANICS.md`, verbatim from mattpocock/skills `5beb35b`, MIT provenance, `disable-model-invocation: true` added).
- **House rules.** `skills-and-styles.md#skill-authoring` has the new pointers and seven new rules (positive over prohibition, do not cache the environment, one-hop reference, branch-only reference, contents lists, third-person tag-free descriptions, lint as gate). The #268 decision record is there too, and the #275 survey rows are marked done.
- **Lint.** New `src/issue_flow/skill_lint.py` (frontmatter parser with no YAML dep, `lint_skill`, `lint_skills_root`). `agent.audit_skill_spec` is wired into `_audit_payload`, so `issue-flow doctor`, `agent audit` and `/iflow-status doctor` all report `skill_spec_*`. Packaged skill errors are error, user skill errors are warn, hints are info. Documented in `docs/cli.md` and `iflow_status/doctor.md.j2`.
- **The lint found real bugs.** Four lifecycle descriptions (`iflow`, `iflow-pick`, `iflow-plan`, `iflow-run`) contained `<N>`-style XML tags. Fixed.
- **Template pass:**
  - Third-person descriptions for all 11 lifecycle skills.
  - `iflow-pick`: the router now names `capture.md` and `comments.md` directly, and `capture.md` no longer tells the agent to read `comments.md` (one hop).
  - `**Contents:**` lines on the 5 side files over 100 lines (`version`, `epic`, `auto`, `cycle`, `drive`).
  - The PowerShell body-file block became the one-line `_gh_body_file_short.md.j2` inside the `pick` step 5 and `build` step 8 bullets. The full block stays in close and the mode files.
  - The "`issue-flow` is only present when the user installed it" sediment is gone from 5 skills.
- **Negation pass** (13 routers + caveman + grill-me + shared partials): router prohibitions went from 102 to 32. Rendered skill words went from 31209 to 31018. Per file:
  - iflow: 10 hits — 7 converted, 2 removed (dup of Constraints), 1 kept as guardrail (no silent pick, paired with ask)
  - build: 9 hits (+2 bold) — 8 converted, 2 removed (dup of Constraints), 1 kept as guardrail (branch delete/force-update)
  - plan: 8 hits (incl. bold) — 8 converted (two Constraints merged into one line)
  - pause: 5 hits — 3 converted to one positive scope line, 2 kept as one guardrail line (destructive git) paired with keep-everything
  - pick (+ _worktree_start partial): 16 hits — 13 converted, 1 removed (dup of Constraints), 2 kept as guardrails (confirm before create; no force-push/branch delete)
  - close: 13 hits — 9 converted, 1 removed (dup), 3 kept as guardrails (HISTORY on issue branch; bare --force/default branch; --admin/skip CI/force-push scope)
  - cleanup: 14 hits — 5 converted, 9 kept as guardrails (branch -D scope, unique_work, default-branch push/rebase/delete, worktree removal, A1/A2 confirm separation)
  - setup: 9 hits — 6 converted, 3 kept as guardrails (gh auth login interactive; never install uv/gh; no uv init over a project)
  - issue: 3 hits — 2 converted, 1 kept as guardrail (explicit yes on exact text before create/edit/label)
  - run: 4 hits — 2 converted, 1 kept as guardrail (dirty tree / failing baseline), 1 removed (no-op "Do not guess")
  - status: 2 hits — 2 converted
  - caveman: 4 hits — 4 converted (self-reference rule rewritten positively; the banned example phrases are no longer spelled out)
  - grill-me: 1 hit — converted
  - shared partials included by routers (_essential_tests_*, _noob_next, _default_sync_recover, _worktree_close_remove): 8 hits — 5 converted, 3 kept as guardrails (never silent-push; never --force worktree; never delete the issue branch in close)
- **Tests.** New `tests/test_skill_lint.py` (21 tests):
  - parser shapes and every check;
  - a guard that renders every packaged skill for every editor with pstack all, with zero errors or warnings;
  - the one-hop reference rule;
  - doctor severity and exit code.

  Updated tests that pinned the old prohibition wording to pin the positive wording. Two doctor fixtures now write valid frontmatter in their stub `SKILL.md`.
- **Verification.**
  - `uv run pytest`: 967 passed.
  - `uv run ruff check src/ tests/`: clean.
  - `uv run issue-flow doctor .`: no errors and no `skill_spec_*` findings. The only info finding is the vendored `writing-for-agents` being unmanaged, as expected.

## Remaining work / follow-ups (not in this PR)

- Negation pass over the 26 mode files (195 prohibitions): #410 (`yolo`).
- `.issueflows/00-tools/verify_scaffold.py` is stale since #406: 38 checks fail **identically on `main`** (they expect `.claude/commands/*.md` and retired names). Tracked in #409 (`yolo`).
