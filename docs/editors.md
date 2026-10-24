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
is preserved). Every editor gets the same eleven skills; each skill folder holds
`SKILL.md` plus its mode files. The extra rules file only points at `AGENTS.md`,
so the rules load once.

| Editor      | `agent_dir`  | Slash commands | Skills | Extra rules file                    | `AGENTS.md` | graphify auto-register |
| ----------- | ------------ | -------------- | ------ | ----------------------------------- | ----------- | ---------------------- |
| Cursor      | `.cursor/`   | — (use skills) | yes    | `.cursor/rules/issueflow-rules.mdc` | yes         | yes                    |
| Claude Code | `.claude/`   | — (use skills) | yes    | `CLAUDE.md` (imports `AGENTS.md`)   | yes         | no                     |
| opencode    | `.opencode/` | `command/` (one-line wrappers) | yes | —                     | yes         | no                     |
| Codex       | `.codex/`    | — (use skills) | yes    | —                                   | yes         | no                     |

Cursor, Claude Code, and Codex show skills in the slash menu, so `/iflow-pick`
runs the `iflow-pick` skill directly. opencode gets a one-line command file per
skill that tells the agent to read the skill. `issue-flow update` removes the
older generated `.cursor/commands/` and `.claude/commands/iflow*.md` copies and
leaves unrelated user commands alone. The [graphify integration](graphify.md)
currently registers only with Cursor; other editors still get
`/iflow-status graph` but no automatic `graphify cursor install`.

## Multi-root workspaces

**Start here** if you have a parent folder of git repos:
[Use issue-flow in a folder of repos](how-to/workspaces.md).

From that parent folder:

```bash
issue-flow workspace bootstrap --yes --default <main-repo>   # first time
issue-flow workspace init --default <main-repo>              # toml only
issue-flow workspace update                                  # refresh skills
```

Each repo keeps its own `.issueflows/`. The parent does not get a shared
tracker.

When the editor workspace already contains those siblings, lifecycle
commands must still target the correct repo. Use slash hints (`root:<path>`,
`repo:<folder-name>`, `repo:owner/name`), or run
`issue-flow agent resolve [--from-file <active-file>] [--json]` before
`git`/`gh` calls. The design notes are in
[workspaces notes](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/workspaces.md#multi-repo-workspaces)
in the issue-flow repository. Run `issue-flow update` to refresh the scoped
`issueflow-rules.mdc` files.

### Workspace registry and default repo

`workspace init` writes `issueflow-workspace.toml` at the workspace root:

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
branches and PRs are per-repo regardless, and `/iflow-cleanup archive` recovery
depends on tracking files being committed in the repo that owns them.
