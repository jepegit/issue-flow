# Lifecycle and commands

<a id="command-surface"></a>

## Command surface: eleven commands with modes (#406)

**Context.** By October 2026 issue-flow shipped 30 lifecycle skills, an always-on
rule of ~4,500 words, full command copies for Claude Code and opencode (another
~24,000 words), and a scaffolded workflow doc of ~8,400 words. Agents loaded the
rule in every session, users could not remember which of yolo / cycle / auto /
drive or issue / fix / epic / split to use, and every feature added prose
without removing any.

**Decision.**

- Eleven commands: `iflow`, `setup`, `pick`, `plan`, `build`, `pause`, `close`,
  `cleanup`, `run`, `issue`, `status`. Merged commands take a **mode** as their
  first word (`run cycle`, `issue epic 42`, `status doctor`, `cleanup prs`).
- **Progressive disclosure.** Each skill folder holds a short `SKILL.md` router
  plus one mode file per mode. Only the router loads on invocation; the agent
  reads one mode file. Internal steps (`comments`, `version-bump`,
  `history-update`, `gh-ci`) became mode files of the command that uses them.
- **Thin always-on rule.** The rule body is the core contract only (layout,
  Done checkbox, command table, branch hygiene, workspaces). `CLAUDE.md`
  imports `AGENTS.md` and the Cursor `.mdc` points at it, so the rule loads once.
- **Claude Code is skills-first**; opencode keeps one-line command wrappers.
- **Word budgets** in `tests/test_command_surface.py` (rule ≤ 900, `SKILL.md`
  ≤ 1,600, mode file ≤ 3,000, workflow doc ≤ 1,500) stop the slow regrowth.
- **One-run migration.** `issue-flow update` prunes retired folders (project,
  canonical store, stamped user-global copies), rewrites retired stems in
  `config.toml`, and refreshes the Linguist block. A retired stem in a mode's
  `remove` list only removes `iflow-run` when all four of its parts are listed;
  otherwise it is dropped, so removing `gh_ci` never removes `iflow-close`.
- **Quieter diffs.** The managed Linguist block marks editor copies and
  archived issue folders `linguist-generated`. This repo gitignores
  `graphify-out/` and keeps design notes in a dozen topic files.

**Alternatives considered.** Keeping every command and only hiding extras by
profile (rejected: still 30 names to document and test). Aliases for the old
names (rejected by the maintainer: breaking change accepted, migration via
`update` instead). Collapsing the three issue files into one (deferred: small
line savings against wide churn in `agent.py` and in-flight projects).

**Link:** issue #406.

How the commands are shaped, named, and invoked, and how labels and knobs steer them. Each section below was a separate design note; they are grouped here so the folder stays small (issue #406).

<a id="slash-less-invocation"></a>

## Slash-less iflow invocation

Context: issue [#118](https://github.com/jepegit/issue-flow/issues/118).

### Problem

Cursor lifecycle skills are invoked explicitly (`disable-model-invocation: true`).
The slash menu requires `/iflow-plan`. On some keyboard layouts (Norwegian called
out in the issue) `/` is awkward; `@` attachment is awkward too.

### Decision

**Primary chat form:** `iflow <step>` (space-separated) — e.g. `iflow plan`,
`iflow pick`, `iflow close`. Plain `iflow` runs the dispatcher.

**Aliases:** hyphen (`iflow-plan`), slash (`/iflow-plan`), slash + space
(`/iflow plan`).

**Mechanism:** always-on rules in `templates/rules/_body.md.j2` (rendered into
`AGENTS.md` and `.cursor/rules/issueflow-rules.mdc`) instruct agents to treat
matching chat text as explicit skill invocation. Lifecycle skill bodies include
a one-line **Invoke** hint via `templates/skills/_invocation_forms.md.j2`.
`docs/issue-workflow.md` documents the space form first.

Skill folder names and YAML `name:` fields stay hyphenated (`iflow-plan`).

### What we did not do

- Remove `disable-model-invocation` (would auto-load heavy playbooks; violates
  #117 skill-authoring rules).
- Add a config opt-out in v1.
- Change Cursor's slash menu (product limitation).

### Alternatives considered

- Promote `@iflow-plan` — rejected; `@` is also awkward on Norwegian keyboards.
- Rename skill folders to spaces — rejected; invalid / non-portable paths.

<a id="rename-start-to-build"></a>

## Rename `/iflow-start` → `/iflow-build`

**Issue:** [#183 — renaming from start to build](https://github.com/jepegit/issue-flow/issues/183)
**Status:** decided 2026-07-19, implemented in the same issue.

### Context

The post-plan implement step was named `/iflow-start`. "Build" better matches
"implement the plan", and frees `start` for a future small auto-loaded prep
skill (not part of this issue).

### Decisions

1. **Hard cut** — no lasting `iflow start` / `/iflow-start` alias.
2. **`agent state` stage** string becomes `"build"`; `next_command` is
   `/iflow-build`. `STAGE_START` remains a Python alias of `STAGE_BUILD` for
   importers.
3. **Retirement** — `iflow-start` added to `RETIRED_COMMANDS` and
   `RETIRED_SKILLS` so `issue-flow update` prunes old scaffold files.
4. **Behaviour unchanged** — rename + docs only.

### Consequences

- Chat invoke: `iflow build` / `/iflow-build`.
- Yolo / dispatcher chains use `build` instead of `start`.
- Dogfood projects need `issue-flow update` after upgrade.

<a id="iflow-init-vs-capture"></a>

## `iflow-init` vs `iflow-capture` (#241)

**Status:** decided 2026-09-05.
**See also:** #183 (`iflow-start` → `iflow-build`) for the retire/rename pattern.

### Context

`/iflow-init` used to mean "capture this GitHub issue into `.issueflows/`"
(often inferred from the branch name). That overloaded the word *init*, which
users and the CLI already use for **scaffolding the harness** (`issue-flow
init`).

### Decisions

1. **Issue capture** is **`/iflow-capture`** (`iflow capture`, skill
   `iflow-capture`). Matches `issue-flow agent capture`.
2. **`/iflow-init`** is **harness cold-start / check** (off-path): guide
   `issue-flow init` when the scaffold is missing; on a **parent folder
   of git siblings** guide `issue-flow workspace bootstrap` (classify,
   then `--yes` after confirm); otherwise point at `update` / doctor /
   `/iflow-capture`. Never captures issues; never auto-dispatched by
   `/iflow`. The skill is also user-global (`both`, issue #310) so it
   exists before a project scaffold.
3. **No dual-meaning alias** for one release (same as #183). Loud docs +
   HISTORY note instead.
4. Lifecycle stage id is **`capture`** (`STAGE_CAPTURE`); `STAGE_INIT` remains
   a back-compat alias equal to `STAGE_CAPTURE`. Suggested next command is
   `/iflow-capture`.
5. Scaffold marker skill stays `skills/iflow-init/SKILL.md` (always emitted).
6. **`/iflow-setup` (#246) stays a separate off-path command.** It walks
   environment readiness (`uv` / git / `gh` / scaffold). `/iflow-init` only
   cold-starts or checks the issue-flow harness. Not aliased onto setup.

### Link

Issue #241, `issue241_plan.md`.

<a id="create-non-epic-issue"></a>

## `/iflow-issue`: create a normal (non-epic) issue

**Issue:** [#181 — create non-epic issue](https://github.com/jepegit/issue-flow/issues/181)
**Status:** decided 2026-07-19, implemented in the same issue.
**Scope:** new off-path slash command (`/iflow-issue`) + mirrored skill that
authors one well-specified GitHub issue and optionally starts the normal
lifecycle.

### Context

issue-flow already had two create-adjacent surfaces:

- `/iflow-pick fix` / `/iflow-fix` — general-fixes / iterative small-fixes buckets
- `/iflow-epic` — multi-issue staged work (requires an existing epic **anchor**)

There was no first-class way to file **one normal, well-specified** issue (real
body with acceptance criteria) and hand it into `/iflow-init` → `/iflow-plan`.

### Decisions

#### 1. Name: `/iflow-issue` (skill stem `iflow_issue`)

Reads as the third creation mode beside fix / epic. Rejected `iflow-new` /
`iflow-create` as vaguer.

#### 2. Off-path command + skill, same registration pattern as `/iflow-fix`

Ship `commands/iflow-issue.md.j2` and `skills/iflow_issue/SKILL.md.j2`, register
in `COMMAND_NAMES` / `SKILL_DIRS`, default step profile **reasoning** (drafting
quality). `/iflow` never auto-dispatches.

#### 3. Structured draft body (not a full plan)

Propose **Problem / context**, **Spec**, **Acceptance criteria**, optional
**Out of scope**. Confirm before `gh issue create`. Over-large drafts: offer
`/iflow-split` (flat) or `/iflow-epic` (staged) — no auto-split. See
[linked-sub-issues.md](./linked-sub-issues.md).

#### 4. Offer branch + `/iflow-init` after create; allow create-only

Default path mirrors `/iflow-pick` setup, then asks about `/iflow-plan` (never
auto-runs plan). Declining Phase 2 leaves a parked GitHub issue for later
`/iflow-pick` / `/iflow-init` — useful for epic anchors.

#### 5. Epic-anchor hint: leading `epic`

`/iflow-issue epic <intent>` prefixes the title with `Epic:` and applies the
`epic` label when `gh label list` shows it. `/iflow-epic` points missing-anchor
cases here.

#### 6. Coexist — do not merge with pick-fix or `/iflow-fix`

Different intents; docs cross-reference. No CLI `agent` helper in v1 (skills
call `gh` directly).

### Consequences

- Manifest +1 skill (all editors); +1 command for editors with `commands_dir`.
- Touch points: dispatcher off-path lists, rules body, workflow doc, README,
  review/fix/epic cross-links, templating tests.

### Notes for future work

- Optional labels/milestones beyond the epic-anchor label (user-asked only in v1).
- CLI `issue-flow agent issue-create` helper if agents need a deterministic path.

<a id="issue-fix-interactive"></a>

## `/issue-fix`: interactive iterative-fix sessions

**Issue:** [#54 — Allow for more interactive sessions](https://github.com/jepegit/issue-flow/issues/54)
**Status:** decided 2026-06-16, implemented in the same issue.
**Scope:** a new off-path slash command (`/issue-fix`) + mirrored skill for
working a stream of small fixes on a single long-lived branch.

### Context

issue-flow's linear lifecycle (`/issue-init` → `/issue-plan` → `/issue-start` →
`/issue-close`) assumes one well-defined deliverable per issue. Issue #54 asked
for a lighter, interactive mode: a single branch where you fix one small thing,
use the code, find the next small thing, and so on — each fix getting a short
plan and an implementation only if the user wants it, with everything recorded
in the issue's markdown and landed together via `/issue-close`.

### Decisions

#### 1. New off-path command, mirroring the existing command/skill pattern

`/issue-fix` ships as a `commands/issue-fix.md.j2` template **and** a mirrored
`skills/issueflow_issue_fix/SKILL.md.j2`, both registered in
`templating.py` (`COMMAND_NAMES`, `SKILL_DIRS`). It is **off-path** like
`/issue-pick`, `/issue-yolo`, and `/graphify`: `/iflow` never auto-dispatches to
it (it creates GitHub issues + branches and then drives an open-ended loop), and
the skill sets `disable-model-invocation: true`.

Manifest counts: cursor 25 → 27, codex 14 → 15 (skills 13 → 14).

#### 2. Always create a GitHub issue (`gh`); no local-only mode in v1

Per the issue comment, setup always creates a real GitHub issue via
`gh issue create` (after showing the title/body and confirming). A local-only
mode was considered (work without a GitHub issue, e.g. offline) and deferred —
keeping a single, predictable setup path for v1. GitLab is **not** supported:
issue-flow's external surface is `git` + `gh` (GitHub).

#### 3. Per-fix log lives in `issue<N>_status.md`

Each fix is appended as a dated bullet under an `## Iterative fixes log` section
in the existing `issue<N>_status.md`, rather than a dedicated
`issue<N>_fixes.md`. This keeps the issue group to the familiar
`_original` / `_status` shape and means the existing folder-sweep and
`- [ ] Done` / `- [x] Done` conventions keep working unchanged. The checkbox
stays unchecked for the whole session; `/issue-close` flips it when the work
lands.

#### 4. Coexist with `/issue-pick fix` (do not merge)

`/issue-pick fix` already creates a new general-fixes issue + branch, but then
hands back to the normal `/issue-plan` → `/issue-start` flow (a one-shot setup).
`/issue-fix` instead **stays** and runs the iterative loop until
`/issue-close`. They overlap on setup but serve different intents, so they
coexist; the docs cross-reference each other rather than folding one into the
other.

#### 5. Delegate, don't duplicate

Setup delegates local capture to the `/issue-init` flow (issue fetch +
`issue<N>_original.md` + archive sweep) and finishing to `/issue-close`
(tests, optional bump, status, commit, push, PR). `/issue-fix` only adds the
GitHub-issue creation, the branch-from-current-vs-default choice, the status
seed, and the fix loop on top.

#### 6. `/iflow` interaction: document only

An active `/issue-fix` session has an `issue<N>_original.md` but intentionally no
`issue<N>_plan.md` (each fix uses a lightweight inline plan instead). A stray
`/iflow` would therefore see "no plan file yet" and dispatch `/issue-plan`. v1
handles this by **documentation** — `/iflow`, its skill, and the rules tell the
user to drive an active session with `/issue-fix` + `/issue-close`, not `/iflow`.
A status marker that `/iflow` could detect and decline on was considered and
deferred as unnecessary complexity for v1.

### Consequences

- Two new template files; manifest entry count rises by 2 (per editor with a
  `commands_dir`) / by 1 for command-less editors (Codex).
- Touch points updated everywhere commands are enumerated:
  `commands/iflow.md.j2`, `skills/issueflow_iflow/SKILL.md.j2`,
  `rules/_body.md.j2`, `docs/issue-workflow.md.j2`, `README.md`, and
  `tests/test_templating.py` (counts + expected command/skill membership + a
  focused `/issue-fix` test).

### Notes for future work

- A local-only session mode (`/issue-fix local <name>`) could be added if users
  want offline / no-GitHub buckets.
- If sessions become long, a status marker enabling `/iflow` to recognize and
  defer to an active `/issue-fix` session would remove the documentation-only
  caveat in decision 6.

<a id="issue-review-labelling"></a>

## Issue review and labelling (`/iflow-review`)

**Context.** Issue #174: help users assess how open issues should be labelled.
Today label-driven flows consume a configurable `yolo` label
([label-driven-flows.md](./label-driven-flows.md)); nothing helped *assign*
that label systematically.

**Decision.**

- New off-path skill/command **`iflow-review`**. Bare invoke lists review
  **kinds** and asks; v1 kind is **`yolo`** only.
- Fitness criteria for `yolo` reuse `/iflow-epic`'s yolo-fitness wording
  (well-specified, mechanical/pattern-following, low blast radius, test-guarded;
  umbrella / design / flag-day → no).
- Candidate set = **all open issues** (re-score already-labelled; adds are
  no-ops). v1 never removes labels.
- Missing target label → offer `gh label create` under confirm, then continue.
- Thin CLI (no judgment): `issue-flow agent label-candidates` and
  `issue-flow agent label-apply`. Judgment stays in the skill.
- Standard mode only (omitted from `modes.simple`), same class as yolo/cycle.
- Queue planning's `_yolo_from_labels` honours the resolved `yolo_label`, not a
  hardcoded `"yolo"` string.

**Alternatives considered.**

- Skill-only `gh` shell with no CLI — rejected: other off-path flows
  (status/doctor) ship deterministic helpers; apply/list are pure plumbing.
- Auto-run from `/iflow-pick` or cycle — rejected: labelling is a deliberate
  batch triage step; keep off-path.
- Filter to unlabeled-only — rejected: user wants re-score of the full open set.

**Link.** Issue #174, `issue174_plan.md`.

<a id="label-driven-flows"></a>

## Label-driven flows (yolo label)

**Context.** Issue #106: typing slash commands for small issues is tedious;
GitHub labels already carry intent.

**Decision.**

- Two `[issueflow]` config keys, mirroring the `caveman_default` pattern
  (persisted `config.toml` > `ISSUEFLOW_*` env > default; re-render on
  `issue-flow update`): `label_flows` (default `true`) and `yolo_label`
  (default `"yolo"`).
- The hook lives in `/iflow-pick` only: a picked issue carrying the yolo label
  is routed through `/iflow-yolo`, with pick's confirmation folded together
  with yolo's consolidated confirm (one prompt total). `/iflow-init` stays
  untouched.
- Yolo's close step closes the loop via a `yolo` token on `/iflow-close`:
  changelog bullet written without a confirm prompt, PR merged with
  `gh pr merge --squash` (fallback `--squash --auto` when branch protection or
  pending checks block it; `draft` skips the merge), then default-branch
  switch + `git pull --ff-only`. Branch deletion stays in `/iflow-cleanup`.

#### Batch: all yolo-labelled issues (issue #175)

- `/iflow-cycle yolo` is the one-token alias for
  `label:<resolved yolo_label>` — process every open issue carrying the
  trigger label through the yolo chain under one confirm.
- No separate `/iflow-yolo-all` skill: cycle already owns queue confirm,
  `cycle_status.md`, onfail, and resume.
- **Merge conflicts:** sequential cycle merges each PR and returns to a clean
  default before the next issue (single-writer for `HISTORY.md` etc.).
  Experimental `parallel:<n>` still serializes merges (see
  [parallel-cycle.md](./parallel-cycle.md)).
- Optional prep: `/iflow-review yolo` to assign labels, then `/iflow-cycle yolo`.

#### Pick by arbitrary label (issue #228)

- `/iflow-pick label:<L>` is a **hard filter** on the interactive shortlist
  (GitHub list via `gh issue list --label`, plus parked/epic candidates that
  carry `<L>`). Free-form hints stay soft bias only when `label:` is absent.
- Still confirm before branching — never auto-pick a singleton shortlist.
- `/iflow-cycle label:<L>` is the batch twin (same GitHub label selection,
  hands-off yolo chain). No new CLI; pick stays skill-documented.

**Alternatives considered.**

- Always `gh pr merge --auto` — rejected: on repos without required checks the
  merge would silently rely on GitHub state; immediate `--squash` with `--auto`
  fallback is more deterministic.
- Runtime reading of `config.toml` by the agent — rejected: baking values at
  render time matches every other knob and keeps commands self-contained.
- New `/iflow-yolo-all` skill (#175) — rejected: duplicates cycle machinery;
  alias + docs on `/iflow-cycle` suffice.

**Link.** Issue #106, `issue106_plan.md` (archived with the issue group).
Issue #175 (batch alias).

### Ops / no-PR label (issue #251)

- `[issueflow].ops_label` (default `"ops"`) under the same `label_flows` gate.
- `/iflow-pick` routes to `/iflow-ops` → `/iflow-close ops` (no PR).
- When both `ops_label` and `yolo_label` are present on an issue, **ops wins**.
- See [ops-no-pr.md](./ops-no-pr.md).

### Publish on success (issue #308)

- `[issueflow].publish_label` (default `"publish"`) under the same
  `label_flows` gate.
- **Not** a pick router — close/cleanup concern only.
- Bare label → bump **patch** in the close PR (uv) or plan the tag
  (tag-derived); `publish:<level>` / `publish:<version>` override.
- Illogical explicit versions → stop and ask (even under yolo); CLI
  `issue-flow agent publish-intent` returns `logical` / `suggestion`.
- After merge: `gh release create "v<version>" --generate-notes` from yolo
  close step 9 or `/iflow-cleanup` Phase A.
- **ops wins** over publish (no PR → no release). Command-line bump tokens
  win over the label when both are present.

<a id="ops-no-pr"></a>

## Ops / no-PR close

**Issue:** [#251 — Support no-PR / ops work](https://github.com/jepegit/issue-flow/issues/251)
**Status:** decided with the issue plan (2026-09-11).

### Context

The normal lifecycle assumes code → branch → PR. Some real work should not open a
PR: promote staging→production, flip a feature flag, run an external deploy
checklist, or a tag-only step with no product diff. `lifecycle-and-commands.md#modes` had deferred a
“no-PR close variant”; this ships it as a token + skill, not a separate mode id.

### Decision

1. **Close token** `ops` (aliases `nopr` / `no-pr`) — dedicated **Ops close path**
   in `/iflow-close`: checklist confirm, refuse product-code dirty trees and
   unique product commits, skip HISTORY by default, skip push/PR, archive
   tracking, optional `.issueflows/` commit (default branch allowed with
   confirm), `gh issue close`. Mutually exclusive with `yolo` / `draft`.
2. **Config** `ops_label` (default `"ops"`), gated by existing `label_flows`,
   same bake pattern as `yolo_label`.
3. **`/iflow-ops`** off-path skill — entry for “do ops now”, then `close ops`.
4. **Pick routing** — `ops_label` → `/iflow-ops`; when both yolo and ops labels
   present, **ops wins**.
5. **HISTORY** — skip by default on ops; honour explicit `log "..."`.
6. **Defer** — `/iflow-review ops`, `/iflow-cycle ops`, body auto-detect.

### Alternatives considered

- Separate scaffolding **mode** that rewrites all close copy — rejected; mode
  mechanism stays surface selection; ops is a close variant.
- Auto-detect ops from issue text — rejected; too easy to skip review silently.
- Always require an issue branch for ops — rejected; default-branch tracking
  commits are fine when there is no product diff.

### Examples

- Promote staging → production via project deploy CLI / console.
- Flip a remote feature flag; record result in status.
- Run a one-off ops checklist documented in the GitHub issue body.

<a id="early-pr"></a>

## Early pull request

**Issue:** [#99 — Create pull request early](https://github.com/jepegit/issue-flow/issues/99)
**Status:** decided 2026-07-23.

### Context

PRs were opened only in `/iflow-close`. Sometimes teams want a draft PR
earlier (CI + review while build continues). Close must stay idempotent and
still own HISTORY.

### Decisions

1. **`[issueflow] early_pr = false`** by default — today's close-only create.
2. **Trailing overrides on `/iflow-build`:** `early` / `pr` force on;
   `noearly` force off. Precedence: trailing > baked config > default.
3. **When:** after the first successful push of an issue branch (or when a
   remote tip exists with no open PR). Always **draft**
   (`gh pr create --draft`) with `Refs #N`.
4. **Close:** list-before-create updates the existing PR; writes HISTORY in
   step 3 even if a draft already exists; marks ready (unless `draft` token)
   before yolo merge.
5. **Formalize close `draft`:** trailing `draft` → `--draft` on create; skips
   yolo merge.

### Alternatives considered

- Open at plan confirm / init — rejected (no commits yet).
- Ready (non-draft) early PR — rejected (noisier; draft is the safe default).
- New slash command — rejected (timing option, not a new lifecycle step).

### Link

Knobs table: [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).
Changelog ownership: [changelog-timing.md](./changelog-timing.md).
List/reuse contract: [gh-list-and-watch.md](./gh-list-and-watch.md).

<a id="linked-sub-issues"></a>

## Linked sub-issues (`/iflow-split`)

**Issue:** [#12 — Create linked (sub) issues for over-ambitious issues](https://github.com/jepegit/issue-flow/issues/12)
**Status:** decided 2026-08-13, implemented in the same issue.
**Closes:** Phase B of #63 (pick used to mention-only).

### Context

`/iflow-epic` already splits large work into staged issues + a markdown task
list on the anchor. `/iflow-issue` creates one well-specified issue.
`/iflow-pick` only *mentioned* that an over-large issue could be broken up.

GitHub now has native parent/child sub-issues. Agents need a confirm-gated
recipe: `sub_issue_id` is the REST **database id**, not the issue number, and
`gh api -f` stringifies and 422s.

### Decisions

#### 1. Name: `/iflow-split` (skill stem `iflow_split`)

New off-path surface. Rejected folding into `/iflow-issue` (that skill
creates *one* issue) and `/iflow-sub` (opaque).

#### 2. Split vs epic

- **Split** — 2–5 flat children, each one branch / one PR. Parent stays
  **open** as the tracker.
- **Epic** — sequential stages, `Depends on`, yolo-fitness, publish
  idempotency. If a proposed split needs that, stop and point at
  `/iflow-epic`.

#### 3. Offer-only from pick / issue / plan

Those surfaces mention `/iflow-split` or `/iflow-epic` and stop. They never
create children. `/iflow` never auto-dispatches split.

#### 4. Native sub-issue + task-list fallback

Create with `gh issue create`, then
`issue-flow agent sub-issue-add <parent> <child>` (JSON `--input`).
Append `- [ ] #<M>` under `## Sub-issues` on the parent. If the sub-issue
API fails, keep the created issue and rely on the task list.

#### 5. Local parent parks; children stay on GitHub

If `issue<N>_*` is the focus, move it to `02-partly-solved-issues/`.
Do not write child tracking groups at create time. Do not close the parent.

### Out of scope (v1)

- Retrofitting `/iflow-epic publish` to also call the sub-issues API.
- Auto-split without confirm; silent pick routing.
- GitLab; GraphQL `addSubIssue`.

### Link

Issue #12. Sibling: [create-non-epic-issue.md](./create-non-epic-issue.md).

<a id="novice-onboarding"></a>

## Onboarding novice and new users

Context: issue [#246](https://github.com/jepegit/issue-flow/issues/246) — a user
who has just been told to install issue-flow needs to get from "empty folder" or
"unprepared existing project" to a working workflow, without already knowing how
agentic coding works.

### The three-layer split

The work divides along one line: **the CLI reports, the agent acts.**

1. **`issue-flow agent setup-status`** (`readiness.py`) — read-only facts: tools
   on `PATH`, git repo / commits / remote, `gh` authentication, Python project,
   existing scaffold, a `new` / `existing` classification, and an ordered
   `blockers` list. Never prompts, never mutates, always exits 0 ("not ready" is
   an answer, not an error).
2. **`/iflow-setup`** — the conversation. Reads the payload, confirms the
   new-vs-existing guess with the user, and clears blockers one confirmation at
   a time.
3. **`novice` mode + settings preset** — what the project looks like afterwards.

Keeping (1) out of the skill matters because the skill has to work identically
across editors, and because the probe logic is the part worth testing.

### Decisions

**Named `/iflow-setup`, not `/iflow-init`.** #246's own text says the user types
`/iflow-init`, but that name is taken by issue capture. Issue
[#241](https://github.com/jepegit/issue-flow/issues/241) proposes renaming
capture to `/iflow-this` and freeing `/iflow-init` for exactly this cold-start
role. Rather than couple the two, #246 ships a new name; #241 can alias
`/iflow-init` onto `/iflow-setup` later without re-doing any of this work.

**The agent may run mutations, behind confirms — with three exceptions.** It
runs `uv init`, `uv sync`, `git init`, the first commit, `gh repo create`, and
`issue-flow init`. It never installs `uv` or `gh` (it cannot), never runs
`gh auth login` (an interactive browser flow that an agent must not drive), and
never runs `git init` inside an enclosing repository without the user deciding.
Those three are encoded as `agent_may_run: false` on the blocker, so the rule
lives in the data rather than only in skill prose.

**Novice is two axes, not one.** A smaller command list alone does not make the
flow easier to follow, and gentler settings alone still leave a beginner facing
twenty commands. So `[modes.novice]` selects the surfaces and `NOVICE_CONFIG`
seeds the knobs (`auto_plan` / `auto_build` / `auto_close` off, `label_flows`
off, `confirm_version_bump` / `confirm_changelog_update` on). The preset is only
written when there is no `config.toml` yet, so switching an established project
to `novice` never rewrites tuned settings.

**`--mode novice` implies `skill_level = "basic"`.** This deliberately couples
two otherwise-orthogonal axes; an explicit `--skill-level` still wins. The
alternative (leaving skill level alone) meant a "novice" scaffold could still
emit the advanced quality-tooling design doc.

### Repo detection: the bug worth remembering

`git rev-parse` answers for the *enclosing* work tree. A new folder created
inside any existing checkout — which is a very common way to start a project,
and is true of `$HOME` on at least one developer's machine — otherwise reads as
"already a repo, with commits, so this is an existing project". `readiness.probe`
therefore compares `git rev-parse --show-toplevel` against the target directory
and reports `enclosing_repo` separately, and never attributes the parent's
commits or remote to the child.

### Membership gating in the rendered rule

`novice` excluding surfaces exposed a pre-existing looseness: the scaffolded
rule body described `/iflow-yolo`, `/iflow-cycle`, `/iflow-epic` and friends
unconditionally, so a mode that omitted them still advertised them. Those
paragraphs are now gated on `included_skills`, which also fixes the same problem
for `simple`.

The scaffolded **workflow doc** deliberately keeps listing every surface — it
carries a mode banner explaining that entries outside the active mode are
reference-only — so it was left alone.

### Alternatives rejected

- **An interactive wizard in `issue-flow init`.** The CLI has to stay headless
  (CI, `--skip-dep-check`, `verify_scaffold.py`), and the editor chat is a
  better place for a conversation than a terminal prompt anyway.
- **Knobs-only novice preset** (no mode subset) — leaves the beginner staring at
  the full command surface.
- **Blocking `init` until the project is ready** — `init` is useful on a bare
  folder, and refusing to scaffold would strand the user before they have an
  agent that can help them.

<a id="modes"></a>

## Scaffolding modes

Context: issue #48 — let users pick which workflow surfaces `issue-flow init`
installs (e.g. a lightweight markdown-only workflow), and make it extensible so
developers can ship new modes and users can define custom ones.

### Decision

A **mode** is a named selection of workflow surfaces (skill stems from
`SKILL_DIRS`, command stems from `COMMAND_NAMES`). Modes are **data-driven**:

- Built-in modes ship as packaged data in
  [`src/issue_flow/modes.toml`](../../src/issue_flow/modes.toml) (`standard` =
  everything, back-compat default; `simple` = markdown-only lifecycle).
- A project may add or override modes in its own `.issueflows/config.toml` using
  the same `[modes.<id>]` grammar. Project tables win on id clash.
- `src/issue_flow/modes.py` mirrors the `editors.py` pattern: a frozen `Mode`
  dataclass + a resolver (`resolve_mode`) that expands the `all` sentinel and the
  `extends` / `add` / `remove` composition keys into concrete, validated stem
  sets. A mode may only reference stems that ship as packaged templates.

The **active** mode for a project is persisted to `.issueflows/config.toml`
`[issueflow].mode` (committed, so `update` honours it after a fresh checkout —
unlike `.env`, which is git-ignored). Resolution order: **`--mode` (CLI, applied
by `run_init` before the fallback resolver) > persisted `config.toml` >
`ISSUEFLOW_MODE` env > `DEFAULT_MODE` ("standard")**. The persisted choice
deliberately beats the environment so a stray `ISSUEFLOW_MODE` cannot silently
override the project's mode on `update` (honouring the issue contract: switching
modes is an `init --mode` action). `init --mode <id>` is the only way to change
it; `update` reads but never writes it.

### Two structural choices (and why)

These make the system ready for future surfaces/modes without per-mode `if`
ladders (the scenarios that motivated the design):

- **A. Templates gate on surface *membership*, not mode id.** The render context
  carries `included_skills` / `included_commands` (sorted stem lists). Templates
  branch with `{% if "iflow_close" in included_skills %}` etc. A new surface
  (e.g. a hypothetical `caveman` or a `grill_me` sub-skill used by `iflow-plan`)
  is gated by its own membership, so any current/future mode that includes it
  lights it up — no enumeration of mode names. For `standard` the set is "all",
  so output is unchanged.
- **B. Mode definitions are data, mergeable from project config.** This is what
  lets a user define a custom mode (`extends = "simple"`, `add = ["grill_me"]`)
  without editing package source, and keeps "what each mode contains" editable.

### Mechanics

- `build_manifest(profile, mode=None)` filters command/skill entries by the
  mode's stem sets. `mode=None` keeps the full set (back-compat for existing
  call sites / `TEMPLATE_MANIFEST`). Rules extra, the workflow doc, and the
  `AGENTS.md` block are emitted for every mode; their *content* adapts via
  membership gating.
- `init` / `update` resolve the active `Mode` once and thread it through
  `build_manifest` and `template_context`, then call
  `_prune_excluded_surfaces(...)` to delete previously-scaffolded skills/commands
  the active mode excludes (so a `standard -> simple` switch actually shrinks the
  surface and `update` stays idempotent). Only issue-flow's own generated
  surfaces are pruned; user files are untouched.
- Persistence round-trips via `tomlkit` so updating `[issueflow].mode` preserves
  user comments and `[modes.*]` tables.

### Scope / deferred

- `simple` is a *subset selection*; individual skills are not rewritten per mode.
  The `iflow` dispatcher's done-state is membership-gated (no `/iflow-close` route
  when close isn't installed; it points at moving files to `03-solved-issues/`
  instead), and the workflow doc prints a mode banner listing the installed
  surfaces. A no-PR close path ships as the `/iflow-ops` skill + `ops` close
  token (issue #251), not as a separate mode id.

### Rejected

- `.env`-only persistence (git-ignored → lost on checkout, `update` couldn't
  honor it).
- A hardcoded Python `MODES` dict only (would block user-defined custom modes,
  which scenario testing for #48 explicitly required).

<a id="step-model-directives"></a>

## Step model directives

**Context.** Issue #113: different iflow steps benefit from different model
trade-offs (speed vs reasoning depth).

**Decision.**

- Each lifecycle skill/command carries an advisory
  `### MODEL & EXECUTION DIRECTIVE` section baked at `issue-flow update`.
- Profiles: **`economy`** (speed/token savings) or **`reasoning`** (design depth).
  Packaged defaults live in `src/issue_flow/step_profiles.toml`; projects override
  per stem in `[issueflow.step_profiles]`.
- Config knobs under `[issueflow]` (persisted > env > default):
  `step_directives` (master toggle, default `true`), `model_label_flows`
  (default `false`), `deep_model_label` / `fast_model_label` (defaults
  `"deep"` / `"fast"`). `/iflow-pick` announces label-based session overrides
  only — no auto-dispatch.
- Cursor-specific hint when `editor == "cursor"`: Auto/fast vs thinking model.
  No SKILL.md `model:` frontmatter — Cursor does not support forcing a model
  from skills.

**Alternatives considered.**

- Runtime `config.toml` reads by agents — rejected; bake at render like other knobs.
- Per-issue model enforcement — rejected; advisory only.

**Link.** Issue #113.

<a id="skill-behaviour-knobs"></a>

## Skill-behaviour knobs

**Context.** Issue #182: templates + `config.toml` already bake toggles
(`caveman_default`, `label_flows`, `checks_watch_minutes`, …). More knobs
should tweak lifecycle *nudges* and close/yolo/cycle parameters without editing
templates by hand.

**Decision.** `[issueflow]` keys, same precedence as siblings
(`project config.toml` > user-global `config.toml` > `ISSUEFLOW_*` env >
default), baked at `issue-flow update`. User-global path and lock
semantics: [user-global-config.md](./user-global-config.md) (issue #281 /
epic #269). Until Stage 2 ships, only the project file and env exist.

**Naming conventions** (after consistency pass):

| Pattern | Keys |
|---------|------|
| Soft nudges (`verb_object`) | `remind_cleanup`, `suggest_graphify` |
| Named help mode | `noob` (issue #307; distinct from scaffolding `--mode novice`) |
| Cleanup defaults (`cleanup_*`) | `cleanup_include_github`, `cleanup_yes_a1`, `cleanup_yes_a2` |
| Tool upgrade (event-hook name) | `on_bleeding_edge` |
| Auto behaviours (`auto_*`) | `auto_switchback`, `auto_remove_worktree`, `auto_close`, `auto_cleanup`, `auto_plan`, `auto_build`, `auto_graphify_on_plan` |
| Unattended chain | `hands_off` (distinct from scaffolding `mode`; set with `issue-flow mode`) |
| Graphify checkout | `graphify_gitignored` |
| Start layout | `worktree_first` (issue #329; distinct from `auto_remove_worktree` and from worktree location #328) |
| Timing / PR | `early_pr` |
| Fix-session | `fix_auto_name` |
| Auto / advanced | `auto_adversarial_loops` (see [advanced-auto-mode.md](./advanced-auto-mode.md)) |
| Confirm gates (`confirm_*`) | `confirm_version_bump`, `confirm_changelog_update` |
| Changelog write timing | `defer_changelog` |
| Tool / value | `ruff_autofix`, `pr_merge_method`, `cycle_max_issues`, `cycle_onfail`, `cycle_nonyolo`, `test_runner`, `essential_marker`, `essential_review` |
| Feature masters (`*_tests` / paradigm) | `essential_tests` |
| Per-repo skip (`locked`) | `locked` (project `config.toml` only; `update --all` skips) |

| Key | Default | Effect |
|-----|---------|--------|
| `remind_cleanup` | `true` | Soft reminders to run `/iflow-cleanup` after close / cycle / iflow-D (never auto-run). `false` = no in-flow nudges; cleanup only via explicit `/iflow-cleanup` (issue #233) |
| `noob` | `false` | After each lifecycle step, print recommended next from `issue-flow agent state` (focus → `next_command`; no-focus epic gap → `epic_session` + `epic_hint`, not raw `next_command`) plus a short relevant `/iflow-*` list. Never auto-dispatch. Seeded `true` on first-time `--mode novice` only (issues #307, #337) |
| `cleanup_include_github` | `false` | When `true`, `/iflow-cleanup` runs Phase B (GitHub remote audit) by default; trailing `no github` / `local only` opts out (issue #233) |
| `cleanup_yes_a1` | `false` | When `true`, Phase A1 runs without a yes/no (the action list is still printed). Trailing `ask a1` forces the prompt. Does not authorize A2 (issue #388) |
| `cleanup_yes_a2` | `false` | When `true`, Phase A2 `git branch -D` runs without a yes/no (names and tip SHAs still printed). Trailing `ask a2` forces the prompt. `issue-flow update` warns while this is on. Never deletes `unique_work` (issue #388) |
| `on_bleeding_edge` | `false` | When `true`, `/iflow-cleanup` runs `issue-flow agent self-update` after a successful FF pull (`uv tool install issue-flow@latest` then `issue-flow update`). Trailing `bleeding edge` / `no bleeding` override. Skips editable installs (issue #382) |
| `suggest_graphify` | `true` | Soft GRAPH_REPORT / rebuild suggestions (never auto-run) |
| `auto_graphify_on_plan` | `false` | `/iflow-plan` runs `issue-flow graphify` (AST `update`) before prior-art; missing/fail → note + continue (issue #214) |
| `graphify_gitignored` | `false` | Gitignore all of `graphify-out/` on `init`/`update`. Also runs the plan and epic refresh even when `auto_graphify_on_plan` is false. Prints `git rm -r --cached graphify-out` when paths are still tracked; does not run it (issue #400) |
| `auto_switchback` | `true` | After PR, switch to default when clean (`false` ≈ always `stay`) |
| `auto_remove_worktree` | `true` | After `/iflow-close` opens or merges a PR, remove the sibling issue worktree when clean (`false` = YES/NO). Skip `stay` / draft / failed merge. Never deletes the branch (issue #273) |
| `worktree_first` | `true` | `/iflow-pick` / `/iflow-issue` / `/iflow-fix` start in a sibling worktree. `false` → `git switch -c` on home. Tokens `inplace` / `no worktree` / `worktree` override (issue #329) |
| `auto_close` | `false` | `/iflow-build` / `/iflow-fix` end chain into `/iflow-close` when ready |
| `auto_cleanup` | `false` | After a PR exists, watch until it merges (`checks_watch_minutes`) and then run `/iflow-cleanup`. Does not merge. Independent of `auto_close` (issue #388) |
| `auto_plan` | `true` | `/iflow-pick` chains into `/iflow-plan` after pick confirm + branch/init; trailing `noplan` skips once (issue #219) |
| `auto_build` | `true` | `/iflow-plan` chains into `/iflow-build` on plan Accept; trailing `nobuild` skips once (issue #219) |
| `hands_off` | `false` | Unattended chain skips its up-front confirm. Drive accepts a short description, AST graphify runs before each plan, and a spent auto budget records accept. `issue-flow mode hands-off` / `standard`. See [hands-off-mode.md](./hands-off-mode.md) |
| `early_pr` | `false` | `/iflow-build` opens a draft PR after the first push; trailing `early`/`pr` / `noearly` override per run |
| `fix_auto_name` | `false` | `/iflow-fix` invents session title/slug without a naming confirm; create issue+branch still confirms (issue #258). CLI: `issue-flow config show\|set\|edit` |
| `auto_adversarial_loops` | `2` | `/iflow-auto` inter-epoch adversarial loop budget; trailing `loops:<n>` overrides per run ([advanced-auto-mode.md](./advanced-auto-mode.md)) |
| `confirm_version_bump` | `false` | Non-yolo close confirms once about bump when unset |
| `confirm_changelog_update` | `false` | Changelog diff confirm before write; `false` = write without ask (bullet lands in the PR). Decline (when true) **stops** close — no silent skip. |
| `defer_changelog` | `false` | When `true`, issue branches never write `HISTORY.md` / CHANGELOG; the bullet is recorded on `issue<N>_status.md` + PR body and applied on the default branch after merge (`issue-flow agent apply-changelog`). Default off keeps today's #171 / #240 / #260 path. |
| `pr_merge_method` | `"squash"` | Yolo `gh pr merge --{squash\|merge\|rebase}` |
| `cycle_max_issues` | `10` | `/iflow-cycle` safety cap before `max:<n>` |
| `cycle_onfail` | `"stop"` | Default `/iflow-cycle` failure policy (`stop` \| `skip`); per-run `onfail:` token overrides (issue #248) |
| `cycle_nonyolo` | `"merge"` | Non-yolo lane merge policy for `yolo: no` issues in cycle / auto / drive (`merge` \| `pr-only` \| `stop`); per-run `nonyolo:` token overrides; env `ISSUEFLOW_CYCLE_NONYOLO` (issue #386) |
| `ruff_autofix` | `true` | Gate ruff `--fix` / format in start/close |
| `essential_tests` | `false` | Opt-in essential-suite paradigm (pytest); see [essential-tests.md](./essential-tests.md) (issue #213) |
| `test_runner` | `"pytest"` | Runner for essential-tests; v1 only `"pytest"` supported |
| `essential_marker` | `"essential"` | pytest mark name for the essential suite |
| `essential_review` | `"close"` | When to triage issue-touched tests: `close` \| `build` \| `both` \| `never` |
| `locked` | `false` | Per-repo skip for `issue-flow update --all`. Project `.issueflows/config.toml` only; user-global must not set it. Missing key = unlocked. Single-repo `update` still runs. Optional process override: `ISSUEFLOW_LOCKED`. See [user-global-config.md](./user-global-config.md) (issue #281) |

**Consistency.** `auto_plan` / `auto_build` / `auto_close` / `auto_cleanup` are **independent** —
each only skips its own next-step pause (pick confirm, plan Accept, and
build-ready still gate). Mode-gated on `iflow_plan` / `iflow_build` /
`iflow_close`. Do **not** imply yolo / auto-merge. One-shot skips: `noplan`,
`nobuild`. `auto_close` still honours `confirm_*`, `auto_switchback`,
`remind_cleanup`, `pr_merge_method`, etc.
`confirm_changelog_update = false` (default) matches yolo's no-prompt history
write so the bullet is always in the PR commit; `nohistory` still skips.
When confirm is on and declined, close **stops** (write / revise /
`nohistory` / abort) — never silent-skip and continue. Never offer a
HISTORY/CHANGELOG update after the PR is open or merged (see
[changelog-timing.md](./changelog-timing.md)).
`defer_changelog = true` moves only the **file write** to the default branch
after merge; the close-step *decision* (and the confirm gate) still runs.

**Continue to next step** (issue #388). Each knob only skips its own pause.
Cleanup cannot run until the PR is merged, so `auto_cleanup` watches and
does not merge.

| Step | Knob | Default |
| --- | --- | --- |
| Pick confirm | (always ask) | — |
| Capture | part of pick; no separate knob | — |
| Plan | `auto_plan` | `true` |
| Build | `auto_build` | `true` |
| Close | `auto_close` | `false` |
| Cleanup | `auto_cleanup` | `false` |

`cleanup_yes_a1` / `cleanup_yes_a2` are accept-knobs inside cleanup, not
continue-knobs. A1 does not authorize A2.

**Alternatives considered.**

- Runtime reads of `config.toml` by agents — rejected (matches
  [label-driven-flows.md](./label-driven-flows.md): bake at render time).
- Moving env-only path keys (`ISSUEFLOW_DIR`, …) into `config.toml` — out of
  scope; still environment-only.

**Link.** Issue #182.
