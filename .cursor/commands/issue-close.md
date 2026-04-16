# Close out the current issue

Run this when implementation is done and you are ready to land the work.

## Input

Optional text after the command (same line). Examples:

- **No extra text** — close the issue without bumping the package version.
- **`bump`** or **`patch`** — bump the **patch** semver (e.g. `1.2.0` → `1.2.1`).
- **`bump minor`** or **`minor`** — bump **minor**.
- **`bump major`** or **`major`** — bump **major**.
- **Free text** — if it clearly asks to release or bump the version, infer `patch`, `minor`, or `major` from wording (e.g. “bugfix release” → patch); if unclear, ask once.

Other optional notes still apply: branch name, PR title, draft PR, skip issue doc update, commit all changes, etc.

## Typical steps

1. **Sanity check**
   - Run tests and any checks you rely on (e.g. `uv run pytest`).
   - Skim the diff so the commit matches what you intend to ship.

2. **Optional version bump** (only if the user asked for it in the command input)
   - Read `.cursor/skills/issueflow-version-bump/SKILL.md` and follow it.
   - From the project root, run `uv version --bump patch`, `uv version --bump minor`, or `uv version --bump major` according to the input rules above.
   - Do this **before** updating issue markdown and **before** commit / push / PR so the new version is in the tree that gets merged.
   - If the project has no bumpable `pyproject.toml` version, skip and say so; continue with the remaining steps.

3. **Issue tracking in the repo** (see project rules under `.issueflows/01-current-issues`)
   - Update the status file for this issue: clear checklist, remaining work, and use `- [x] Done` only when fully resolved.
   - If the issue is fully resolved, move its markdown files from `.issueflows/01-current-issues` to `.issueflows/03-solved-issues`. If partially resolved, move to `.issueflows/02-partly-solved-issues`.

4. **Commit and fix merge conflicts**
   - Unless told to commit all, stage the right files (avoid unrelated changes). Include `pyproject.toml` (and `uv.lock` if it changed) when a version bump ran.
   - Write a commit message that states what changed and why in normal sentences.
   - Make sure you have pulled the last changes from the default branch (e.g. `main`) and check for and fix merge conflicts.

5. **Push**
   - Push your branch to `origin` (or the remote you use).

6. **Pull request**
   - Open a PR against the default branch (e.g. `main`).
   - Describe the change, how to test it, and link the GitHub issue (e.g. `Closes #123` or `Refs #123` in the PR body).

7. **After review**
   - Address feedback, push updates, and merge when approved and CI is green.

## Output

Summarize what was committed, pushed, and the PR URL (or next step if blocked).
