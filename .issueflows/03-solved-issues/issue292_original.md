# Issue #292: Confirm or skip opencode's user-global skill path

Source: https://github.com/jepegit/issue-flow/issues/292

## Original issue text

### Problem / context

Epic #269 Stage 3: #282 left opencode's user-global skill dir **unknown**. Stage 3 materialize must not guess a write path.

### Spec

Verify the write target (`~/.config/opencode/skills` vs `~/.agents/skills` vs other) from current opencode docs / source, or record an explicit **skip** (no global writes for opencode until known). Update the editor table in [global-vs-local-skills.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/global-vs-local-skills.md). No `src/` materialize in this issue.

Acceptance: table row is `verified` or `skip` with a one-line reason.

### Goal

Stage 3 materialize never writes an opencode global path that we guessed.

### Model

deep

### Depends on

#282

Part of epic #269.
