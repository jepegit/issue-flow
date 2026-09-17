# Issue #285: User-global config file + resolve precedence

Source: https://github.com/jepegit/issue-flow/issues/285

## Original issue text

### Problem / context

Epic #269 Stage 2 implements the Stage 1 contract: a user-global config file and knob resolve that inserts that layer without changing today's behaviour when the file is missing.

### Spec

Implement [user-global-config.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/user-global-config.md) (#281). Read/write the user-global `config.toml` (create-on-first-set) under the OS path in that doc. Wire `Settings` so preference knobs resolve **project > user-global > env > default**. `issue-flow config show|set` grows `--global`. Tests: missing file = today’s behaviour; set global; project override.

### Acceptance criteria

- Round-trip tests.
- Docs in `docs/configuration.md`.

### Goal

`config show --global` and project resolve match the design doc’s precedence.

### Model

default

### Depends on

#281

Part of epic #269.
