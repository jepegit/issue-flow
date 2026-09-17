# Issue #286: Per-repo lock flag

Source: https://github.com/jepegit/issue-flow/issues/286

## Original issue text

### Problem / context

Epic #269 Stage 2: a repo can opt out of `update --all` without write-protecting a normal single-repo `update`.

### Spec

Persist `[issueflow] locked` per [user-global-config.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/user-global-config.md) (#281): project `config.toml` only, default `false`, optional `ISSUEFLOW_LOCKED` process override. Bake into `config show`. User-global `locked` is ignored.

### Acceptance criteria

- Seed + resolve tests.
- Locked project documented.

### Goal

A repo can be marked locked and `config show` reports it.

### Model

fast

### Depends on

#285

Part of epic #269.
