# Editor support

issue-flow can scaffold its workflow for several AI coding tools. Pass one or
more `--editor` values (repeatable, or `all`) to `init` / `update`; the default
is `cursor`, so existing setups are unchanged.

```bash
issue-flow init                          # Cursor (default)
issue-flow init --editor claude          # Claude Code
issue-flow init -e cursor -e claude      # both
issue-flow init --editor all             # every supported editor
```

**Agent Skills** (`<agent_dir>/skills/<name>/SKILL.md`) are the portable core —
every editor gets the full set. **`AGENTS.md`** is the convergent rules file and
is written for every editor as a non-destructive *managed block* (issue-flow
only ever owns the content between its markers, so a hand-maintained `AGENTS.md`
is preserved). Slash commands and an editor-specific rules file are layered on
top where the tool supports them.

| Editor      | `agent_dir`  | Slash commands | Skills | Extra rules file                    | `AGENTS.md` | graphify auto-register |
| ----------- | ------------ | -------------- | ------ | ----------------------------------- | ----------- | ---------------------- |
| Cursor      | `.cursor/`   | — (use skills) | yes    | `.cursor/rules/issueflow-rules.mdc` | yes         | yes                    |
| Claude Code | `.claude/`   | `commands/`    | yes    | `CLAUDE.md`                         | yes         | no                     |
| opencode    | `.opencode/` | `command/`     | yes    | —                                   | yes         | no                     |
| Codex       | `.codex/`    | — (use skills) | yes    | —                                   | yes         | no                     |

Cursor and Codex use skills as their primary slash-menu surface, so you invoke
the mirrored skills (e.g. `/iflow-capture`) instead of separate files under
`commands/`. `issue-flow update` removes known generated `.cursor/commands/`
files during the Cursor migration but preserves unrelated user commands. The
[graphify integration](graphify.md) currently registers only with Cursor; other
editors still get the `/iflow-graphify` command/skill where applicable but no
automatic `graphify cursor install`.

## Multi-root workspaces

When one editor workspace contains **several sibling repositories** (each with
its own `issue-flow init`), lifecycle commands must target the correct repo
explicitly. Use slash hints (`root:<path>`, `repo:<folder-name>`,
`repo:owner/name`), or run
`issue-flow agent resolve [--from-file <active-file>] [--json]` before
`git`/`gh` calls. See `.issueflows/04-designs-and-guides/multi-repo-workspaces.md`
in scaffolded projects (or run `issue-flow update` to refresh scoped
`issueflow-rules.mdc` files).

### Workspace registry and default repo

Run **`issue-flow workspace init [--default <member>]`** at the workspace root
to create `issueflow-workspace.toml`:

```toml
[workspace]
default = "cellpy"                   # the "parent repo"
members = ["cellpy", "cellpy-core"]  # optional; auto-discovered when omitted
```

The `default` member is used when a command runs from **outside any single
scaffold** (typically the workspace root itself) — it replaces the final
"stop and ask" step of the resolution order, and nothing else: explicit
hints, the nearest scaffold, and the issue-branch heuristic all still win.
`issue-flow agent resolve --json` reports the workspace context
(`workspace_root`, `workspace_default`, `workspace_members`) and flags when
the default was used (`resolved_via_workspace_default: true`).

A single **shared** `.issueflows/` folder for the whole workspace is
deliberately not supported: GitHub issue numbers are a per-repo namespace,
branches and PRs are per-repo regardless, and `/iflow-archive` recovery
depends on tracking files being committed in the repo that owns them.
