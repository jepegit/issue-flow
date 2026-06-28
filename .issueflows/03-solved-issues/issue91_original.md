# Issue #91: add config-driven always-on caveman style (caveman_default)

Source: https://github.com/jepegit/issue-flow/issues/91

## Original issue text

Interactive `/iflow-fix` session.

### Goal

Add an opt-in, config-driven way to make the **caveman** response style on by
default for a project, rather than only when the user asks per-session.

### Approach (option 1)

A `.issueflows/config.toml` entry under `[issueflow]`:

```toml
[issueflow]
caveman_default = true
```

When set (and the `caveman` skill is part of the active mode), `issue-flow init`
/ `issue-flow update` injects an **always-on** caveman pointer into the managed
rule body (`rules/_body.md.j2`, shared by `AGENTS.md`, `CLAUDE.md`, and the
always-applied `.mdc` rule). Since that rule is `alwaysApply: true`, caveman is
re-armed every session for that project. Toggle off per-session with "stop
caveman" / "normal mode".

Default remains `false` (off by default), preserving current behavior.

### Scope

- Read `[issueflow].caveman_default` (+ `ISSUEFLOW_CAVEMAN_DEFAULT` env), expose
  in template context.
- Branch the caveman block in `rules/_body.md.j2` (always-on vs off-by-default
  wording).
- Document the new key (README, AGENTS.md, docs, design guide).
- Tests.
