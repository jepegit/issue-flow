# Slash-less iflow invocation

Context: issue [#118](https://github.com/jepegit/issue-flow/issues/118).

## Problem

Cursor lifecycle skills are invoked explicitly (`disable-model-invocation: true`).
The slash menu requires `/iflow-plan`. On some keyboard layouts (Norwegian called
out in the issue) `/` is awkward; `@` attachment is awkward too.

## Decision

**Primary chat form:** `iflow <step>` (space-separated) — e.g. `iflow plan`,
`iflow pick`, `iflow close`. Plain `iflow` runs the dispatcher.

**Aliases:** hyphen (`iflow-plan`), slash (`/iflow-plan`), slash + space
(`/iflow plan`).

**Mechanism:** always-on rules in `templates/rules/_body.md.j2` (rendered into
`AGENTS.md` and `.cursor/rules/issueflow-rules.mdc`) instruct agents to treat
matching chat text as explicit skill invocation. Lifecycle skill bodies include
a one-line **Invoke** hint via `templates/skills/_invocation_forms.md.j2`.
`docs/issue-workflow.md` documents the space form first.

Skill folder names and YAML `name:` fields stay hyphenated (`iflow-plan`).

## What we did not do

- Remove `disable-model-invocation` (would auto-load heavy playbooks; violates
  #117 skill-authoring rules).
- Add a config opt-out in v1.
- Change Cursor's slash menu (product limitation).

## Alternatives considered

- Promote `@iflow-plan` — rejected; `@` is also awkward on Norwegian keyboards.
- Rename skill folders to spaces — rejected; invalid / non-portable paths.
