# Close, changelog, and release

What `/iflow-close` does around changelogs, versions, CI, and syncing with the default branch. Each section below was a separate design note; they are grouped here so the folder stays small (issue #406).

<a id="changelog-timing"></a>

## Changelog timing — in the PR, or deferred until default

**Issue:** [#171 — Timing of updating changelog](https://github.com/jepegit/issue-flow/issues/171)
**Status:** decided 2026-07-19, implemented in the same issue.
**Follow-up:** [#288 — `defer_changelog`](https://github.com/jepegit/issue-flow/issues/288)
writes on the default branch after merge when the knob is on (default **off**).

### Context

Agents sometimes asked about `HISTORY.md` / CHANGELOG **after** a PR was
accepted or merged. `/iflow-close` already updates the changelog in step 3
(before commit / push / PR), but confirm-decline used to skip and continue,
so PRs could land without a bullet — inviting a post-merge ask.

Two issue branches appending `[Unreleased]` still collide (#240 / #260).
`defer_changelog` is the **prevention** path: the issue branch never touches
the file. Repair (`sync-branch` / `pr-sync`) stays the default-off path.

### Decisions

1. **Reuse `confirm_changelog_update`** — it still gates *whether / what text*.
   It does not choose *when* the file is written.
2. **Default `false`** — write without asking so the bullet lands in the PR
   commit (same as yolo history behaviour). Projects can set `true` for a
   confirm gate.
3. **Decline is blocking** (when confirm is on) — stop close; offer write /
   revise / `nohistory` / abort. No silent skip-and-continue.
4. **Never invent a post-close *offer*** — close, history-update, cleanup, and
   rules forbid proposing a *new* HISTORY/CHANGELOG bullet after close has
   finished or after merge. A draft opened earlier via `/iflow-build` early PR
   does **not** skip close's HISTORY *decision*.
5. **`defer_changelog` (default off, #288)** — when on, step 3 still decides
   the bullet (`nohistory` / `log` / confirm) but writes
   `### Deferred changelog` on `issue<N>_status.md` and the PR body instead of
   `HISTORY.md`. `/iflow-cleanup` A1 and yolo post-pull run
   `issue-flow agent apply-changelog --issue N` on the **default** branch
   (from **home** even under `stay`) and commit `docs: changelog for #<N>`
   when it wrote. That apply is not a new offer.

### Follow-up (#404) — trailers, not a file edit

Decided 2026-10-23 with the plan for #404. Close no longer writes
`HISTORY.md` on the issue branch, and cleanup no longer runs
`apply-changelog`. The bullet is three commit-message trailers
(`Changelog`, `Changelog-Date`, `Changelog-Id`). `issue-flow changelog release`
prepends one version section on the default branch and deletes
`## [Unreleased]` the first time it runs. `defer_changelog` stays in config
so old files still parse, but templates ignore it when choosing where to
write. `apply-changelog` stays for a status file that already has
`### Deferred changelog`.

A repo that still has `## [Unreleased]` keeps those bullets until the first
`changelog release`, which folds them into the new version section and
removes the heading. Do not recreate the heading after that.

### Link

Issue #171 / #288 / #404; knob table in [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).
Conflict *repair*: [changelog-conflicts.md](./changelog-conflicts.md) (#240),
[pr-queue-sync.md](./pr-queue-sync.md) (#260 Part A).

<a id="changelog-conflicts"></a>

## Changelog conflicts — sync before merge, keep both bullets

**Issue:** [#240 — Changelog conflicts](https://github.com/jepegit/issue-flow/issues/240)
**Status:** decided 2026-09-04, implemented in the same issue.

### Context

`/iflow-close` synced with `git pull --ff-only` **on the issue branch**, which
only follows that branch's own upstream — it can never pick up commits that
landed on the *default* branch while the issue was in flight. The collision
therefore surfaced late, at merge time, as `mergeable: CONFLICTING` /
`mergeStateStatus: DIRTY`.

The reported case (a **sequential** `/iflow-cycle yolo` on `jepegit/cellpy`,
queue `#961 → #962 → #963`) shows why this is not just a parallel-dispatch
problem: an unrelated PR merged to `master` during #961's ~8 minute
test/implement/test window, and the only conflict was two additive bullets
under `## [Unreleased]`. Cycle step 6b treated the refused merge as a stop, so
`onfail:stop` halted the batch and #962 / #963 were never reached.

Sequential mode's "shared files stay single-writer" property holds *inside* the
cycle, but says nothing about the default branch moving externally.

### Decisions

1. **Sync explicitly, before push and again on a conflicted merge.** Close
   step 6 replays the issue branch onto `origin/<default>`; step 8a retries a
   `CONFLICTING` merge once after re-syncing.
2. **Rebase, not merge.** Keeps history linear and matches the manual
   precedent in the issue. The cost is that close must push with
   `--force-with-lease` (issue branch only — the default branch is never
   rewritten). `--strategy merge` exists for projects that would rather have a
   merge commit than a force-push.
3. **Auto-resolve only the mechanical shape.** All of: the changelog is the
   **only** conflicted file, every conflict region sits under
   `## [Unreleased]`, and both sides contain only list items. Then keep **all**
   bullets. Anything else — code conflict, edited or deleted bullet, renamed
   heading, promoted version section — aborts and stops.
4. **Ordering: the in-flight bullet goes last.** Already-landed bullets keep
   their positions. This matches `iflow-history-update` mode A's append
   semantics, so a resolved conflict is indistinguishable from having written
   the bullet after the other one landed. Note this is the **opposite** of the
   manual resolve in the issue report (which put ours first); the issue asked
   for one documented order, and consistency with mode A won.
5. **No config knob for the resolver.** Keep-both is always on. Prevention
   of the collision is a *different* knob: `defer_changelog` (#288, default
   **off**) so issue branches never write HISTORY. This repair path stays
   the default.
6. **One command, not two.** `issue-flow agent sync-branch` owns the git side;
   the pure text resolver lives in `issue_flow.history` for tests and reuse. A
   separate `agent history-resolve` was floated in the issue but has no second
   caller — the parallel coordinator *appends* bullets rather than resolving
   markers, and it can call `sync-branch` when a worker PR does go dirty.
7. **Never paper over a blocked merge.** No `gh pr merge --admin`, no skipping
   checks. A rebased branch needs a fresh check run, so watch-then-merge (with
   `--auto` as last resort) stays as it was.
8. **The CLI never pushes.** A rebase rewrites the branch, so the
   force-with-lease push stays in `/iflow-close`, inside the user's token and
   confirmation surface.

### Implementation

- `src/issue_flow/history.py` — conflict-marker parsing and the keep-both
  resolver, pure text in / text out, with explicit refusal reasons
  (`not_unreleased_section`, `heading_conflict`, `non_bullet_content`,
  `empty_side`, `unterminated_conflict`).
- `issue-flow agent sync-branch [--strategy rebase|merge] [--json]` in
  `agent.py` / `cli.py`, plus rebase/merge/unmerged-path helpers in
  `gitutils.py`. An abort **rolls back** any resolve made earlier in the same
  run, and the payload stops claiming `changelog_resolved` accordingly.
- Templates: `iflow_close` (step 6 sync + step 8a retry), `iflow_history_update`
  (the documented keep-both rule), `iflow_cycle` (step 6b is no longer tripped
  by a changelog-only refusal), `iflow_yolo`, and the mirrored command files.

### Links

Issue #240; timing rules in [changelog-timing.md](./changelog-timing.md);
parallel coordinator in [parallel-cycle.md](./parallel-cycle.md);
multi-PR refresh in [pr-queue-sync.md](./pr-queue-sync.md) (issue #260);
prevention via `defer_changelog` in #288 (default off).

### Prevention that removes the shared heading (#404)

Keep-both still repairs a repo whose open PRs edit `## [Unreleased]`.
New closes do not. They put the bullet in commit trailers, and
`issue-flow changelog release` is the only writer of a new version section.
The first release after adoption folds the bullets already under
`## [Unreleased]` into that section and deletes the heading. After that,
the heading stays gone, so this conflict shape stops occurring for
changelog text. Design-guide and status-file keep-both is unchanged.

<a id="release-strategies"></a>

## Release strategies (version bump)

Context: issue #125 — in tag-versioned projects (cellpy), the
`iflow-version-bump` skill's `uv version --bump` advice was wrong: the built
version comes from git tags, so "bumping" means tagging, not editing
`pyproject.toml`.

### Decision

`iflow-version-bump` resolves a **release strategy** before doing anything,
in this order:

1. The **"Release & version bump" section of `this-project.md`** — user-owned
   documentation always wins (same deference pattern as the Python toolchain
   rules).
2. **Detection from `pyproject.toml`** — `dynamic = ["version"]` plus a
   tag-driven backend (setuptools-scm / hatch-vcs / versioningit) → tag
   strategy; static `[project] version` → uv strategy.
3. **Default** — the original uv behaviour.

**Tag strategy semantics:** never write a version into `pyproject.toml`, and
never tag an issue-branch commit — under squash merges that commit never
lands on the default branch. `/iflow-close` only *plans* the tag (computed
from the latest tag with the shared level table) and promotes the changelog
with the planned version; the tag is created after the merge, on the updated
default branch, by `/iflow-cleanup`'s consolidated confirm or the yolo
close's post-merge step.

**Self-healing:** when the strategy came from detection or user explanation
(not the brief), the skill records it into `this-project.md` so it is only
discovered once. This is how pre-existing projects (whose briefs predate the
section) converge without `issue-flow update` touching the user-owned brief.

### Alternatives considered

- `version_strategy` key in `.issueflows/config.toml` — rejected for now:
  the brief is the human-facing place for project conventions, and no code
  reads the value yet. Revisit if a deterministic `issue-flow agent
  version-plan` CLI (PEP 440 next-tag arithmetic) lands as a follow-up.
- Tagging during `/iflow-close` (pre-merge) — rejected: wrong commit under
  squash merges.

<a id="pr-queue-sync"></a>

## PR queue sync — refresh dirty open PRs after a merge

**Issue:** [#260](https://github.com/jepegit/issue-flow/issues/260)
**Status:** Part A implemented with the issue; Part B (`defer_changelog`) shipped in #288 (opt-in, default off).

### Context

`#240` / `issue-flow agent sync-branch` fixes the *current* close branch when
`HISTORY.md` collides under `[Unreleased]`. It does **not** help sibling open
PRs that go `DIRTY` after another squash lands (or after a version promote).
GitHub’s “Update branch” cannot keep-both bullets and fails hard on promoted
version headings (as with dual `0.4.13` promotions on #255 vs #259).

### Decisions

1. **Repair skill + CLI first.** `/iflow-pr-sync` and
   `issue-flow agent pr-sync` loop: worktree → `sync-branch` →
   `git push --force-with-lease`. Explicit confirm in the skill; CLI itself is
   non-interactive (agent owns the confirm).
2. **Reuse keep-both.** No second resolver — same `history.py` rules; heading /
   code conflicts still abort that head. Since #386 the same rule is applied
   per path to additive bullets / table rows in `04-designs-and-guides/*.md`
   and to `issue<N>_status.md` (`history.resolve_additive_conflict`;
   `sync-branch` payload `resolvers`). Product code is never auto-resolved.
2b. **Stacked children.** `sync-branch --base <ref>` replays only the commits
   after a squash-landed parent (`git rebase --onto`); auto-detected when an
   ancestor branch is provably landed — merged PR, zero `git cherry` unique
   commits, or `gitutils.content_landed` (touched files byte-identical on
   `origin/<default>`). Payload: `base`, `base_detected`, `dropped_commits`.
3. **Default candidates = dirty only.** `--all-open` is opt-in.
4. **Ephemeral worktrees.** `../<repo>-prsync-<branch>` created as needed and
   removed by default (`--keep-worktrees` to retain).
5. **Prevention shipped (#288).** Optional `defer_changelog` writes the bullet
   on the default branch after merge (`issue-flow agent apply-changelog`).
   Default **off** — this skill stays the repair path when issue branches
   still edit HISTORY.

### Links

[changelog-conflicts.md](./changelog-conflicts.md),
[changelog-timing.md](./changelog-timing.md),
[parallel-cycle.md](./parallel-cycle.md).

<a id="gh-list-and-watch"></a>

## gh list and watch in `/iflow-close`

**Context.** Issue #172: agents already depend on `gh` for PRs, but close said
"when CI is green" without naming commands, and yolo fell straight through to
`--auto` when checks were pending. Issue #220: agents still missed the toolkit
outside close wording and asked for `gh run watch` by name.

**Decision.**

- Interpret "gh list / gh watch" as **`gh pr list`** + **`gh pr checks [--watch]`**
  (no top-level `gh list` / `gh watch`). Always pass `--repo <owner/repo>`.
- **List before create:** after push, `gh pr list --head <branch> --state open`;
  reuse/update an existing open PR instead of opening a second one.
- **Checks snapshot** after the PR exists; "CI green" means `gh pr checks` exits 0.
- **Fallback** when PR checks are empty / unavailable: `gh run list` then
  `gh run watch <run-id>` (same watch budget). Named in close + the `gh-ci` skill.
- **Yolo merge:** try `gh pr merge --squash` first; on pending/required checks,
  `gh pr checks --watch --fail-fast` under a hard wall-clock budget, then retry
  merge. **`--squash --auto` is last resort** (cap elapsed, checks never
  register, or watch unavailable). Red checks stop hands-off.
- **Budget:** `[issueflow].checks_watch_minutes` (default `15`), env
  `ISSUEFLOW_CHECKS_WATCH_MINUTES`. Baked into close/yolo/`gh-ci` at
  `issue-flow update`. Agent-enforced (`gh` has no max-duration flag).
  Non-positive values fall back to the default.
- **Discoverability (#220):** ship a model-invoked **`gh-ci`** skill (standard
  mode; not simple) plus thin pointers in close and the always-on rules. Close
  still owns the merge sequence; `gh-ci` is the shared command cheatsheet.

**Alternatives considered.**

- Always `--auto` (status quo) — rejected: agents never see CI fail in-session.
- Open-ended watch — rejected: can hang unattended yolo/cycle runs.
- Promote a new `issue-flow agent` watch subcommand — **landed in #317** as
  `issue-flow agent pr-ready [N] [--watch]` (classify + poll; never merges).
  Yolo still uses `gh pr checks --watch` on the merge path.
- **#321:** a check blocks `ready` unless `isRequired` is explicitly `false`.
  Omitted required + pending is `pending` even when `mergeStateStatus=UNSTABLE`
  (the #320 false-ready). Explicit optional noise (e.g. Cursor Approval) still
  does not block.
- Elevate `gh run watch` to equal primacy with `gh pr checks` — rejected (#220);
  keep #172 ordering.
- Rules-only / close-only expansion without a skill — rejected (#220); weaker
  discoverability when not already in close.

**Link.** Issues #172 / #220 / #317; `issue172_plan.md`, `issue220_plan.md`,
`issue317_plan.md`.

<a id="gh-repo-view-positional"></a>

## `gh repo view` takes a positional repo

**Context.** Issue #216: agents (and one skill template) called
`gh repo view --repo owner/name`, which fails with `unknown flag: --repo`.
Separately, Windows locale decoding in `gitutils._run` crashed on UTF-8
`gh issue view` output.

**Decision.**

- Document and teach: `gh repo view <owner/repo> --json …` (positional).
- Keep `--repo <owner/repo>` for other `gh` commands (`issue`, `pr`, `label`, …).
- Scaffolded resolve-root snippet and `/iflow-cleanup` skill state the exception
  explicitly; `gitutils._run` always uses `encoding="utf-8", errors="replace"`.

**Alternatives considered.**

- Wrap every default-branch lookup in `issue-flow agent preflight` only —
  rejected as sole fix; agents still shell out to `gh` in manual fallbacks.
- Force `PYTHONUTF8=1` / `PYTHONIOENCODING` in the environment — helpful but
  not under our control on every machine; fix the wrapper instead.

**Link.** Issue #216, `issue216_plan.md`.

<a id="default-branch-diverge"></a>

## Default-branch diverge (ff-only vs unpushed home commits)

**Issue:** [#303](https://github.com/jepegit/issue-flow/issues/303)
**Status:** decided 2026-09-19, implemented in the same issue.
**See also:** [`workspaces.md#separate-workspaces`](workspaces.md#separate-workspaces) (#255),
[`cleanup-and-branches.md#local-branch-cleanup`](cleanup-and-branches.md#local-branch-cleanup) (#243).
Changelog-only PR conflicts (#260 / #288) are a different class.

### Context

Worktree-first start keeps **home on the default branch** and used to
require `git pull --ff-only` before `worktree-add`. Cleanup A1 and
switchback do the same pull. That dead-ends when home is both ahead and
behind `origin/<default>` — typically an unpushed `.issueflows/` chore
(epic `Published: #N`, doctor, scaffold) plus a squash on origin, often
made worse by a local merge “to catch up”.

`worktree-add` already starts from fetched `origin/<default>`. The issue
branch is fine. The pain is **home default hygiene**.

### Decisions

1. **Starting work does not require a clean FF of home default.**
   Fetch, classify with `issue-flow agent default-sync`, FF only when
   `action` is `even` / `ff_only`, otherwise print and continue.
2. **`default-sync` is classify-only.** No mutate. Skills choose the
   recovery.
3. **Never** rebase default, `push --force` default, or push default to
   skip CI.

| `action` | Offer |
| --- | --- |
| `even` / `ff_only` | `git pull --ff-only` is safe |
| `report_ahead` | Print unique commits; do not silent-push |
| `tracking_pr` | Merge origin or cherry-pick onto a chore branch, then a tiny PR |
| `replay_tracking` | Replay tracking onto `origin/<default>` (chore + PR); no stacked merge |
| `stop_product` | Stop. User decides. Includes `HISTORY.md` / lock / source |

4. **Prevent:** epic `Published: #N`, doctor housekeeping, and scaffold
   updates do not sit unpushed on home default.
5. **`apply-changelog`** still writes `HISTORY.md` on default after merge
   (#260). A leftover HISTORY commit plus a moved origin classifies as
   `stop_product`.
