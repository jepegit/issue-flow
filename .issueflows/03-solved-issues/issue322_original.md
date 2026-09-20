# Issue #322: workspace bootstrap: print the exact next command when --default is required

Source: https://github.com/jepegit/issue-flow/issues/322

## Original issue text

### Problem / context

`issue-flow workspace bootstrap` in a multi-member folder (e.g. cellpy-workspace-wsl) dead-ends:

1. Classify-only says `will need --default; members: …` but not a copy-pasteable command.
2. `--yes` without `--default` errors: `pass --default <member> when more than one git member is present`.
3. `bootstrap --yes --default` (no value) is a Typer error: option requires an argument — looks like a picker, is not.

`iflow-init` already says: propose `--default` (first scaffolded, else first unscaffolded, or ask). The CLI does not.

### Spec

1. Classify-only (no `--yes`), more than one git member, no `--default`: print the exact next command using the proposed member (first `scaffolded`, else first git member), e.g.
   `issue-flow workspace bootstrap --yes --default cellpy`
2. `--yes` without `--default` and multiple members: same proposed command in the error (not only the member list). Do not invent a silent default.
3. Help text for `--default`: say it takes a member folder name (not a flag-only switch).

### Acceptance criteria

- Dry-run output includes a line an agent/human can run unchanged.
- `--yes` missing `--default` names the proposed member in the error.
- No auto-write of toml without an explicit `--default` when there are 2+ members.

### Out of scope

- Interactive TTY picker.
- Changing how `--default` is resolved once supplied.
- Work already in #321 (pr-ready omitted-required + CI 3.12–3.14).
