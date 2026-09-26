---
name: iflow-cleanup
description: >-
  Post-merge branch hygiene: switch to the default branch and delete landed
  local branches (reachable via -d; squash-landed via -D behind its own
  confirm). Optional GitHub remote audit via trailing "include GitHub" or
  baked cleanup_include_github. Never --force, never deletes unique work.
disable-model-invocation: true
issue-flow-version: 0.5.17
---

# issue-flow — issue cleanup (`/iflow-cleanup`)

Follow this skill to **run post-merge branch hygiene** after a PR has been merged (typically the PR opened by `/iflow-close`).


**Invoke:** type `iflow cleanup` in chat, or `/iflow-cleanup` from the slash menu (`iflow-cleanup` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands. When the answer came from the workspace registry, the payload sets `resolved_via_workspace_default: true`.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Workspace default** — an `issueflow-workspace.toml` at the workspace root (created with `issue-flow workspace init`) may name a `default` member repo; use it when no scaffold matched above. Tell the user the default was used.
6. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** pass an explicit repo on every `gh` call — never rely on `gh`'s implicit cwd default. For most commands use `--repo <owner/repo>`; **exception:** `gh repo view` takes the repo as a **positional** arg (`gh repo view <owner/repo> …`) and rejects `--repo`.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Input

Optional free-form text after the command:

- **No extra text** — Phase A: detect the current branch's PR, clean that up, plus any other local branches already merged into the default. Phase B stays off unless a GitHub-audit token is present.
- A **branch name** — Phase A targets that branch instead of the current one (e.g. `/iflow-cleanup 42-fix-login`).
- **GitHub remote audit (opt-in tokens)** — trailing text containing (case-insensitive) `include github`, `include gh`, `with github`, or a standalone `github` token enables **Phase B** after Phase A.
- **GitHub remote audit (opt-out tokens)** — trailing `no github`, `local only`, or `local-only` (case-insensitive) **skips Phase B** even when `cleanup_include_github` is baked true.
- **Self-update (opt-in tokens)** — trailing `bleeding edge`, `bleeding-edge`, or `self-update` (case-insensitive) enables the package upgrade after a successful FF pull.
- **Self-update (opt-out tokens)** — trailing `no bleeding`, `no bleeding-edge`, or `skip self-update` (case-insensitive) **skips** the upgrade even when `on_bleeding_edge` is baked true.
- **Phase A ask tokens** — trailing `ask a1` or `ask a2` (case-insensitive) forces that phase's yes/no prompt even when `cleanup_yes_a1` / `cleanup_yes_a2` is baked true.
- **Pre-authorized force-delete (orchestrator token)** — trailing `drive` (or `landed`) means the caller (`/iflow-drive`) already obtained one confirm that **explicitly covered** `-D` on squash-landed branches. Phase A1 and A2 then run **without re-asking**, but A2's scope narrows: `squash_landed` always; `merged_pr_divergent` only when none of its unique commits is newer than the PR's `mergedAt`; never `unique_work` / `skipped`. Tip SHAs are still printed. A human typing `/iflow-cleanup` never passes this token.
- **Workspace mode (opt-in tokens)** — trailing `all`, `workspace`, or `include workspace` (case-insensitive) runs cleanup for **every scaffolded workspace member** in one pass (see step 4b). Confirms are **consolidated across members but still split by phase**: one A1 confirm, one A2 confirm, and (when Phase B is enabled) one Phase B confirm — never more than three for the whole workspace. Extra `root:<path>` hints include a scaffolded repo outside the registry (`--extra-root`). Ignore these tokens when parsing a named branch. When self-update is enabled, upgrade the tool **once** at the start, then `issue-flow update` per member (do not reinstall PyPI on every member). The CLI half is `issue-flow workspace cleanup` — classify-only unless told otherwise.

**Phase B enable rule:** run Phase B when (`cleanup_include_github` is baked true **or** an opt-in GitHub token is present) **and** no opt-out token is present.

**Self-update enable rule:** run `issue-flow agent self-update` when (`on_bleeding_edge` is baked true **or** a self-update opt-in token is present) **and** no self-update opt-out token is present.

**Phase A1 ask rule:** ask yes/no before running Phase A1. `cleanup_yes_a1` is off.

**Phase A2 ask rule:** ask a **separate** yes/no before any `git branch -D`. Phase A1's yes never implies A2. `cleanup_yes_a2` is off.

## Instructions

1. **Detect the default branch.** Prefer `gh repo view <owner/repo> --json defaultBranchRef -q .defaultBranchRef.name` (repo is **positional** on `gh repo view` — not `--repo`), else `git -C <project_root> symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`.

2. **Identify the target branch.** If the user named a branch after `/iflow-cleanup` (ignoring GitHub-audit / opt-out tokens), use it. Else use the current branch (`git branch --show-current`). If the current branch **is** the default, skip to step 7 (folder sweep only) for Phase A.

3. **Check PR / merge state.** Prefer `gh pr view <branch> --json state,mergedAt,mergeCommit,headRefName`. If `gh` is unavailable, approximate with `git fetch --prune` then `git cherry origin/<default> <branch>` (all commits marked `-` means squash-merged).
   - **If not merged:** remind the user that the working copy is still on the issue branch; suggest `git switch <default>` before unrelated work and re-run `/iflow-cleanup` after the PR merges. **Stop Phase A.** Do not delete anything locally. If Phase B is enabled (see Input), you may still offer Phase B alone (remote audit does not require the issue branch to be merged).
   - **If merged:** continue Phase A.

4. **Classify the local branches.** Prefer the CLI fast path; fall back to manual `git`/`gh` when it is missing.
   - **CLI:** `issue-flow agent local-branches --json -C <project_root>` (add `--no-fetch` only if `git fetch --prune` just ran). Buckets: `reachable`, `squash_landed`, `merged_pr_divergent`, `unique_work`, `skipped`. Every entry carries a `tip` short SHA.
   - **Manual fallback**, per local branch (skipping the current branch and the default):
     1. `git merge-base --is-ancestor <branch> origin/<default>` — exit 0 → **`reachable`**.
     2. Else `git cherry origin/<default> <branch>` — no `+` lines → **`squash_landed`** (every commit has an equivalent patch upstream).
     3. Else `gh pr list --repo <owner/repo> --state all --head <branch> --json number,state,mergedAt,url`. With a merged PR, compare `git log --no-merges --format=%cI origin/<default>..<branch>` against its `mergedAt`: no commit **newer** than the merge → **`merged_pr_divergent`** (the squash rewrote these commits); any newer commit → **`unique_work`** (real work pushed after the PR merged).
     4. Anything else → **`unique_work`**.
     5. Record `git rev-parse --short <branch>` for every branch you might delete.

   > **Why the extra buckets:** this project merges PRs with **squash**, which lands a *new* commit on the default branch. A squash-merged branch tip is therefore never an ancestor of the default, so `git branch -d` refuses it forever — `-d` alone can never prune landed branches here.

4b. **Workspace mode** (only with an `all` / `workspace` token — replaces steps 2–6 for the whole workspace; steps 7–8 then run per member).
   1. **Survey.** Resolve the workspace root (`issue-flow agent resolve --json` → `workspace_root`). Run `issue-flow workspace cleanup --json` from there (add `--extra-root <path>` per `root:` hint). It fetches, classifies `default-sync`, buckets local branches with the same code as `agent local-branches`, lists linked worktrees, and computes an A1 / A2 plan per member — **read-only**. Print the grouped table. Members it **refused** (`skipped: true` — dirty product-code tree, detached HEAD, missing `origin`, locked) are reported with their reason and left out of every confirm; the loop continues with the rest.
   2. **Phase A1 (one confirm for all members).** List per member: `switch <default>` (or why it is blocked), `pull --ff-only`, worktree removes, and `branch -d <reachable…>` by name. Members whose `default_sync.action` is not `even` / `ff_only` are listed **with that action** and their pull is **skipped** — never pulled, rebased, or pushed; their `-d` deletes still run. Ask once. On yes: `issue-flow workspace cleanup --apply --json` (same `--extra-root` hints). Without the CLI, run the listed `git -C <member>` commands yourself. A1 never authorises A2.
   3. **Phase A2 (second confirm, never implied by A1).** Only when any member's `plan.a2.branch_D` is non-empty. List per member every `<name>  <tip>` with its bucket (`squash_landed` / `merged_pr_divergent`) and merged PR; show `merged_pr_divergent` unique-commit subjects; print the recovery line `git branch <name> <tip>`. **Never** list `unique_work` or `skipped` branches — the CLI never plans them either. Ask once, separately. On yes: `issue-flow workspace cleanup --apply --yes-delete-squash-landed --json`; report every `applied.a2.deleted` entry as `<name> <tip> <flag>` so the SHAs stay in the transcript. The `drive` / `landed` token replaces this prompt with the orchestrator's earlier confirm (same narrowed scope as step 6).
   4. **Phase B (third confirm, only when enabled per the Input rule).** Run step 9 per member and present **one** confirm grouped by member.
   5. Steps 7 (folder sweep) and 8 (epic gate offer) run per member. Step 10 reports each member.

5. **Consolidated confirm (Phase A1 — local)** — one yes/no prompt listing every action:
   - `git switch <default>` (home only; skip if already on default)
   - `git pull --ff-only` — if it fails, **stop** A1 steps that assume default is current (apply-changelog, release tag, self-update) and recover via `default-sync` (see below).
   - **Self-update (when enabled).** After a **successful** FF pull, on the **home** repo (default branch), run `issue-flow agent self-update --json -C <home>`. Never run it inside a leftover issue worktree. A skipped editable install or a failed upgrade is reported; do **not** roll back branch deletes. Skip this line when FF failed.

   - `git fetch --prune`
   - `issue-flow agent worktree-list --json` — for each **linked** worktree whose branch is **`reachable`**, `issue-flow agent worktree-remove <path>` (or the issue number) **before** deleting the branch. Git cannot `-d` a branch that is still checked out in a worktree. Never remove a worktree whose branch is `unique_work`.
   - `git branch -d <branch>` for each **`reachable`** branch, listed explicitly by name first. If `-d` still refuses, report that branch and move on.
   - **Planned release / publish-on-success.** When `/iflow-close` planned a tag (tag-derived) **or** recorded a publish label / planned version on the status file — check the focus issue's status file and the newest `HISTORY.md` release section for a version whose tag is missing from `git tag -l` (or whose GitHub release is missing) — include creating it here: prefer `gh release create "v<version>" --generate-notes` (creates the tag too); for tag-only projects without publish, `git tag <planned>` then `git push origin <planned>` is enough. Run it **after** the pull so the tag lands on the merged squash commit. Do not invent releases for ordinary bumps that had no publish label and no planned tag.

If `git pull --ff-only` fails on default (or home default is **ahead** of origin), run `issue-flow agent default-sync --json` (classify-only; never mutates). Print ahead/behind, unique commit onelines + paths, and the recommended `action`. Do **not** only dump `fatal: Not possible to fast-forward`.

| `action` | What to offer |
| --- | --- |
| `even` / `ff_only` | Pull is safe; retry `git pull --ff-only`. |
| `report_ahead` | Print unique commits. Do not silent-push default. |
| `tracking_pr` | Merge `origin/<default>` **or** cherry-pick onto a chore branch, then open a tiny PR. Never push default. |
| `replay_tracking` | Replay the tracking commit onto `origin/<default>` (chore branch + PR). Do not stack another merge. |
| `stop_product` | Stop. User decides. Do not merge onto default. |

Never: rebase default, `push --force` default, or push default to skip CI.


6. **Force-delete confirm (Phase A2 — only when `squash_landed` or `merged_pr_divergent` is non-empty).** A **separate** yes/no prompt; Phase A1's yes never implies it. Skip this step entirely when both buckets are empty. With the `drive` / `landed` token (see Input) the prompt is replaced by the orchestrator's earlier confirm — apply the narrowed scope, still print every `<name> <tip>`.
   - State plainly that these branches need `git branch -D` because a squash merge leaves no reachable tip, and that `-D` skips git's own safety check.
   - List **`squash_landed`** as `<name>  <tip>` with the evidence (every commit patch-equivalent to the default; merged PR number when known).
   - List **`merged_pr_divergent`** *separately*, each with its `<tip>`, merged PR link, and unique-commit subjects — these are landed per GitHub but their tips differ, so the user should eyeball the subjects before agreeing.
   - Show the recovery line: any deletion is undone with `git branch <name> <tip>`.
   - On yes, `worktree-remove` each linked worktree whose branch is in these buckets (clean trees only; never `unique_work`), **then** try `git branch -d <name>` first and only fall back to `git branch -D <name>` when it refuses — `-d` also accepts a branch merged into its own upstream, so it sometimes still works while the remote-tracking ref survives. Report each `<name> <tip>` and which flag was used, so the SHAs stay in the transcript. On no, leave every branch and worktree in place.
   - **Never** include a `unique_work` or `skipped` branch in this prompt, even if the user asks to "delete them all" — point at the branch's unique commits instead and let them delete it by hand.

7. **Optional folder sweep** (safe; no destructive git). In `.issueflows/01-current-issues/`, for each `issue<N>_*` group whose status file contains `- [x] Done` (case-insensitive on `done`), move the group to `.issueflows/03-solved-issues/`. Leave groups without a checked `Done` in place — routing them to `.issueflows/02-partly-solved-issues/` is `/iflow-pause`'s job.

8. **Epic stage gate (offer only).** If the just-merged issue belongs to an epic — its number appears in a `- Published: #<N>` line of an `epic<M>_plan.md` under `.issueflows/05-epics/` — check whether that closed the stage: run `issue-flow agent epic-status <M> --json` and see if the issue's stage now has no open issues left. If the stage just completed, **offer** (do not do automatically) to (a) post a short stage-summary comment on the epic anchor issue and (b) run `/iflow-epic <M> publish` to publish the next stage. Both are the user's explicit call — never auto-publish or auto-comment.

9. **Phase B — GitHub remote audit** (only when Phase B is enabled per the Input enable rule). Prefer the CLI fast path; fall back to manual `git`/`gh` when the CLI is missing.
   - **CLI:** `issue-flow agent branches --json -C <project_root>` (add `--no-fetch` only if `git fetch --prune` just ran). Payload buckets: `deletable`, `unique_work`, `skipped`.
   - **Manual fallback:** `git fetch --prune`; list `refs/remotes/origin/*` (skip `HEAD` and the default); for each tip run `git cherry origin/<default> origin/<branch>` (`+` = unique); `git log --oneline origin/<default>..origin/<branch>` (cap ~20) + `git diff --shortstat`; `gh pr list --repo <owner/repo> --state all --head <branch> --json number,title,state,url,mergedAt`. Treat open-PR heads as unique work (never deletable). Protected branches (when `gh api …/branches/<name>` reports `protected: true`) go to skipped.
   - **Report** the three buckets. For unique-work branches, summarise commit subjects (and open PR titles/URLs) in prose for the user.
   - **Second consolidated confirm** (never folded into Phase A's yes): list every proposed action, then ask once:
     - Optional: for each **deletable** name, `git push origin --delete <branch>` (or `gh api -X DELETE repos/<owner>/<repo>/git/refs/heads/<branch>`). Never `--force`. Never delete the default. On push failure (e.g. protection), report and continue.
     - Optional: create a findings issue with `gh issue create --repo <owner/repo>` after showing the draft title/body (deletable list + unique-work summaries). Suggested title: `chore: remote branch audit (<YYYY-MM-DD>)`. Create only on yes.

**Multi-line GitHub text (PowerShell-safe).** Bash `<<'EOF'` heredocs fail in Windows PowerShell (`Missing file specification after redirection operator`). Write the text to a file and pass that file:

- `gh issue create`, `gh issue edit`, and `gh pr create` take `--body-file <path>`.
- `git commit` takes `-F <path>`.

```powershell
@'
line one

line two
'@ | Set-Content -Encoding utf8 body.md
gh issue create --repo owner/repo --title "title" --body-file body.md
```

Bash accepts the same `--body-file` / `-F` flags. Use that pattern for every multi-line body.

   - Phase B is **read-only until that second confirm**. Declining leaves remotes untouched.

10. **Report.** Summarize: default branch, PR/merge status, Phase A1 commands and `-d` deletions, Phase A2 `-D` deletions with their tip SHAs (or "declined" / "none offered"), branches left alone as unique work, folder sweep, epic stage-gate offer, self-update action (`upgraded` / `skipped` / `failed` / "not enabled"), and (when run) Phase B bucket counts, remote deletes, findings issue URL or "skipped". In workspace mode, report each member (including refused ones with their reason). Else if `issue-flow agent resolve --json` reports `sibling_roots`, list them and remind the user that **each scaffolded repo needs its own `/iflow-cleanup`** — do not loop automatically unless invoked with `all` (or `workspace`). If other open PRs still show `DIRTY` / CONFLICTING (often `HISTORY.md`), **offer** `/iflow-pr-sync` — do not auto-run it.

## Constraints

- Never use `git push --force`. Never rebase default, force-push default, or push default to skip CI.
- `git branch -D` is allowed **only** for `squash_landed` / `merged_pr_divergent` branches, **only** after the Phase A2 confirm (or an orchestrator confirm that explicitly named `-D`, signalled by the `drive` / `landed` token), and **only** with their tip SHAs reported. Never `-D` a branch holding unique work, a branch you could not classify, or the current branch. In Phase A1, a `-d` refusal is reported and left alone — it is never a licence to force-delete.
- Never delete the default branch (local or remote).
- `issue-flow workspace cleanup` is classify-only by default. Pass `--apply` only after the workspace A1 yes, and `--apply --yes-delete-squash-landed` only after the workspace A2 yes (or the orchestrator token). Never pass either flag to "just see what happens".
- Remote deletes and findings-issue creation require the **Phase B** confirm; the Phase A1 and A2 yeses must not imply them (nor each other).
- If anything is ambiguous (detached HEAD, multiple remotes, missing tracking info), report and stop rather than guess.
- Do not open or update PRs. Do not bump version fields — pyproject bumps belong to `/iflow-close`. The only version action allowed here is creating a release tag / GitHub release that `/iflow-close` **planned** (tag-derived strategy or publish-on-success label), inside the Phase A consolidated confirm.
- Do **not** offer to update `HISTORY.md` / CHANGELOG here — that belongs in `/iflow-close` before the PR.

