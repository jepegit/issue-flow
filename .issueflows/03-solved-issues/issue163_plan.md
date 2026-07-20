# Plan — Issue #163: How to handle branches on GitHub

## Goal

Extend `/iflow-cleanup` with an opt-in **GitHub remote-branch audit** (triggered by trailing phrases like `include GitHub`) that classifies remote branches as deletable vs carrying unique work, summarises the unique work, and can optionally delete remotes and/or file a findings issue — all behind explicit confirmation.

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; re-render via `issue-flow update` (dogfood this repo).
- Existing cleanup safety stays: never `git branch -D`, never `git push --force`, never delete the default branch; remote delete uses `git push origin --delete <branch>` (or equivalent `gh`) only after listing each name and getting yes.
- Opt-in only — default `/iflow-cleanup` behaviour unchanged (local merged branches + folder sweep).
- Always pass `--repo <owner/repo>` to `gh`; resolve root via existing multi-repo contract.
- Off-path: `/iflow` still never auto-dispatches cleanup.
- No new runtime Python deps; shell/`gh`/`git` + optional agent CLI helper only.
- One PR; defer protected-branch API edge cases that need admin rights if they block classification.

### Prior art

| Hit | Module / path | Relation |
| --- | --- | --- |
| `/iflow-cleanup` skill + command | `templates/skills/iflow_cleanup/SKILL.md.j2`, `templates/commands/iflow-cleanup.md.j2` | **Extend** — add opt-in Phase B for remotes; keep local Phase A |
| Local merge detection | skill steps: `gh pr view`, `git cherry origin/<default> <branch>` | **Mirror** for remote tips after `fetch --prune` |
| `gitutils` (`default_branch`, `fetch_prune`, `remote_owner_repo`, `ahead_behind`, …) | `src/issue_flow/gitutils.py` | **Reuse / extend** for listing remotes + cherry classification |
| `issue-flow agent preflight` / `switchback` | `src/issue_flow/agent.py` | **Coexist** — preflight stays local hygiene; new audit is separate subcommand |
| `issue-flow doctor` / `agent audit` | dirty `.issueflows/` pattern (`dirty-issueflows.md`) | **Mirror** JSON audit shape for agents; do not merge domains |
| gh list/watch decisions | `04-designs-and-guides/gh-list-and-watch.md` (#172) | **Follow** — prefer documented `gh` commands; CLI helper only where classification must be deterministic |
| `/iflow-issue` create flow | `create-non-epic-issue.md` (#181) | **Mirror** confirm-before-`gh issue create` for findings issue; no merge into `/iflow-issue` |
| Toolbox | `.issueflows/00-tools/` | None for branch audit — no new toolbox script unless CLI proves awkward |
| Graph | `graphify-out/GRAPH_REPORT.md` (no `graph.json`) | God-node community covers `gitutils` / cleanup / preflight / switchback — plan touches those |

## Approach

### Trigger

Parse trailing text after `/iflow-cleanup` / `iflow cleanup` (case-insensitive). Recognise at least:

- `include github` / `include gh`
- `with github` / `github`

If a branch name is also present (existing behaviour), keep it for Phase A target selection; GitHub Phase B still audits **all** `origin/*` remotes (minus default), not only that one branch.

### Phase A — unchanged local cleanup

Run today’s steps (merge check → consolidated local confirm → `-d` → folder sweep → epic offer) whether or not the GitHub token is present.

### Phase B — GitHub remote audit (token present only)

1. **`git fetch --prune`** (if not just done).
2. **Classify** every `refs/remotes/origin/*` except `origin/<default>` into buckets:
   - **Deletable (merged):** tip fully contained in `origin/<default>` (`git cherry` all `-`, or merged PR via `gh pr list --state merged --head <branch>` / `gh pr view`), and no open PR on that head.
   - **Unique work:** has commits not in default; attach `git log --oneline origin/<default>..origin/<branch>` (cap ~20) + shortstat; note open PR URL if any.
   - **Skipped:** default, current checkout’s upstream if it would be unsafe mid-work, and branches `gh` reports as protected when detectable — list with reason.
3. **CLI fast path (recommended):** `issue-flow agent branches [--json] [-C <root>]` returns the classification payload so agents do not re-implement cherry/`gh` logic. Skill documents manual `git`/`gh` fallback when CLI missing (same pattern as `preflight` / `sweep`).
4. **Summarise unique work** in the agent report (commit subjects + PR titles); keep mechanical facts in CLI JSON, prose summary in the skill.
5. **Second consolidated confirm** (separate from Phase A so remote deletes are never implied by local yes):
   - Optional: `git push origin --delete <branch>` for each listed **deletable** remote (never force; never default).
   - Optional: create a GitHub issue with the full findings (deletable list + unique-work summaries) via `gh issue create --repo …` after showing title/body draft. Title sketch: `chore: remote branch audit (<date>)`.
6. **Report** buckets, deletes attempted/skipped, findings issue URL or “skipped”.

### Non-goals (this issue)

- Auto-dispatch from `/iflow` or yolo/cycle chains.
- Force-delete (`-D` / `--force`) of remotes with unique commits.
- Cross-repo looping over `sibling_roots` (remind only, same as cleanup today).
- Rewriting `/iflow-issue` or doctor.

### Design doc

Add `.issueflows/04-designs-and-guides/github-branch-audit.md` recording trigger phrases, buckets, two-confirm model, and CLI contract.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2` | Input tokens; Phase B steps; safety constraints |
| `src/issue_flow/templates/commands/iflow-cleanup.md.j2` | Mirror skill (existing duplication debt) |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Short note on `include GitHub` cleanup mode |
| `src/issue_flow/templates/rules/_body.md.j2` | One-line mention if cleanup is described there |
| `src/issue_flow/gitutils.py` | Helpers: list remote branches, cherry-vs-default, optional merged-PR probe wrappers |
| `src/issue_flow/agent.py` + CLI wiring (`cli.py`) | `issue-flow agent branches [--json]` |
| `tests/test_gitutils.py`, `tests/test_cli.py` / agent tests, `tests/test_templating.py` | Classification + rendered trigger docs |
| `.issueflows/04-designs-and-guides/github-branch-audit.md` | Durable decision record |
| Dogfood scaffolds (`.cursor/skills/iflow-cleanup/…`, commands) | Via `uv run issue-flow update` after template edits |

## Test strategy

- `uv run pytest` — unit-test classification helpers with fixed refs / mocked `_run` where existing `test_gitutils` patterns allow; CLI JSON shape smoke test; templating asserts mention `include GitHub` / Phase B constraints (`never --force`, second confirm).
- `uv run ruff check src/ tests/`
- Optional: `uv run .issueflows/00-tools/verify_scaffold.py` if template surface markers change enough to warrant it.

## Open questions

1. **Remote delete in v1?**  
   **Recommend: yes, but only listed deletable remotes, second confirm, never unique-work branches.** Alternative: report + findings issue only (delete later).

2. **Ship `issue-flow agent branches` in this PR?**  
   **Recommend: yes** (deterministic JSON for agents; mirrors doctor/preflight). Alternative: skill-only `gh`/`git` instructions (#172-style defer).

3. **Findings issue default?**  
   **Recommend: offer after audit; create only on yes** (show draft first). Never auto-create.

4. **Protected branches:** if API cannot detect protection, treat as normal and rely on push-delete failure reporting — OK? **Recommend: yes for v1.**
