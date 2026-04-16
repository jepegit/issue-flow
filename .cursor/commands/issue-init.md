# Create original issue file from GitHub issue

Create an `*_original.md` file in `.issueflows/01-current-issues` from a GitHub issue.

## Input
The user may provide one of:
- an issue number (e.g. `123`)
- or a full GitHub issue URL

The text after this slash command is the **issue reference**. It may also be **empty or only whitespace** (user ran `/issue-init` with no arguments).

## Agent efficiency
- Run the flow once; do not re-fetch or re-run tools only to diff the written file against the API (for example, no extra `gh` calls or scripts to compare bytes).
- Do **not** spend effort on trailing newlines, byte-identical file endings, or CRLF vs LF. A normal markdown file with a final newline is fine.
- "Preserve the issue body exactly as returned by GitHub" means the **body text** from the fetch: paste it into the template in **step 5** and move on. No second-pass verification or newline normalization.

## Steps

0. Check that the required folders exist (`.issueflows/00-tools`, `.issueflows/01-current-issues`, `.issueflows/02-partly-solved-issues`, `.issueflows/03-solved-issues`). If not, create them after asking for permission.

1. Resolve the issue reference.
   - **A. No non-empty issue reference** (missing or whitespace-only after the command):
     - Run `git branch --show-current` to get the current branch name.
     - If the branch name is empty **or** equals `main` or `master` (**case-insensitive**): **stop**. Tell the user the issue cannot be inferred from this branch and they must run `/issue-init` with an issue number, a full GitHub issue URL, or `owner/repo/#number`.
     - Else if the branch name matches an **issue-style branch**: ASCII digits at the start, then `-`, then at least one more character (example: `42-fix-login-bug`). Let `NN` be the leading digit sequence.
       - Ask: "You have not provided an issue reference. Should I use issue #NN from the current branch `<branchname>`?" (use the real branch name).
       - If the user **confirms**, treat `NN` as the issue number and continue with the bullets under **B** as if the user had typed only `NN`.
       - If the user **declines** or is **unclear**, ask for an issue number, full URL, or `owner/repo`, and do not proceed until you have a clear reference.
     - Else (branch does not match that pattern): **do not guess.** Ask the user for an issue number, full GitHub issue URL, or `owner/repo/#number`, and do not proceed until they provide it.
   - **B. You have a concrete issue reference** (from user input or from **A** after confirmation):
     - If the reference is a full URL, extract `owner`, `repo`, and `issue number`.
     - If the reference is only an issue number:
       - derive `owner/repo` from `git remote` (prefer `origin`)
       - support both SSH and HTTPS remote URL formats
       - if parsing fails, ask the user for either full issue URL or `owner/repo`

2. Fetch issue data using GitHub CLI (explicit repo if needed):
   - title
   - body
   - url
   - number
   - and confirm resolved `owner/repo`

3. Archive existing issue files already in `.issueflows/01-current-issues` (except the current issue number).
   - Inspect issue groups by issue number (for example `issue121_*` belongs to issue 121).
   - Consider all files for that issue in `.issueflows/01-current-issues` (original + status/supplementary files) as one group to move together.
   - Decide destination:
     - move to `.issueflows/03-solved-issues` if the issue is done
     - move to `.issueflows/02-partly-solved-issues` if the issue is not done
  - Determine "done" status from an explicit checkbox marker in a status file:
    - done only if a status markdown file for that issue contains `- [x] Done` (case-insensitive match for `done`)
    - if the checkbox is missing, unchecked (`- [ ] Done`), unclear, or no status file exists, treat as not done
   - Never move files for the issue currently being created.

4. Create this file:
   - `.issueflows/01-current-issues/issue<number>_original.md`
5. File content format:
   ```markdown
   # Issue #<number>: <title>

   Source: <url>

   ## Original issue text

   <body exactly as in GitHub issue>
   ```
6. If `gh` is not authenticated or issue fetch fails:
   - stop and report the exact error
   - suggest `gh auth login`
7. If the target file already exists:
   - do not overwrite silently
   - ask whether to overwrite or keep both

## Output to user
Report:
- issue number fetched
- repository used (`owner/repo`)
- if the issue number was inferred from the current branch after the user confirmed in step **1 A**, state the branch name and that `#NN` was inferred from it
- file path created
- archive moves performed (source -> destination, grouped by issue number)
- whether the operation succeeded

## Constraints
- Preserve the issue body **text** exactly as returned by GitHub (see **Agent efficiency**; do not optimize for trailing newlines or line-ending style).
- Use UTF-8 markdown.
- Allowed file modifications for this command:
  - create/update the target `issue<number>_original.md`
  - move pre-existing issue files from `.issueflows/01-current-issues` to `.issueflows/02-partly-solved-issues` or `.issueflows/03-solved-issues` according to the archive rule above
- If `.issueflows/01-current-issues` does not exist, report an error and stop.
- If archive destination directories do not exist, report an error and stop.
- Prefer deterministic behavior: always state which repo was resolved before writing the file (including when the issue number came from branch inference).

## Example invocations
- `/issue-init 123`
- `/issue-init https://github.com/owner/repo/issues/123`
- `/issue-init owner/repo/#123`
- `/issue-init` (no trailing text: on an issue-style branch like `123-fix-bug`, ask for confirmation then proceed as for issue `123`)
