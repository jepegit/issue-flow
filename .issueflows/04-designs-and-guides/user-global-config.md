# User-global config, lock, registry, and update-all

**Issue:** [#281](https://github.com/jepegit/issue-flow/issues/281) (this
contract) / epic [#269](https://github.com/jepegit/issue-flow/issues/269)
**Status:** decided 2026-09-17 (Stage 1). User-global file + resolve +
`config show|set --global` shipped in #285. Per-repo `locked` shipped
in #286. Registry + `update --all` shipped in #287.

## Context

A user wants **one machine-wide default** for issue-flow knobs, a
**registry** of repos that use issue-flow on this computer, a way to
**lock** some of those repos so bulk-update leaves them alone, and one
command that refreshes every unlocked registered stack. Workspace
update already covers sibling members of an
`issueflow-workspace.toml`. This layer sits **above** that: no
workspace file required, any registered root is eligible.

Not a skillbook clone. [skillbook-lessons.md](./skillbook-lessons.md)
already pointed #269 at user-global config + update-all + lock and
rejected a personal skill library. Which packaged stems may also
install user-global is decided in
[global-vs-local-skills.md](./global-vs-local-skills.md) (#282).

## Decisions

### User-dir layout

| OS | Directory |
|----|-----------|
| Linux / macOS | `$XDG_CONFIG_HOME/issue-flow/` when `XDG_CONFIG_HOME` is set, else `~/.config/issue-flow/` |
| Windows (native) | `%APPDATA%\issue-flow\` (Roaming) |
| WSL | **Linux path inside the distro** (`~/.config/issue-flow/` or `XDG_CONFIG_HOME`). Do not read the Windows `%APPDATA%` tree from WSL Python (no `/mnt/c/Users/…` lookup). A native Windows install is a separate machine view. The `win32` branch is covered by tests that monkeypatch `sys.platform` (#298). |

Files in that directory:

| File | Role |
|------|------|
| `config.toml` | User-global `[issueflow]` **preference** knobs |
| `registry.toml` | Absolute project roots that `update --all` walks |

Create the directory and files on first write (`config set --global`,
`register`, or `init` registering the current root). Missing files mean
"no user-global layer" — today's resolve behaviour.

### Precedence

For `[issueflow]` **preference knobs** (the keys already documented in
[skill-behaviour-knobs.md](./skill-behaviour-knobs.md)):

**project `.issueflows/config.toml` > user-global `config.toml` >
`ISSUEFLOW_*` env / `.env` > baked default**

Justification: this **extends** the existing contract
(`config.toml` > env > default) instead of reversing it. A committed
project file stays portable and CI-stable; user-global fills knobs the
project did not set; env remains the last explicit override before
code defaults. "System-wide defaults win over the project" was
rejected — that would make a laptop preference silently override a
repo that already chose otherwise.

**Not in user-global** (ignore the key if present):

- `mode` — project identity; only `init --mode` writes it.
- `locked` — per-repo skip flag (below).
- Path keys (`ISSUEFLOW_DIR`, `ISSUEFLOW_AGENT_DIR`,
  `ISSUEFLOW_DOCS_DIR`, `ISSUEFLOW_HISTORY_FILE`) — stay
  **environment-only**, as today.

CLI flags (`--mode`, `--editor`, `--force`, …) still beat every file.

### Lock

`[issueflow] locked = true` lives on the **project**
`.issueflows/config.toml` only. Default is **false** (missing key =
unlocked).

- `update --all` **lists and skips** locked roots; it does not run
  `update` on them.
- A single-repo `issue-flow update <root>` does **not** refuse a locked
  repo — lock is a bulk-update skip, not a write-protect on the
  project itself.
- User-global `locked` is invalid and ignored.
- Optional process override: `ISSUEFLOW_LOCKED=true|false` wins for
  that invocation only (the one exception to project-beats-env). Use
  it in CI or a one-off shell to skip or force-include without
  editing `config.toml`.

### Registry

`registry.toml` is a list of absolute roots:

```toml
roots = [
  "/home/you/src/issue-flow",
  "/home/you/src/other-app",
]
```

- **Both** `issue-flow init` (adds the current root when missing) and
  an explicit `issue-flow register [PROJECT_DIR]` write the registry.
  `issue-flow unregister [PROJECT_DIR]` removes a root. Writes are
  idempotent.
- No whole-disk scan on `update --all` / `init` / `workspace update`.
  Missing roots are skipped and reported, not treated as a hard failure.
  Opt-in: `issue-flow register --discover [START]` walks a start
  directory for existing `.issueflows/` trees (bounded depth, no
  symlink follow) and registers only after confirm (`--yes` for
  scripts).
- Roots are stored resolved (absolute). Relative paths are rejected
  on write.
- `.issueflows/` tracking, epic plans, and project knobs stay
  **per-repo**. The registry is only a list of places to run `update`.

### `update --all` vs `workspace update`

| Command | Set | Needs workspace file? |
|---------|-----|------------------------|
| `issue-flow update --all` | Registry roots | No |
| `issue-flow workspace update` | Scaffolded members of `issueflow-workspace.toml` | Yes |

Keep the name **`update --all`** (compose with the existing command;
no second verb). It walks the registry, skips missing and **locked**
roots, runs `update` on the rest, and aggregates ok / skip / fail the
same way `workspace update` does (one member failure does not abort
the rest).

Flags `--editor`, `--skip-dep-check`, and `--force` forward to each
member `update`. `--force` is the #276 `overwrite_foreign` switch.

A repo may appear in both the registry and a workspace file. Default
command sets stay different (`update --all` = registry;
`workspace update` = workspace members). `update --all --workspace`
unions the nearest workspace file's members with the registry, unique
by resolved path, so an overlapping root is refreshed once in that
invocation. `workspace update` also collapses a member listed twice.

### #276 stamps on a registered repo

Each registered root keeps its own
`.issueflows/agent/skill-stamps.json`. `update --all` running `update`
on that root uses **that repo's** stamps: skip foreign packaged skill
dirs (symlink, extra files, hash ≠ last-write stamp) unless `--force`
was passed on the `--all` invocation.

User-global **skill** materialize (#293) writes a second stamp file at
`$XDG_CONFIG_HOME/issue-flow/skill-stamps.json` (or
`~/.config/issue-flow/skill-stamps.json` /
`%APPDATA%\issue-flow\skill-stamps.json`), keys
`{editor_id}/{output_name}` (e.g. `cursor/caveman`). `--force` on
`update` / `update --all` is `overwrite_foreign` for those global dirs
too. Honour [skillbook-lessons.md](./skillbook-lessons.md): no second
library. #277 unmanaged-skill scan stays a project-doctor concern
(global dirs are not scanned).

## Knobs

New project key (see [skill-behaviour-knobs.md](./skill-behaviour-knobs.md)):

| Key | Default | Effect |
|-----|---------|--------|
| `locked` | `false` | `update --all` skips this root. Project `config.toml` only. |

User-global path / registry path are **not** project knobs. They follow
the OS table above.

## Stage 2 must implement

Cite this doc from the Stage 2 issues:

1. User-global `config.toml` + resolve precedence +
   `config show|set --global`.
2. Persist `[issueflow] locked` (default false) + `ISSUEFLOW_LOCKED`.
3. Registry + `register` / `unregister` + `update --all`.

## Non-goals (this contract)

- Vendoring skillbook or a personal skill library.
- Default whole-disk scan (opt-in `register --discover` only, #297).
- GitLab.
- Making every packaged skill global (#282 / #293: only `both` stems).
- Deduping `update --all` with `workspace update` except the opt-in
  `--workspace` union (#296).
- Windows-native paths from inside WSL (explicit non-goal; #298 tests the
  `win32` branch only).

## Link

Epic plan: `.issueflows/05-epics/epic269_plan.md`.  
Knobs: [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).  
Workspace registry: [multi-repo-workspaces.md](./multi-repo-workspaces.md).  
Clobber-protect: issue #276 / `skill_ownership.py`.
