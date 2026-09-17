# Issue #287: Registry of issue-flowed projects + update-all

Source: https://github.com/jepegit/issue-flow/issues/287

## Original issue text

### Problem / context

Epic #269 Stage 2: one command refreshes every unlocked registered repo without requiring `issueflow-workspace.toml`.

### Spec

Persist `registry.toml` per [user-global-config.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/user-global-config.md) (#281). `init` and `issue-flow register` add the current root; `unregister` removes it. `issue-flow update --all` walks the registry, skips missing and **locked** repos, runs `update` on the rest (forward `--force` / `--editor`; honour #276 stamps per root), aggregates like `workspace update`. No workspace file required.

### Acceptance criteria

- Register + update-all tests with one locked and one unlocked tmp project.
- Docs in `docs/cli.md`.

### Goal

`update --all` refreshes unlocked registered repos and skips locked ones.

### Model

default

### Depends on

#286

Part of epic #269.
