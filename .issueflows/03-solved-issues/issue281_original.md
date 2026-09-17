# Issue #281: Design doc — user-global config, lock, registry, update-all

Source: https://github.com/jepegit/issue-flow/issues/281

## Original issue text

### Problem / context

Epic #269 needs a written contract before any user-global writes: where the user config lives, how knobs resolve, how repos are locked and registered, and how bulk update relates to `workspace update`.

### Spec

Add `.issueflows/04-designs-and-guides/user-global-config.md` defining: XDG/user config path (and Windows/WSL note); precedence (project `config.toml` > user-global > env > default, or the reverse for “system-wide defaults” — pick one and justify); lock key on the **project** (`[issueflow] locked = true`, default false); registry file (list of roots, how a repo gets registered — `init` / explicit `register` / both); `update --all` (or named command) vs `workspace update` (workspace file optional); lock skip behaviour; interaction with #276 stamps when refreshing a registered repo. Cross-link knobs table.

### Acceptance criteria

- Design doc merged.
- Knobs table row(s).
- Later Stage 2 issues cite it.

### Goal

One doc answers path, precedence, lock, registry, and update-all vs workspace.

### Model

deep

### Depends on

none

Part of epic #269.
