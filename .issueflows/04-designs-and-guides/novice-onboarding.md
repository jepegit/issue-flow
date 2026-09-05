# Onboarding novice and new users

Context: issue [#246](https://github.com/jepegit/issue-flow/issues/246) — a user
who has just been told to install issue-flow needs to get from "empty folder" or
"unprepared existing project" to a working workflow, without already knowing how
agentic coding works.

## The three-layer split

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

## Decisions

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

## Repo detection: the bug worth remembering

`git rev-parse` answers for the *enclosing* work tree. A new folder created
inside any existing checkout — which is a very common way to start a project,
and is true of `$HOME` on at least one developer's machine — otherwise reads as
"already a repo, with commits, so this is an existing project". `readiness.probe`
therefore compares `git rev-parse --show-toplevel` against the target directory
and reports `enclosing_repo` separately, and never attributes the parent's
commits or remote to the child.

## Membership gating in the rendered rule

`novice` excluding surfaces exposed a pre-existing looseness: the scaffolded
rule body described `/iflow-yolo`, `/iflow-cycle`, `/iflow-epic` and friends
unconditionally, so a mode that omitted them still advertised them. Those
paragraphs are now gated on `included_skills`, which also fixes the same problem
for `simple`.

The scaffolded **workflow doc** deliberately keeps listing every surface — it
carries a mode banner explaining that entries outside the active mode are
reference-only — so it was left alone.

## Alternatives rejected

- **An interactive wizard in `issue-flow init`.** The CLI has to stay headless
  (CI, `--skip-dep-check`, `verify_scaffold.py`), and the editor chat is a
  better place for a conversation than a terminal prompt anyway.
- **Knobs-only novice preset** (no mode subset) — leaves the beginner staring at
  the full command surface.
- **Blocking `init` until the project is ready** — `init` is useful on a bare
  folder, and refusing to scaffold would strand the user before they have an
  agent that can help them.
