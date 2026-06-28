# Plan for issue #82: switch back to main if clean

## Goal

Make `/iflow-close` switch the working copy back to the detected default branch after the PR is opened or updated, when it is safe to do so. Support explicit opt-out text such as `stay` or `don't switch to main`.

## Constraints

- Do not move destructive post-merge cleanup back into `/iflow-close`; branch deletion remains owned by `/iflow-cleanup`.
- Only switch when the working tree is clean and branch work has been committed and pushed to the PR branch.
- Preserve existing `/iflow-close` responsibilities: tests, optional version bump, history update, issue-folder updates, commit, push, and PR.
- Cursor is skills-first, so the generated skill template is the primary surface; command templates still matter for editors that support slash-command files.

### Prior art

- `src/issue_flow/templates/commands/iflow-close.md.j2` currently ends with a reminder that the user is still on the issue branch and points to `/iflow-cleanup` after merge.
- `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` mirrors that same reminder and explicitly says branch deletion belongs to `/iflow-cleanup`.
- `src/issue_flow/templates/commands/iflow-cleanup.md.j2` and `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2` own post-merge switching, pulling, pruning, and `git branch -d`.
- `tests/test_templating.py` already asserts `/iflow-close` delegates destructive branch cleanup to `/iflow-cleanup`.
- `tests/test_init.py` already asserts generated `iflow-close` skills mention unrelated changes and the issue-branch warning.
- Graph communities checked: close/cleanup branch hygiene is clustered around Communities 26, 28, 50, 74, and 131 in `graphify-out/GRAPH_REPORT.md`.

## Approach

1. Extend `/iflow-close` input parsing docs with opt-out tokens: `stay`, `stay on branch`, `don't switch`, and `dont switch to main`.
2. Replace the current post-PR branch reminder with a safe switch step:
   - detect the default branch;
   - if opt-out text is present, remain on the issue branch and report that choice;
   - otherwise run `git status --porcelain` after the PR step;
   - only if clean, run `git switch <default>` followed by `git pull --ff-only`;
   - if dirty, stay on the issue branch and explain that uncommitted changes made switching unsafe.
3. Keep `/iflow-cleanup` as the later post-merge command for `git fetch --prune`, branch deletion, and solved-folder sweep.
4. Mirror the same behavior in both command and skill templates.
5. Update workflow docs / yolo token docs only if needed so users know `stay` can be forwarded to `/iflow-close`.
6. Add or adjust focused regression tests proving:
   - `/iflow-close` documents `stay` / `don't switch` tokens;
   - `/iflow-close` documents safe default-branch switching after PR creation;
   - `/iflow-close` still does not contain `git branch -d`;
   - generated Cursor `iflow-close` skill includes the new behavior.

## Files to touch

- `src/issue_flow/templates/commands/iflow-close.md.j2` — document opt-out tokens and safe post-PR switching.
- `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` — mirror the close workflow behavior for skills-first agents.
- `src/issue_flow/templates/commands/iflow-yolo.md.j2` and `src/issue_flow/templates/skills/iflow_yolo/SKILL.md.j2` — forward `stay` tokens if yolo docs need parity.
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — update close/yolo summary language if it otherwise contradicts the new behavior.
- `tests/test_templating.py` — add command template regression coverage.
- `tests/test_init.py` — add generated Cursor skill regression coverage.
- Generated scaffold files under `.cursor/skills/`, `.cursor/rules/`, `docs/`, and `graphify-out/` only if the implementation workflow regenerates them intentionally.

## Test strategy

- Run `uv run pytest tests/test_templating.py tests/test_init.py` for focused template and generated-skill coverage.
- Run `uv run pytest` for the full suite.
- Run `uv run ruff check src/ tests/` for lint.
- Exercise the CLI end-to-end in a throwaway git repo with `uv run --project /workspace issue-flow init . --skip-dep-check`, then inspect the generated `.cursor/skills/iflow-close/SKILL.md` for the switch and opt-out instructions.

## Open questions

- None for implementation. Interpret "after the PR" as after `/iflow-close` has opened or updated the PR, not after merge; `/iflow-cleanup` remains the post-merge branch-deletion command.
