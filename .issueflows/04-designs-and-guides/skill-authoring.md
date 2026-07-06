# Skill authoring — house rules

Context: issue [#117](https://github.com/jepegit/issue-flow/issues/117). We adopted
mattpocock's **writing-great-skills** reference (vendored verbatim, MIT, at
`.cursor/skills/writing-great-skills/` — `SKILL.md` + `GLOSSARY.md`) as the
standard for every skill issue-flow ships. Read it before editing any template
under `src/issue_flow/templates/skills/`.

## Decision

All shipped skills follow the vendored reference. Templates are the single
source of truth; edit `SKILL.md.j2`, then re-render with `issue-flow update`.

## House rules (distilled for issue-flow templates)

- **Invocation.** Lifecycle skills (`iflow-*`) are **user-invoked**
  (`disable-model-invocation: true`): their `description` is a one-line,
  human-facing summary — no trigger lists ("Use when the user mentions…"),
  those belong only to model-invoked skills. Only `caveman` and `grill-me`
  are model-invoked and keep trigger-rich descriptions.
- **No trigger-bait "When to use" sections in user-invoked skills.** Keep
  genuinely behavior-bearing lines (e.g. "off-path: never auto-dispatch from
  /iflow"); drop lines that only restate invocation triggers.
- **Single source of truth.** Shared material lives in one place and is
  reached by a context pointer (e.g. `iflow-init` points at `iflow-comments`
  instead of inlining a rules summary).
- **Prune no-ops and sediment.** Sentence-level test: does the line change
  behavior versus the model's default? If not, delete the sentence (e.g.
  "Use UTF-8 for markdown output").
- **Sharpen completion criteria.** Prefer checkable, exhaustive bounds
  ("every group moved and reported") over vague ones ("handle the folder").
- **Behavior is sacred.** Pruning must preserve workflow semantics:
  confirmations, off-path markers, `- [x] Done` rules, file-movement rules,
  output contracts.
- **Jinja stays intact.** Keep `{{ issueflows_dir }}`-style variables and the
  `_model_directive.md.j2` include; verify rendering with
  `uv run .issueflows/00-tools/verify_scaffold.py`.

## Alternatives considered

- Scaffolding the reference into target projects: rejected — it guides
  maintainers of this repo, not users of scaffolded projects.
- Plain doc under `04-designs-and-guides/` instead of a vendored skill:
  rejected — placing it under `.cursor/skills/` keeps it reachable while an
  agent edits skill templates, at zero context load (user-invoked).

## Known debt

- `templates/commands/*.md.j2` duplicate skill content wholesale (~1070
  lines) — a single-source-of-truth violation. Tracked as a follow-up issue
  candidate; do not fold command restructuring into unrelated PRs.
