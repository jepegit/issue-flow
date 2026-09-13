---
title: Use pstack skills
---

# Use pstack skills

## Goal

Opt into a **curated subset** of
[pstack](https://github.com/cursor/plugins/tree/main/pstack) skills next to the
`iflow-*` skills — same invocation names as upstream (`/unslop`, `/tdd`, …),
refreshed by `issue-flow update`. Off by default; nothing runs unasked.

## Steps

1. Pick which skills you want (upstream names):

   | Skill | When |
   | --- | --- |
   | `unslop` | Cut AI tells from PR bodies, HISTORY bullets, issue specs, docs |
   | `tdd` | Bug with a cheap local test path — failing test first, then fix |
   | `blast-radius` | Small-looking diff might break elsewhere; prove safety by running code |
   | `technical-writing` | Docs, READMEs, RFCs, PR descriptions, commit messages |
   | `bro` | Restate the last message in plain language |
   | `principle-prove-it-works` | Verify against the real artifact before declaring done |
   | `principle-subtract-before-you-add` | Remove or simplify before adding |
   | `principle-fix-root-causes` | Fix the cause, not the symptom |
   | `principle-test-behavior-not-implementation` | Keep tests on observable behaviour |

2. Set the selection in `.issueflows/config.toml`, then re-render:

   ```toml
   [issueflow]
   pstack_skills = ["unslop", "tdd", "blast-radius"]
   # or: pstack_skills = "all"
   ```

   ```bash
   issue-flow update
   ```

   Env fallback: `ISSUEFLOW_PSTACK_SKILLS=unslop,tdd` (config wins).
3. Invoke like any other skill — slash or chat form matching the upstream
   name, e.g. `unslop`, `/tdd`. Folders land at
   `<agent_dir>/skills/<name>/SKILL.md`.
4. During `/iflow-build` / `/iflow-close`, the agent may *suggest* `tdd`,
   `blast-radius`, or `unslop` when those skills are installed — confirm or
   skip; they never auto-run.
5. To drop a skill: remove it from the list (or clear the key) and
   `issue-flow update` again — that folder is pruned.

Skills that need Cursor multi-model subagents, MCP, or pstack's own lifecycle
(`poteto-mode`, `interrogate`, `arena`, …) are **not** vendored. Install the
full Cursor plugin for those; same-named skills can coexist with the opt-in
set.

## Related

- [Configuration — pstack skills](../configuration.md#pstack-skills)
- [Fast-track a small issue](yolo.md) — close may still offer unslop outside yolo
- [Acknowledgements](../acknowledgements.md) — upstream attribution
