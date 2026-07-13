# Multi-editor conversion

Context: issue #23 — teams where developers use different AI coding tools need
a shared git layout and local materialization of editor-specific surfaces.

## Decision

- **Canonical store in git:** `.issueflows/agent/skills/` (rendered `SKILL.md`
  snapshots) + `manifest.json` + existing `.issueflows/` issue tracking +
  `AGENTS.md` managed block.
- **Generated locally:** per-editor trees (`.cursor/`, `.claude/`, `.opencode/`,
  `.codex/`), optional `CLAUDE.md`, workflow doc under `docs/`.
- **CLI:** `issue-flow convert --to <editor|canonical>` with `--prune-other` and
  `--gitignore`. `issue-flow init --canonical` bootstraps the team workflow.
- **Standards:** Agent Skills (`SKILL.md`, agentskills.io) is the portable core;
  no universal format exists for rules/commands — issue-flow renders those per
  profile from the shared template tree ([editor-profiles.md](editor-profiles.md)).

## Solo vs team

| Workflow | Init | Git commits |
| --- | --- | --- |
| Solo (default) | `issue-flow init` | `.cursor/` (or chosen editor) as today |
| Team | `issue-flow init --canonical` | `.issueflows/agent/` + `AGENTS.md`; editor dirs gitignored |

## Deferred

- Opt-in git hooks (`post-checkout` → local editor, `pre-push` → canonical) —
  phase 2 of #23; compose separately from #101 issue-file hooks.
- Windsurf `EditorProfile` (#17).

## Link

- Issue: [#23](https://github.com/jepegit/issue-flow/issues/23)
