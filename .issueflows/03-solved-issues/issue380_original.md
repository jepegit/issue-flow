# Issue #380: Windows PowerShell: bash heredocs break gh issue create / multi-line bodies in agent skills

Source: https://github.com/jepegit/issue-flow/issues/380

## Original issue text

### Problem / context
On Windows, Cursor agent sessions often run commands in **PowerShell**. Several agent workflows (including `/iflow-issue` creating a multi-line GitHub issue body) commonly use a **bash heredoc**:

```bash
gh issue create --repo owner/repo --title "..." --body "$(cat <<'EOF'
...
EOF
)"
```

That pattern is also common in Cursor user rules for `git commit --trailer "Co-authored-by: Cursor <cursoragent@cursor.com>" -m "$(cat <<'EOF' ...)"`. PowerShell does **not** support `<<'EOF'`; it treats `<<` as redirection and fails with:

```
Missing file specification after redirection operator.
```

Observed while creating https://github.com/ife-bat/bess-wrangler/issues/1 via `/iflow-issue` (issue-flow 0.5.12, Windows 10, PowerShell).

### Spec
Document (and preferably standardize in scaffolded skills) a **shell-portable** way to pass multi-line bodies to `gh` / git on Windows PowerShell, e.g.:

1. Prefer `gh … --body-file <path>` (write body with the shell’s native here-string or a small Python/temp write).
2. Or detect shell and branch: bash heredoc vs PowerShell `@'…'@` / `-Body` / temp file.
3. Call out in agent-facing docs (`llms.txt` / how-to for agents / `/iflow-issue` skill) that bash heredocs are **not** safe on PowerShell.

Same guidance should cover other multi-line `gh` writes skills already use (`gh issue edit … --body-file`, PR bodies, commit messages) so agents do not invent a second failing recipe.

### Acceptance criteria
- [ ] Agent-facing docs or skills state that bash `<<'EOF'` heredocs fail under PowerShell and give a working alternative.
- [ ] `/iflow-issue` (and any other skill that creates multi-line `gh` bodies) recommends `--body-file` or an equivalent portable pattern — not bash-only heredoc as the sole example.
- [ ] A Windows/PowerShell agent can create an issue with a multi-line markdown body on the first attempt without a ParserError.

### Out of scope
- Changing Cursor’s default shell.
- Implementing a full cross-shell command rewriter in the CLI.
