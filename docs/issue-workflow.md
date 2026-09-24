# issue-flow command reference

This project uses **Cursor**. The commands are **Agent Skills** under `.cursor/skills/`; they appear in the slash menu as `/iflow`, `/iflow-plan`, and friends. Paths on this page are for Cursor; other editors use other folders (see [Editor support](https://issue-flow.readthedocs.io/en/latest/editors/)). Issue state is tracked in `.issueflows/01-current-issues/`. The ideas behind the workflow (focus issue, on-path vs off-path, where the agent stops to ask) are explained in [Concepts](https://issue-flow.readthedocs.io/en/latest/concepts/).

> **Keyboard-friendly chat:** type **`iflow plan`**, **`iflow pick`**, **`iflow close`**, etc. in chat (letters + space only). Slash menu still uses `/iflow-plan`. Hyphen form `iflow-plan` also works. Norwegian and similar layouts often lack a dedicated `/` key; `@` is awkward too — the space form is intentional. Every command can be typed all three ways, for example `iflow plan`, `iflow-plan`, `/iflow-plan`.

**Quick start:** type **`iflow`** in chat or run **`/iflow`** from the slash menu. It inspects the state of the focus issue and dispatches to the right linear-flow skill (`iflow capture` / `/iflow-capture`, `iflow plan` / `/iflow-plan`, `iflow build` / `/iflow-build`, or `iflow close` / `/iflow-close`) — so you don't have to remember which step is next. Haven't chosen an issue yet? Start with **`iflow pick`** or **`/iflow-pick`**.


**Brand new to this?** If the project itself is not ready yet — no Python project, no git repo, no GitHub remote, or `gh` not signed in — start with **`iflow setup`** (or **`/iflow-setup`**) instead. It reports what is missing and walks you through each gap one confirmation at a time, for a fresh folder as well as an existing codebase. Run `issue-flow agent setup-status` yourself any time you want the same report without the conversation.


`issue-flow init` also creates a durable project brief at `.issueflows/04-designs-and-guides/this-project.md` when it is missing. Edit it by hand with project-specific context; `issue-flow update` and `issue-flow init --force` leave existing content untouched.

It also seeds `.issueflows/00-tools/README.md` — the index of the project's **shared toolbox**. Drop reusable helper scripts there during issue work and add a one-line index entry; check the folder before writing a new one-off helper. Like the project brief, this README is never overwritten by `issue-flow update`, so its index grows over time.

**Several repos in one folder?** Scaffold and refresh them from the parent with `issue-flow workspace bootstrap` / `update`, and resolve the target repo (`root:` / `repo:` hints, or `issue-flow agent resolve`) before any `git` / `gh` call. Details: [Use issue-flow in a folder of repos](https://issue-flow.readthedocs.io/en/latest/how-to/workspaces/). `/iflow-pick`, `/iflow-issue` and `/iflow-fix` start in a sibling worktree (`../<repo>-<N>`) so this checkout stays on the default branch (knob: `worktree_first`).


## All commands

**Path:** *on* = the dispatcher `/iflow` can run it for you; *off* = you run it explicitly. **Modes:** which scaffolding modes install it.

| Command | What it does | Path | Modes |
|---|---|---|---|
| **Core loop** | | | |
| `/iflow` | Smart dispatcher: detects the focus issue's state and runs capture, plan, build or close. | — | standard, novice, simple |
| `/iflow-capture` | Pull a GitHub issue into `issue<N>_original.md`; sweep older current issues. | on | standard, novice, simple |
| `/iflow-plan` | Write `issue<N>_plan.md` and stop for your approval before any code is touched. | on | standard, novice, simple |
| `/iflow-build` | Implement the approved plan; optional early draft PR. | on | standard, novice, simple |
| `/iflow-close` | Tests, optional version bump, `HISTORY.md`, status files, commit, push, PR. | on | standard, novice |
| `/iflow-cleanup` | After the merge: back to default, pull, delete landed local branches (behind confirms). | off | standard, novice |
| **Starting work** | | | |
| `/iflow-setup` | Guided first-time project setup (`uv init`, `git init`, `gh auth login`, `gh repo create`). | off | standard, novice |
| `/iflow-init` | Cold-start or check the issue-flow harness. Does **not** capture issues. | off | standard, novice, simple |
| `/iflow-pick` | Front door: choose the next issue, create the branch, run capture. | off | standard, novice |
| `/iflow-issue` | Create one well-specified GitHub issue (or an epic anchor). | off | standard, novice |
| `/iflow-split` | Cut an over-large issue into 2–5 linked sub-issues. | off | standard |
| `/iflow-epic` | Plan a large change as stages; publish a stage as real issues. | off | standard |
| **Hands-off and special runs** | | | |
| `/iflow-yolo` | Small, low-risk issue: capture → plan → build → close under one confirm. | off | standard |
| `/iflow-fix` | Iterative session: one issue + branch, many small confirmed fixes. | off | standard |
| `/iflow-ops` | Ops / no-PR work (promote, flag flip, external deploy); closes without a PR. | off | standard |
| `/iflow-cycle` | Batch of yolo-fit issues in a row under one confirm (PRs auto-merged). | off | standard |
| `/iflow-auto` | Unattended epic stage via cycle, then adversarial review. | off | standard |
| `/iflow-drive` | Whole epic path from one issue: draft → publish → auto → final review. | off | standard |
| **Helpers** | | | |
| `/iflow-pause` | Park the focus issue in `02-partly-solved-issues/` with resume notes. | off | standard, novice, simple |
| `/iflow-status` | Read-only overview of every issue, locally and on GitHub. | off | standard, novice, simple |
| `/iflow-review` | Propose and apply workflow labels on open issues (v1: yolo). | off | standard |
| **Maintenance** | | | |
| `/iflow-doctor` | Audit `.issueflows/` for dirty conditions; optional safe repair. | off | standard, novice |
| `/iflow-archive` | Condense old solved issues into a dated summary (destructive, gated). | off | standard, simple |
| `/iflow-pr-sync` | Refresh open PRs that went dirty after another merge (usually `HISTORY.md`). | off | standard |
| `/iflow-graphify` | Rebuild the optional [graphify](https://graphify.net) knowledge graph. | off | standard |

**Helper skills** (called by other commands, rarely by hand): `iflow-version-bump` — strategy-aware version bump: static `[project]` versions via `uv version --bump <level>` (any uv level: `major`/`minor`/`patch`/`stable`/`alpha`/`beta`/`rc`/`post`/`dev`); git-tag-derived versions via a planned post-merge tag; the project's own "Release & version bump" section in `this-project.md` wins, and a bare `bump` stays on the current pre-release channel. `iflow-history-update` — append an entry to `## [Unreleased]` in `HISTORY.md`, or promote it to a new `## [x.y.z] - YYYY-MM-DD` release section when a version bump happened.

Each skill sets `disable-model-invocation: true` so it is included when you **explicitly** invoke it, not on every chat. Every rendered `SKILL.md` also carries `issue-flow-version: <version>` in its YAML frontmatter (the package version at last `issue-flow init` / `issue-flow update`). Compare with `issue-flow --version`; if they differ, re-run `issue-flow update`. See [Agent Skills](https://cursor.com/help/customization/skills) in the Cursor docs.

Lifecycle skills also carry a **`### MODEL & EXECUTION DIRECTIVE`** — **economy** (speed/token savings) or **reasoning** (design depth) — baked at `issue-flow update` from `[issueflow]` / `[issueflow.step_profiles]` in `.issueflows/config.toml`. `/iflow-pick` can announce label-based session overrides when `model_label_flows` is enabled (`deep_model_label` / `fast_model_label`).


Every command below is described the same way: **When to use**, **Arguments**, **What it does**, **What it asks you**, **Result**, **Related**.

---

## Core loop

### `/iflow` — smart dispatcher

**When to use:** Any time you want the next right step without remembering which specific command applies.

**Arguments:** Nothing, or the same arguments the target command would take (e.g. `/iflow 42` on a fresh branch, `/iflow bump minor` when the issue is done). `/iflow` forwards the trailing text verbatim.

**What it does:** Picks the next step from the focus issue's files:

| State of the focus issue | Dispatches to |
|--------------------------|---------------|
| No focus, session present (`epic_session`) + that epic has `next_candidates` | **Stop** — ask next `#<M>` continue / cycle\|auto\|drive / stop (never silent-pick) |
| No focus, but an active epic has `next_candidates` (`agent state` → `epic_hint`) | **Stop** — list candidates; recommend `/iflow-pick` (never auto-pick) |
| No `issue<N>_original.md` (or no focus / no epic candidates) | `/iflow-capture` |
| `original` exists, no `issue<N>_plan.md` | `/iflow-plan` |
| Plan exists, status file missing or `- [ ] Done` | `/iflow-build` |
| Status file contains `- [x] Done` | `/iflow-close` |

**Focus-issue resolution:** prefer the leading digits of the current branch when it matches `^<N>-.+`; else the single group in `.issueflows/01-current-issues/`; else the epic gap check; else ask. See `04-designs-and-guides/iflow-epic-awareness.md`.

**Not auto-dispatched:** `/iflow-setup`, `/iflow-init`, `/iflow-pause`, `/iflow-cleanup`, `/iflow-yolo`, `/iflow-ops`, `/iflow-fix`, `/iflow-issue`, `/iflow-split`, `/iflow-status`, `/iflow-doctor`, `/iflow-review`, `/iflow-epic`, `/iflow-cycle`, `/iflow-auto`, `/iflow-drive`, and `/iflow-archive`. `/iflow` will mention them in its output when relevant (e.g. "after the PR merges, run `/iflow-cleanup`") but never picks them for you.

**What it asks you:** Nothing itself — each dispatched command keeps its own checkpoints. The epic gap without a session only **recommends** `/iflow-pick`; with a session it **asks** (never silent-pick).

**Result:** One of the four linear commands runs, or a stop with epic candidates listed.

**Related:** [Concepts](https://issue-flow.readthedocs.io/en/latest/concepts/) · [Work one issue end-to-end](https://issue-flow.readthedocs.io/en/latest/how-to/work-one-issue/)

### `/iflow-capture` — capture the issue locally

**When to use:** You have a GitHub issue you want to work on (or archive older "current" issues before starting a new one).

**Arguments:** An issue number (e.g. `42`), a full GitHub issue URL, or nothing — then, on a branch named like `42-short-description`, the assistant may ask to use `#42` from the branch (and refuses to guess on `main`/`master`). `owner/repo` comes from `git remote origin` when you only pass a number.

**What it does:**

1. Fetches title, body, URL and comments with **GitHub CLI** (`gh`; run `gh auth login` if needed).
2. Writes **`.issueflows/01-current-issues/issue<number>_original.md`** with the title, source URL, the **exact** issue body, and an optional curated comments summary.
3. **Archive:** other `issue<N>_*` groups in `.issueflows/01-current-issues/` move to `.issueflows/03-solved-issues/` if a status file contains `- [x] Done`, otherwise to `.issueflows/02-partly-solved-issues/`. The new issue's files never move in this step.

**What it asks you:** Before overwriting an existing `issue<number>_original.md`, and a second confirmation before re-opening an issue that is already archived.

**Result:** One canonical "original issue" file under `.issueflows/01-current-issues/` plus optional archive moves.

**Related:** [Work one issue end-to-end](https://issue-flow.readthedocs.io/en/latest/how-to/work-one-issue/)

### `/iflow-plan` — design the approach

**When to use:** The issue is captured (`*_original.md` exists) and you want a confirmed plan **before** any code changes.

**Arguments:** Optional free-form hints (constraints, design preferences).

**What it does:**

1. Finds the focus issue in `.issueflows/01-current-issues/` and runs the branch-status preflight (non-destructive).
2. Reads the original issue and any prior status; reads `.issueflows/04-designs-and-guides/this-project.md` when present and consults other files under `.issueflows/04-designs-and-guides/` when relevant.
3. **Prior-art discovery** — skims `.issueflows/00-tools/` for an existing helper; if `graphify-out/GRAPH_REPORT.md` exists, skims God Nodes / Communities / Suggested Questions for the affected area; greps for adjacent helpers; records findings under **`### Prior art`** in **`## Constraints`** (or `- None found (toolbox + grep + graph checked).`). Strong overlaps become **Open questions**.
4. Explores read-only, then writes **`issue<N>_plan.md`** with sections: **Goal**, **Constraints** (including **Prior art**), **Approach**, **Files to touch**, **Test strategy**, **Open questions**.
5. Runs a scope check — if the change is broad, proposes `/iflow-split` or `/iflow-epic`.

**What it asks you:** **Always stops for explicit confirmation**: accept, revise, or abort. When `auto_build` is true (default), **Accept** chains into `/iflow-build`; trailing `nobuild` skips once. No code is written before Accept.

**Result:** A confirmed `issue<N>_plan.md` ready for `/iflow-build`.

**Related:** [Work one issue end-to-end](https://issue-flow.readthedocs.io/en/latest/how-to/work-one-issue/)

### `/iflow-build` — implement the plan

**When to use:** The issue has a confirmed `issue<N>_plan.md` and you are ready to code.

**Arguments:** Optional implementation hints. Early-PR tokens: `early` / `pr` (force on), `noearly` (force off). Precedence: trailing > baked `[issueflow].early_pr` (default **False**) > `false`.

**What it does:**

1. **Branch status preflight** — `git fetch --prune`, current branch and ahead/behind vs the default branch; warns if the branch looks stale or you are still on the default branch.
2. **Sweeps stale current issues** — moves every `issue<n>_*` group **other than the focus issue** to `.issueflows/03-solved-issues/` (done) or `.issueflows/02-partly-solved-issues/` (not done).
3. **Seeds `issue<N>_status.md` up front** (unchecked `- [ ] Done`, **What's done** / **Remaining work**) and keeps it current while working.
4. **Implements** the plan, using `.issueflows/04-designs-and-guides/this-project.md` and relevant design docs when present. Reuses helpers from `.issueflows/00-tools/` and contributes new reusable ones back there.
5. **Early pull request (optional)** — when early PR is on, after the first successful push: `gh pr list` then `gh pr create --draft` with `Refs #N`; records the PR in the status file. Does **not** write `HISTORY.md` (close owns that).

**What it asks you:** Which issue to use if several are ambiguous. If `issue<N>_plan.md` is missing: run `/iflow-plan` now, proceed without a plan (noted in the status file), or abort — it does not hard-stop.

**Result:** Implementation aligned with the confirmed plan and project rules, optionally with a draft PR already open.

**Related:** [Work one issue end-to-end](https://issue-flow.readthedocs.io/en/latest/how-to/work-one-issue/)

### `/iflow-close` — land the work

**When to use:** Implementation is done and you want to ship (commit, push, PR). Post-merge branch cleanup is a **separate** step (`/iflow-cleanup`).

**Arguments:** Optional notes (branch name, PR title, draft PR, or "skip issue doc update"), plus any of:

- `/iflow-close bump` — **pre-release-aware default**: stays on the current channel (alpha→alpha, beta→beta, rc→rc, dev→dev) or `patch` when the version is already stable.
- `/iflow-close <level>` — any uv level: `patch`, `minor`, `major`, `stable`, `alpha`, `beta`, `rc`, `post`, `dev` (e.g. `/iflow-close minor`, `/iflow-close beta`). `dev` must be paired, e.g. `/iflow-close bump patch dev`.
- Free text that clearly describes the bump level — the assistant infers the level (e.g. "bugfix release" → `patch`, "promote to beta" → `beta`); it never auto-picks `major`.
- `/iflow-close nohistory` (or `skip history`) — skip the `HISTORY.md` update step for this run.
- `/iflow-close log "one-line summary"` (or `note "..."`) — override the `HISTORY.md` bullet summary instead of using the GitHub issue title.
- `/iflow-close stay` (or `stay on branch`, `don't switch`, `dont switch to main`) — skip the safe default-branch switch after the PR step.
- `/iflow-close draft` — create with `gh pr create --draft` (or leave an existing PR draft); skips yolo merge.
- `/iflow-close ops` (`nopr` / `no-pr`) — the ops path: close locally and on GitHub without a PR (see `/iflow-ops`).

**What it does:**

1. **Sanity check** — e.g. `uv run pytest`, review the diff.
2. **Optional version bump** — if requested, follow `.cursor/skills/iflow-version-bump/SKILL.md`. It resolves the project's **release strategy** first (the "Release & version bump" section of `.issueflows/04-designs-and-guides/this-project.md`, else `pyproject.toml` detection): static versions are bumped with `uv version --bump …` from the project root; **git-tag derived** versions (setuptools-scm and friends) get a **planned tag** instead — created after the merge (by `/iflow-cleanup`, or the yolo close's post-merge step), never on the issue branch. The bump runs after tests and before commit / push / PR, so the PR includes the new version; with no bumpable version it is skipped.
3. **Update `HISTORY.md`** — unless `nohistory` was passed, follow `.cursor/skills/iflow-history-update/SKILL.md`. Append a bullet to `## [Unreleased]` (no bump) or promote `## [Unreleased]` to `## [<new_version>] - <YYYY-MM-DD>` and open a fresh empty `## [Unreleased]` above it (with bump). The bullet is staged in the **same commit** that feeds (or updates) the PR — including when a draft was opened earlier via `/iflow-build` early PR. Never offered after close finishes or after merge. With `confirm_changelog_update = false` (the default), the assistant writes without asking (same as the `yolo` token's history behaviour). If `HISTORY.md` is missing at the project root, the step is skipped with a note — never auto-created.
4. **Issue folders** — update status markdown; use `- [x] Done` only when fully resolved. Move completed issue files from `.issueflows/01-current-issues/` to `.issueflows/03-solved-issues/`, or partly done work to `.issueflows/02-partly-solved-issues/`.
5. **Commit** — focused staging and a clear message (include `pyproject.toml` / `uv.lock` if the bump changed them, and `HISTORY.md` when step 3 updated it).
6. **Sync with the default branch** — `issue-flow agent sync-branch --json` replays the issue branch onto `origin/<default>` so commits that landed while the issue was in flight are included instead of surfacing as a conflicted PR at merge time. A conflict confined to `HISTORY.md`, where both sides only added `## [Unreleased]` bullets, is resolved by keeping them all (the in-flight issue's bullet last); any other conflict aborts the rebase and stops close.
7. **Push** — to your usual remote (e.g. `origin`); `--force-with-lease` when the sync rebased the branch.
8. **Pull request** — `gh pr list --head <branch>` first (reuse an open PR, including an early draft); else `gh pr create` (with `--draft` when the `draft` token was passed). Mark ready from draft when not keeping `draft`. Afterward, snapshot CI with `gh pr checks` (see the `gh-ci` skill for `gh run list` / `gh run watch` fallback). Link the GitHub issue (`Closes #n` / `Refs #n`).
9. **Switch back when safe** — unless `stay` / `don't switch` was passed, run `git status --porcelain`; if clean, `git switch <default>` and `git pull --ff-only`; if dirty, stay put and report why switching is unsafe.
10. **After review** — if switched back, return to the PR branch before review fixes; merge when approved and `gh pr checks` is green; once the PR merges, remind the user to run `/iflow-cleanup` for the post-merge tidy-up (do not auto-run it). With `yolo`, close may `gh pr checks --watch` (budget: `checks_watch_minutes`, default 15) before merge, falling back to `--auto` only when the cap elapses.

**What it asks you:** About uncommitted changes that look unrelated to the issue (never included silently); an ambiguous version bump; the changelog text only when `confirm_changelog_update` is on. Never merges without the `yolo` token.

**Result:** Commit, push, PR link, and either a clean switch back to the default branch or a clear reason for staying on the issue branch. No branches are deleted from `/iflow-close` itself.

**Related:** [Work one issue end-to-end](https://issue-flow.readthedocs.io/en/latest/how-to/work-one-issue/)

### `/iflow-cleanup` — post-merge branch hygiene

**When to use:** The PR opened by `/iflow-close` has merged on GitHub. (The optional GitHub remote audit can also run when you only want a remote-branch report.)

**Arguments:** Nothing (acts on the current branch), an explicit branch name, and/or a GitHub-audit token such as `include GitHub` / `with github` / `github`. Opt out of a baked-on Phase B with `no github` / `local only`. With `cleanup_include_github = true` in `config.toml`, Phase B runs by default without a token.

**What it does:**

1. Detects the default branch and the merge state via `gh pr view` (falls back to `git cherry origin/<default> <branch>` to catch squash-merges). If **not merged**: reminds you to stay off the default for unrelated work and re-run after merge (Phase A stops; Phase B may still run when enabled).
2. If **merged**: classifies every local branch with `issue-flow agent local-branches --json` (or the manual `git`/`gh` fallback) into `reachable`, `squash_landed`, `merged_pr_divergent`, `unique_work`, and `skipped`.
3. **Phase A1** — `git switch <default>`, `git pull --ff-only`, `git fetch --prune`, and `git branch -d` on every `reachable` branch. If `-d` refuses, reports and moves on; it never escalates to `-D` here. If ff-only fails, run `issue-flow agent default-sync` and recover from its `action` — never rebase or force-push default.
4. **Phase A2** (only when something landed via squash) — `git branch -D` on the `squash_landed` branches (each listed as `<name> <tip>`) and on `merged_pr_divergent` branches (merged PR, but commits still differ; listed with their unique-commit subjects). Restore any of them with `git branch <name> <tip>`. `unique_work` branches are never listed.
5. Optional safe folder sweep: moves any `issue<N>_*` group whose status file says `- [x] Done` to `.issueflows/03-solved-issues/`.
6. **Optional Phase B** (opt-in token, or baked `cleanup_include_github = true`, unless opt-out): run `issue-flow agent branches --json` (or the manual fallback) to classify `origin/*` as deletable / unique work / skipped and summarise unique commits; then optional `git push origin --delete` on deletable remotes and/or a findings issue via `gh issue create`. Never `--force`; never delete the default.

**What it asks you:** One consolidated confirm for Phase A1; a **second, dedicated confirm** for Phase A2's `git branch -D` (it prints each tip SHA); a further confirm for any Phase B remote deletes or findings issue. No yes implies another.

**Result:** Working tree on the default, landed local branches deleted (with consent — `-d` for reachable ones, `-D` only for the squash-landed set you explicitly approved), unique work left untouched, folders tidy; when Phase B ran, a remote audit report plus any consented remote deletes / findings issue.

**Related:** [After a squash merge](https://issue-flow.readthedocs.io/en/latest/how-to/after-squash-merge/)

---

## Starting work

### `/iflow-setup` — guided first-time setup

**When to use:** The project is not ready yet: no Python project, no git repository, no GitHub remote, or `gh` not signed in. Works for a fresh folder and for an existing codebase.

**Arguments:** None.

**What it does:** Reads `issue-flow agent setup-status`, works out whether this is a brand-new or an existing project, and walks the gaps in order: `uv init`, `git init` + first commit, `gh auth login`, `gh repo create`, scaffold.

**What it asks you:** A confirmation before every step. It never installs tools or signs in on your behalf — for those it prints the command for you to run and stops.

**Result:** A project with a Python setup, a git repository, a GitHub remote and the issue-flow scaffold.

**Related:** [Getting started](https://issue-flow.readthedocs.io/en/latest/getting-started/)

### `/iflow-init` — cold-start or check the harness

**When to use:** A project has no `.issueflows/` / no issue-flow skills yet, a parent folder of git siblings needs `workspace bootstrap`, or you want to check that the harness is present.

**Arguments:** None.

**What it does:** On a parent folder of two or more own-git children, classifies with `issue-flow workspace bootstrap --json` and runs it with `--yes`. Otherwise guides `issue-flow init`. If the harness is already there, points at `issue-flow update`, `/iflow-doctor`, `/iflow-pick`, and `/iflow-capture`. Never captures a GitHub issue — that is `/iflow-capture` (older docs used `/iflow-init` for capture).

**What it asks you:** A confirmation before running `issue-flow init` or `workspace bootstrap`.

**Result:** A scaffolded (or verified) project or workspace.

**Related:** [Upgrade, init, and workspace (for agents)](https://issue-flow.readthedocs.io/en/latest/how-to/for-agents/)

### `/iflow-pick` — choose the next issue (front door)

**When to use:** You are on the default branch with nothing in progress and want help deciding what to work on next.

**Arguments:** Nothing (survey + ask), `fix` (create a new general-fixes issue every time), `label:<L>` (hard-filter the shortlist to open issues with that GitHub label), or a hint (`milestone v0.4`, a topic) to soft-bias ranking when `label:` is absent. Free-form text that names a label is not a hard filter — use the `label:` token. Empty filter → stop. Batch the same filter with `/iflow-cycle label:<L>` (or `/iflow-cycle yolo`). Tokens `inplace` / `no worktree` keep the in-place start; `worktree` forces a sibling worktree.

**What it does:**

1. **Choose.** Prefers parked work in `.issueflows/02-partly-solved-issues/`; otherwise lists open GitHub issues (`gh issue list`) ranked by **milestone**, **labels**, and **topical similarity** to recently solved issues. With `label:<L>`, hard-filters that shortlist (`--label <L>` on GitHub; parked/epic only if they carry `<L>`). `fix` skips the survey and creates a new `chore: general fixes` issue.
2. **Branch.** Requires a clean tree (or, when the only dirt is under `.issueflows/`, offers a default housekeeping commit first — typical after `/iflow-doctor`), then creates `<N>-<short-slug>` off the default branch in a sibling worktree `../<repo>-<N>` (`issue-flow agent worktree-add`), leaving this checkout on the default, and runs the `/iflow-capture` flow for `<N>`.
3. **Hand off.** When `auto_plan` is true (default), chains into `/iflow-plan` after capture; otherwise asks first. Trailing `noplan` skips the chain once. Issues labelled `yolo` route to `/iflow-yolo`, and `ops` to `/iflow-ops` (ops wins when both are present).

**Over-large issues:** if the chosen issue is too big for one PR, `/iflow-pick` **offers** `/iflow-split` (flat parent/child) or `/iflow-epic` (staged). It does not create children itself.

**What it asks you:** To confirm the pick from a short shortlist, and the branch / worktree before creating it.

**Result:** A chosen issue captured on a fresh `<N>-<slug>` branch, ready for `/iflow-plan`.

**Related:** [Work one issue end-to-end](https://issue-flow.readthedocs.io/en/latest/how-to/work-one-issue/) · [Work in a sibling worktree](https://issue-flow.readthedocs.io/en/latest/how-to/worktrees/)

### `/iflow-issue` — create a normal (non-epic) issue

**When to use:** You want to file **one well-specified** GitHub issue — a single deliverable with a real body — then optionally start the normal lifecycle. Not for iterative small-fixes buckets (`/iflow-fix`) or multi-issue staged work (`/iflow-epic`).

**Arguments:** Optional free text to seed the draft (title / short description). Leading `epic` (e.g. `/iflow-issue epic Large rewrite`) creates an epic **anchor** (`Epic:` title + `epic` label when present). Bare `/iflow-issue` → the assistant asks for a one-line intent.

**What it does:**

1. **Preflight** — default branch, `git fetch --prune`, clean/dirty tree.
2. **Draft** — title + body with **Problem / context**, **Spec**, **Acceptance criteria**, and optional **Out of scope**. If clearly over-large for one PR, offers `/iflow-split` (flat) or `/iflow-epic` (staged) — does not auto-split.
3. **Create** — `gh issue create` and capture `N`.
4. **Optional setup** — branch `<N>-<slug>` + `/iflow-capture`, then offers `/iflow-plan` (never auto-runs plan). Decline → create-only; pick up later via `/iflow-pick` / `/iflow-capture`.

**What it asks you:** To refine and confirm the draft; to confirm the final title/body (and epic label) before creating; whether to start work now. GitHub only (`gh`); GitLab is not supported.

**Result:** A new GitHub issue (and optionally a branch + local capture ready for `/iflow-plan`).

**Related:** [Write a good issue](https://issue-flow.readthedocs.io/en/latest/how-to/write-an-issue/) · [Create and run epics](https://issue-flow.readthedocs.io/en/latest/how-to/epics/) (for epic anchors)

### `/iflow-split` — linked sub-issues for an over-large issue

**When to use:** An **existing** issue is too big for one PR but is not a multi-stage epic. Staged work with dependencies still uses `/iflow-epic`.

**Arguments:** `/iflow-split <N>`, or bare `/iflow-split` (focus issue / issue-style branch).

**What it does:**

1. **Draft** 2–5 child specs (same light body as `/iflow-issue`). Size gate: stages or `Depends on` → stop and recommend `/iflow-epic`.
2. **Create + link** — `gh issue create`, then `issue-flow agent sub-issue-add <N> <M>` (REST `--input` JSON fallback; `sub_issue_id` is the database id). Idempotent. A `## Sub-issues` task list on the parent is the fallback if the sub-issue API fails.
3. **Park** the parent group under `02-partly-solved-issues/` if it was the focus. The GitHub parent stays open as the tracker.

**What it asks you:** One confirmation covering the children to create and link; then whether to start the first child (branch + `/iflow-capture`). It does not auto-run plan/build. GitHub only.

**Result:** An open parent tracker + linked children ready for `/iflow-pick`.

**Related:** [Split a big issue](https://issue-flow.readthedocs.io/en/latest/how-to/split-an-issue/) · [Create and run epics](https://issue-flow.readthedocs.io/en/latest/how-to/epics/) (for staged work instead)

### `/iflow-epic` — plan a large change as staged issues

**When to use:** The work is too big for one PR. You want a staged plan anchored to a GitHub issue, then publish one stage at a time as real issues.

**Arguments:** `/iflow-epic <N>` to draft (or revise) `.issueflows/05-epics/epic<N>_plan.md`. Later: `/iflow-epic <N> publish [stage <k>]` to create that stage's issues on GitHub. **`/iflow-epic start [N]`** writes a one-and-ask session; **`/iflow-epic stop`** clears it. No anchor yet → create one with `/iflow-issue epic <intent>`, then pass the new number.

**What it does:**

1. **Draft** — reads the anchor issue and design docs under `04-designs-and-guides/`; drafts stages of manageable issue specs (title, scope, acceptance, dependencies, **yolo: yes|no** judgment) with `Status: draft`. **Does not** create GitHub issues while drafting.
2. **Publish** — requires `Status: confirmed`; selects the named stage (or the earliest unpublished one); creates issues in dependency order (`gh issue create`), records `Published: #<M>` in the plan, and updates the anchor issue's task list. Re-runs are idempotent.
3. **Start / stop** — `start [N]` resolves the epic (preselecting the sole live one), prints `epic-status`, and writes `epic_session.md` so the next `/iflow` asks before picking the next child. `stop` / `abort` deletes `epic_session.md`.

**What it asks you:** To iterate on the draft until you confirm it (`Status: confirmed`); one consolidated confirm before publishing (after a dry-run list of titles + labels); for `start`, one confirm (stay one-and-ask / cycle this stage / auto / drive / abort) and before replacing another session. Never silent-picks.

**Example:**

```text
iflow epic 144
# → drafts .issueflows/05-epics/epic144_plan.md  (Status: draft)
# → you confirm → Status: confirmed
iflow epic 144 publish stage 1
# → creates stage-1 issues (yolo labels per judgment), task list on #144
iflow epic start 144
# → writes epic_session.md (one-and-ask); next /iflow asks before pick
issue-flow agent epic-status 144 --json
# → current stage + next_candidates for /iflow-pick / /iflow-cycle
```

**Result:** A durable epic plan file; published stages become ordinary issues you pick/yolo/cycle as usual. Epics decompose into the normal single-issue lifecycle; they do not replace it.

**Related:** [Create and run epics](https://issue-flow.readthedocs.io/en/latest/how-to/epics/)

---

## Hands-off and special runs

### `/iflow-yolo` — all-in-one for small issues

**When to use:** The change is genuinely small and low-risk (typo, one-line fix, doc tweak) and you want to skip the usual checkpoints. For anything bigger, use the individual commands.

**Arguments:** The issue (number or URL), plus any `bump` / `patch` / `minor` / `major` / `draft` / `stay` tokens to forward to close.

**What it does:**

1. **Preflight** (any failure aborts before the chain starts): refuses on `main` / `master`; refuses if `git status --porcelain` shows unrelated uncommitted changes; runs `uv run pytest` up front and refuses if anything fails.
2. **Chain:** `/iflow-capture` → `/iflow-plan` (auto-confirmed short plan; aborts if the scope check reveals the change isn't actually small) → `/iflow-build` → `uv run pytest` again → `/iflow-close yolo` (changelog written without a prompt; PR merged with `gh pr merge --squash`, then switch to the default and pull).
3. Does **not** run `/iflow-cleanup`.

**What it asks you:** **One consolidated confirmation** up front listing the full planned chain (issue, branch, repo, downstream flags). After that it only stops for a human decision: a failing test, a merge conflict, or a scope that turns out not to be small.

**Result:** A merged PR and the default branch pulled — or an abort at the first ambiguity.

**Related:** [Fast-track a small issue](https://issue-flow.readthedocs.io/en/latest/how-to/yolo/)

### `/iflow-fix` — interactive iterative-fixes session

**When to use:** You have a bucket of small, iterative fixes (little bugs, typos, chores, polish) to knock out on one branch, rather than a single well-defined deliverable.

**Arguments:** An optional session name (used for the issue title and branch slug). No name → agent invents a short kebab slug from context (fallback `iterative-small-fixes`; baked `fix_auto_name = true`). During an active session, a `/iflow-fix <description>` (or just describing a fix) means "run the next fix". Toggle with `fix_auto_name` under `[issueflow]` (re-run `issue-flow update`).

**What it does:**

1. **Set up (once).** Preflight (default branch, `git fetch --prune`, clean tree); resolve the session name without a separate naming confirm; create a GitHub issue with `gh issue create` and capture `N`; create branch `<N>-<slug>` (off the default, or — when already on a non-default branch — ask whether to branch from current or default); delegate local capture to `/iflow-capture`; seed `issue<N>_status.md` with an unchecked `- [ ] Done` and an empty **`## Iterative fixes log`**.
2. **Loop.** For each proposed fix: restate it, write a short inline plan, implement **only on confirmation**, and append a dated bullet to the **Iterative fixes log**. A fix that turns out to be a real feature is split out into its own issue instead.
3. **Finish.** Tells you to run `/iflow-close` to land the session (it never auto-runs it); reminds you about `/iflow-cleanup` after the PR merges.

**What it asks you:** To confirm creating the session issue + branch; to confirm **each** fix before it is implemented.

**Coexists with `/iflow-pick fix` and `/iflow-issue`:** pick-fix is a one-shot general-fixes setup; `/iflow-issue` creates one well-specified normal issue; `/iflow-fix` stays and drives the small-fixes loop until close. While a session is active, drive it with `/iflow-fix` + `/iflow-close`, not `/iflow`. GitHub only (`gh`); GitLab is not supported.

**Result:** A session issue + branch with a running fixes log, ready to land via `/iflow-close`.

**Related:** [Run a fix session](https://issue-flow.readthedocs.io/en/latest/how-to/fix-session/)

### `/iflow-ops` — ops / no-PR work

**When to use:** The work should not open a PR — staging→production promote, feature-flag flip, external deploy checklist, tag-only steps with no product diff.

**Arguments:** The issue (or the focus issue).

**What it does:**

1. Resolve / capture the focus issue.
2. Preflight: refuse product-code dirty trees; the default branch is allowed.
3. Run the ops checklist; log bullets in `issue<N>_status.md`.
4. Finish with `/iflow-close ops` (aliases `nopr` / `no-pr`): local archive, optional `.issueflows/` commit (default branch OK), `gh issue close` — **no PR**.

**Label:** when `label_flows` is on, `/iflow-pick` routes issues carrying `ops` (default `"ops"`) here. If both `ops` and `yolo` are present, **ops wins**.

**What it asks you:** A confirmation for each checklist step, and a final checklist confirm before closing.

**Result:** Local tracking solved + GitHub issue closed, without a pull request.

**Related:** [Do ops work without a PR](https://issue-flow.readthedocs.io/en/latest/how-to/ops/)

### `/iflow-cycle` — batch-process a queue of yolo-fit issues

**When to use:** You have several small, well-specified issues and want them landed hands-off under **one** up-front confirm — the batch form of `/iflow-yolo`.

**Arguments:** A queue spec, for example:

- `yolo` — alias for `label:yolo` (all open issues with the configured yolo trigger label)
- `label:<L>` — every open issue with that label
- explicit numbers — e.g. `12 15 18`
- `epic <N> [stage <k>]` — current (or named) stage of an epic
- optional: `onfail:stop|skip`, `max:<n>`, `resume`, `parallel:<n>` (experimental)

**What it does:**

1. Expands aliases, then resolves the queue with `issue-flow agent queue … --json` (dependency order; closed issues skipped; blocked ones set aside).
2. Cap check (default max 10 without `max:<n>`).
3. Writes `cycle_status.md`, then for each issue runs the full yolo chain from a clean default branch (merge → pull → next).
4. `onfail:stop` (default) halts on the first failure and leaves the tree clean on default; `onfail:skip` parks the failed issue and continues.

**What it asks you:** **One consolidated confirm** (ordered queue, skipped/blocked, auto-merge). Afterwards it stops only when input is strictly necessary: an unfixable failure, a refused merge, a spec that is ambiguous or not actually small, or anything outside the confirmed queue.

**Example — all yolo-labelled issues:**

```text
iflow review yolo
# → table of open issues with add / keep / skip
# → confirm → labels applied
iflow cycle yolo
# → agent queue --label yolo
# → confirm the ordered list
# → each issue: capture → plan → build → close yolo (PR merged)
# → back on default, clean, between issues
```

**Conflict stance:** sequential cycles merge each PR and return to a clean default before the next issue, so shared files like `HISTORY.md` stay single-writer. `/iflow-cycle yolo` is the alias for `label:yolo`. See `04-designs-and-guides/parallel-cycle.md` for experimental `parallel:<n>` (merges still serialized) and `04-designs-and-guides/separate-workspaces.md` for one-window-per-worktree layout.

**Result:** A batch report of merged/failed/not-reached issues; remind the user to run `/iflow-cleanup` once afterward to prune merged local branches.

**Related:** [Run a cycle of issues](https://issue-flow.readthedocs.io/en/latest/how-to/cycle/)

### `/iflow-auto` — unattended large-change orchestration

**When to use:** You have a **confirmed** epic plan and want overnight hands-off progress through a stage, then an adversarial inter-epoch review.

**Arguments:** Epic `<N>`, optional `stage <k>`, optional `loops:<n>`, `review` (adversarial only), or `status` / `dry-run`.

**What it does:**

1. Requires `epic<N>_plan.md` with `Status: confirmed`; resolves the stage via `epic-status`.
2. Resolves the loop budget (`loops:<n>` > baked `[issueflow].auto_adversarial_loops`, currently **2** > 2).
3. Writes `auto_status.md` and runs `/iflow-cycle` for that stage.
4. Runs an adversarial review against the epic and stage goals (criteria in `.issueflows/04-designs-and-guides/advanced-auto-mode.md`); records `adversarial_clear` or `adversarial_findings`. Findings reopen issues or create blocker issues. Standalone: `/iflow-auto <N> review`.
5. **Loop control:** on findings, re-queues the open work via `/iflow-cycle` and re-reviews while `loop_count` < budget.
6. **Next-epoch gate:** starts stage `k+1` only when `epic-status` marks stage `k` `done` and no open blockers remain; otherwise `epoch_gated`.

**What it asks you:** **One overnight confirm** (authorizes cycle auto-merge **and** adversarial reopen/create). When the loop budget runs out with work still open, it **stops and asks**: accept / grant N more loops / abort.

**Result:** Stage queue processed via cycle; durable `auto_status.md`; blockers reopened or created; epochs advance only when the queue is clear.

**Related:** [Use auto mode](https://issue-flow.readthedocs.io/en/latest/how-to/auto-mode/)

### `/iflow-drive` — compose epic → publish → auto-all

**When to use:** You have an **existing** GitHub issue `<N>` that should become an epic and you want the whole path hands-off: draft, publish every stage, `/iflow-auto` each epoch, a final review, then local `-d` cleanup and `/iflow-status`.

**Arguments:** Issue `<N>` (required), optional `grill` / `grill-me`, optional `loops:<n>`, or `dry-run`. Mid-run `abort` / `stop` / `cancel` / `halt` stops at the next stage or issue boundary.

**What it does:**

1. Writes `drive_status.md`.
2. Drafts `epic<N>_plan.md` via `/iflow-epic <N>` (auto-confirmed unless grill-me / `grill_me_default`). Skips draft/publish when the plan is already `Status: confirmed`.
3. Publishes every unpublished stage (the `Published: #<M>` lines are committed off the default branch).
4. Runs `/iflow-auto <N>` for each unfinished published stage, honouring `epoch_gated`.
5. Final `/iflow-auto <N> review`; creates/reopens leftover findings. Does not start another epoch.
6. `/iflow-cleanup` `local only` **and skip Phase A2**: `git branch -d` on reachable branches only (squash-landed locals stay). Then `/iflow-status`.

**What it asks you:** **One drive confirm** covering draft-accept, publish-all, auto-all, final-review creates, and reachable-only cleanup. It still pauses for auto's budget ask and for cycle/yolo stop conditions. See `.issueflows/04-designs-and-guides/drive-mode.md`.

**Result:** Epic published and driven through auto; findings issues recorded; reachable local branches pruned; status report.

**Related:** [Drive an epic hands-off](https://issue-flow.readthedocs.io/en/latest/how-to/drive/) · [Use auto mode](https://issue-flow.readthedocs.io/en/latest/how-to/auto-mode/)

---

## Helpers

### `/iflow-pause` — park work safely

**When to use:** You need to stop partway through an issue (context switch, blocked on input) without closing it.

**Arguments:** Optional short note that becomes the **Remaining work** text.

**What it does:**

1. Updates `issue<N>_status.md` with **Done so far**, **Remaining work**, and **Paused on** sections. The `- [ ] Done` checkbox stays unchecked.
2. Moves the whole `issue<N>_*` group from `.issueflows/01-current-issues/` to `.issueflows/02-partly-solved-issues/`.
3. Never deletes branches, never force-pushes, never runs tests.

**What it asks you:** **One** consolidated prompt offering a WIP commit and/or `git switch <default>`.

**Result:** The issue is safely parked under `02-partly-solved-issues/` with clear resume notes. Re-open via `/iflow-pick` or `/iflow-capture <N>` (which asks for the archived-issue confirmation).

**Related:** [Park and resume](https://issue-flow.readthedocs.io/en/latest/how-to/park-and-resume/)

### `/iflow-status` — status overview of all issues (read-only)

**When to use:** You want a bird's-eye view of where every issue stands, rather than acting on the single focus issue.

**Arguments:** Nothing (full report), `local` (skip the GitHub query), or a hint like `milestone v0.4` to bias the GitHub section.

**What it does (all read-only):**

1. **Context** — current branch, default branch, clean/dirty tree, ahead/behind; focus issue `N` derived from the branch when it matches `^<N>-.+`.
2. **Focus issue** — the active group in `.issueflows/01-current-issues/` and its lifecycle stage (capture / plan / build / close) using the same file-presence logic as `/iflow`, plus the suggested next step.
3. **Parked work** — each `issue<n>_*` group under `.issueflows/02-partly-solved-issues/` with title and one-line status.
4. **Solved archive** — count of distinct solved issues under `.issueflows/03-solved-issues/` and the most recent few.
5. **Open GitHub issues** — `gh issue list` cross-referenced against the local folders, tagged **focus** / **parked** / **solved-locally** / **untracked**. Skipped gracefully when `gh` is unavailable or `local` was passed.
6. **Summary** — one terse line.

**What it asks you:** Nothing. It writes nothing, moves no files, and creates no branches, commits, or GitHub issues.

**Result:** A consolidated, read-only status report.

**Related:** [Concepts](https://issue-flow.readthedocs.io/en/latest/concepts/)

### `/iflow-review` — review open issues and apply labels

**When to use:** You want help deciding which open GitHub issues should carry workflow labels (v1: the configured `yolo` label).

**Arguments:** Nothing (list kinds and ask), or `yolo` to run the yolo review.

**What it does:**

1. **Kind** — if omitted, lists supported review kinds and asks.
2. **Config / label** — resolves `yolo_label` (and notes `label_flows`); creates the label if missing.
3. **Candidates** — lists all open issues (`issue-flow agent label-candidates`), including already-labelled ones for re-score.
4. **Judge** — yolo-fitness (same criteria as `/iflow-epic`); proposes **add** / **keep** / **skip** (never auto-removes).
5. **Apply** — `issue-flow agent label-apply` (or `gh issue edit --add-label`). No issue creation; no label removals in v1.

**What it asks you:** Confirmation before creating a missing label, and **one consolidated confirm** before applying labels.

**Result:** Selected open issues carry the target label so `/iflow-pick` can route them (when `label_flows` is on), or `/iflow-cycle yolo` can batch them.

**Related:** [Run a cycle of issues](https://issue-flow.readthedocs.io/en/latest/how-to/cycle/)

---

## Maintenance

### `/iflow-doctor` — audit and repair `.issueflows/`

**When to use:** Something in the tracking folders looks off: several issue groups in `01-current-issues/`, leftovers, the same issue in two folders, missing folders.

**Arguments:** None.

**What it does:** Runs `issue-flow doctor` / `issue-flow agent audit` to list dirty conditions, then offers **safe repairs** only (create missing folders, sweep finished or stale groups out of `01-current-issues/`) via `issue-flow agent repair`.

**What it asks you:** A confirmation before applying any repair. It never deletes issue files.

**Result:** A clean `.issueflows/` tree, or a report of what needs a human decision.

**Related:** [Concepts](https://issue-flow.readthedocs.io/en/latest/concepts/)

### `/iflow-archive` — condense the solved-issues archive (destructive, gated)

**When to use:** `.issueflows/03-solved-issues/` has grown large and most of its `issue<N>_*` groups are no longer worth keeping as individual files.

**Arguments:** Nothing (archive all but the 5 most recent solved groups), `keep <K>` (keep the `<K>` most recent), an explicit list of issue numbers, or `all`.

**What it does:**

1. **Preflight** — requires a **clean working tree** (stop if dirty) and records the pre-archive ref via `git rev-parse HEAD`.
2. **Select** — lists every solved group (number + title), applies your input rule, and shows the candidate list for you to adjust.
3. **Summarise** — appends to `.issueflows/03-solved-issues/YYYY-MM-DD_archived_issues.md`: a header with the pre-archive ref and recovery recipe (`git show <ref>:<path>`), then one section per issue with source URL, archived file names, and a 2–4 sentence outcome summary.
4. **Delete** — removes the archived groups' files (`issue-flow agent archive <N> ...` when the CLI is installed, else `git rm`).

**What it asks you:** **One consolidated confirm** covering exactly which issues get summarised and that their files will be **deleted**; afterwards, a commit offer (it never pushes).

**Result:** One dated summary file replaces the archived groups; every original file remains recoverable from git history via the recorded ref.

**Related:** [Concepts](https://issue-flow.readthedocs.io/en/latest/concepts/)

### `/iflow-pr-sync` — refresh dirty open PRs

**When to use:** Another merge (usually `HISTORY.md` bullets) left sibling open PRs `DIRTY` / `BEHIND` / `CONFLICTING` on GitHub.

**Arguments:** Nothing (every open PR GitHub marks as needing an update), PR numbers (e.g. `/iflow-pr-sync 259 261`), `dry-run` (list only), `nopush` (sync locally, don't push), or `all` (every open PR, not only dirty ones).

**What it does:**

1. Lists candidates with `issue-flow agent pr-sync --dry-run --json` (PR number, head branch, merge state, URL).
2. For each head, in a worktree: `issue-flow agent sync-branch` onto `origin/<default>`, keeping both sides of a changelog-only `## [Unreleased]` conflict, then `git push --force-with-lease`.
3. Stops the batch at the first conflict that is not changelog-shaped; later PRs stay untouched.

**What it asks you:** **One consolidated confirm** listing every head that will be rewritten and force-with-lease pushed. It never merges.

**Result:** Refreshed PR heads (CI re-runs on them) and a per-PR report.

**Related:** [Refresh dirty open PRs](https://issue-flow.readthedocs.io/en/latest/how-to/pr-sync/)

### `/iflow-graphify` — rebuild the knowledge graph (optional)

**When to use:** The project has the optional [graphify](https://graphify.net) integration enabled (the `graphify` CLI is on `PATH` and a `graphify-out/` folder is present), and the graph has gone stale relative to the source tree.

**Arguments:** Optional graphify subcommand and args, forwarded verbatim. Common picks:

- *(nothing)* — AST-only build of the project root (`graphify update <project>`). **No LLM API key required**; produces the full `graphify-out/`. The default.
- `extract` — adds the slower semantic LLM pass for richer cross-file relationships. Needs an API key (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MOONSHOT_API_KEY`) or `--backend ollama` for a local LLM via [Ollama](https://ollama.com). Cursor's own LLM is **not** available to subprocesses.
- `watch` — long-running watcher that auto-rebuilds on save.
- `cluster-only` — rerun clustering on the existing `graph.json` without re-extraction (e.g. `cluster-only --no-viz`).
- `./subdir` — restrict the scan to a sub-directory (default subcommand: `update`).

**What it does:**

1. Runs `issue-flow graphify` (which shells out to the `graphify` CLI). If `issue-flow` is unavailable, falls back to `graphify update .` directly (`graphify .` alone is **not** valid — graphify requires a subcommand).
2. If `graphify` is not installed, prints install hints (`uv tool install graphifyy`) and stops — never silently retries.
3. If `graphify extract` fails with "no LLM API key found", suggests setting one of the supported env vars, or using `--backend ollama`, or dropping back to the default `update` subcommand.
4. Verifies that `graphify-out/graph.html`, `GRAPH_REPORT.md`, and `graph.json` exist after a successful run.

**What it asks you:** Nothing. `/iflow`, `/iflow-build`, and `/iflow-close` may *suggest* a rebuild but never invoke `/iflow-graphify` automatically.

**Result:** A refreshed `graphify-out/` so `/iflow-build` can navigate by graph instead of grepping.

**Related:** [Graphify integration](https://issue-flow.readthedocs.io/en/latest/graphify/)

---

## Branch and folder hygiene

Two recurring pain points the workflows actively help with:

- **Stale local branches that look "several commits ahead of main" after a merged PR.** `/iflow-close` switches back to the default branch after opening or updating the PR when the tree is clean, unless you pass `stay` / `don't switch`. `/iflow-cleanup` detects merge status after the PR is merged and offers (with one consolidated confirm) to `git fetch --prune` and run `git branch -d` on every local branch reachable from the default branch. Squash-landed branches are unreachable by definition, so `-d` refuses them; cleanup collects those into a **second, dedicated confirm** for `git branch -D` that prints each tip SHA (restore with `git branch <name> <tip>`). Branches with unique commits are never offered for deletion.
- **Left-overs in `.issueflows/01-current-issues/`.** Both `/iflow-capture` (when a new issue is captured) and `/iflow-build` (before implementation begins) sweep that folder: every `issue<n>_*` group **other than the focus issue** is moved automatically to `.issueflows/03-solved-issues/` if a status file contains `- [x] Done`, otherwise to `.issueflows/02-partly-solved-issues/`.

All workflows that touch git also run a short **branch-status preflight**: `git fetch --prune`, current branch, ahead/behind vs the default branch, and a warning when the current branch's leading digits refer to an issue already archived in `02-`/`03-`.

---

## End-to-end flow

Tip: at any point in the linear flow below, you can just run `/iflow` and it will dispatch to the right step based on current state.

```text
(no issue chosen yet)
    │  /iflow-pick   → choose issue, create branch, run /iflow-capture
    ▼
GitHub issue
    │  /iflow-capture   (or /iflow)
    ▼
.issueflows/01-current-issues/issueN_original.md
    │  /iflow-plan
    ▼
issueN_plan.md  (user confirmed)
    │  /iflow-build
    ▼
Code + tests (+ status updates during work)
    │  /iflow-close  [optional: bump <patch|minor|major|alpha|beta|rc|…>]
    ▼
Commit → push → PR
    │
    │  (PR merges on GitHub)
    │  /iflow-cleanup
    ▼
Default branch, stale local branches deleted (with confirms)

Detours:
  /iflow-setup  — guided first-time project setup
  /iflow-init   — cold-start / check the harness (does not capture issues)
  /iflow-pause  — park mid-stream; moves issueN_* to 02-partly-solved-issues/
  /iflow-yolo   — chain capture → plan → build → close for tiny fixes (safeguarded)
  /iflow-ops    — ops / no-PR work (staging→prod, flags, external deploys)
  /iflow-fix    — interactive session: one branch, many small fixes, then /iflow-close
  /iflow-issue  — create one well-specified normal GitHub issue (optional branch + capture)
  /iflow-split  — cut an over-large issue into linked GitHub sub-issues
  /iflow-status — read-only overview of all issues (focus / parked / solved + GitHub)
  /iflow-doctor — audit/repair dirty .issueflows/ folders
  /iflow-review — review open issues and apply labels (v1: yolo)
  /iflow-epic   — stage a large change; publish stages as real issues
  /iflow-cycle yolo — auto-process all open issues with the configured yolo label
  /iflow-auto <N> — unattended epic stage via cycle + adversarial review
  /iflow-drive <N> — compose epic → publish → auto-all → final review → local -d cleanup
  /iflow-archive — condense old solved issues into a dated summary file (gated deletion)
  /iflow-pr-sync — refresh open PRs that went dirty after another merge
```

The skill packages under `.cursor/skills/` are the primary workflow surface. This document is a readable overview only.
