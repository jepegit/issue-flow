# Issue #323: workspace bootstrap --yes should refresh members in an existing toml

Source: https://github.com/jepegit/issue-flow/issues/323

## Original issue text

### Problem / context

After `issue-flow workspace bootstrap --yes --default cellpy` in a folder that already had `issueflow-workspace.toml`, a newly cloned sibling (`cellpy-simple-gui`, already scaffolded) was **not** added to the toml.

Bootstrap classifies all own-git children (it listed `cellpy-simple-gui` as scaffolded) then skips the write when the file exists:

```
write_registry = force or not workspace_exists
# …
kept  issueflow-workspace.toml (pass --force to rewrite)
```

The `kept` line is dim and easy to miss after a long member-init run. `--yes` reads as “make the workspace match what you just classified.” It does not.

Related: #322 (print the exact next `--default` command).

### Spec

1. **`--yes` with an existing toml** must not silently leave a stale `members` list. Prefer **refresh**: rewrite (or union) `members` from the current classify (scaffolded + just-inited), keep an existing `default` unless `--default` was passed. Alternative acceptable: refuse with a loud error naming the missing members and the `--force` command — no silent keep.
2. Classify-only and `--yes` both report members present on disk but absent from the toml.
3. `--force` still full-overwrite as today.
4. Docs (`docs/how-to/workspaces.md`, CLI help): “toml already exists” is not “new clones are ignored.”

### Acceptance criteria

- Existing toml + new scaffolded sibling + `bootstrap --yes --default <same>` → sibling is in `members` (or the command exits 1 with a copy-pasteable `--force` line).
- Dim-only `kept` is not the sole signal.
- No write of `.issueflows/` on the parent; no `git init` of children.

### Out of scope

- Editing `*.code-workspace` (separate issue).
- Interactive picker (#322).
- #321 (pr-ready / CI floor).
