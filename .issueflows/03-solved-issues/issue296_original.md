# Issue #296: Dedupe workspace update and the registry

Source: https://github.com/jepegit/issue-flow/issues/296

## Original issue text

### Problem / context

v1 left `workspace update` and `update --all` as different sets ([user-global-config.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/user-global-config.md) / [multi-repo-workspaces.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/multi-repo-workspaces.md)). The same absolute root in both can be refreshed twice in one session.

### Spec

Add a shared unique-by-resolved-path walk. Default command sets stay unchanged (`update --all` = registry only; `workspace update` = workspace members only). `issue-flow update --all --workspace` unions nearest `issueflow-workspace.toml` members with registry roots (locked / missing still skip). A member already listed twice in the workspace file updates once. Honour #276 per root; `--force` still `overwrite_foreign`. Docs: both design docs + `docs/cli.md`. Tests: overlapping tmp root appears once in the union; without `--workspace`, `update --all` does not walk the workspace file.

### Goal

`--workspace` union updates an overlapping root once; defaults stay two separate sets.

### Model

default

### Depends on

#287

Part of epic #269.
