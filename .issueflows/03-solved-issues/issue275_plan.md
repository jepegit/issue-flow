# Issue #275 plan: Learn from skillbook

## Goal

Survey [kurochenko/skillbook](https://github.com/kurochenko/skillbook), pick
which ideas (if any) issue-flow should adopt, and file well-specified follow-up
GitHub issues. This issue does **not** implement those improvements.

## Constraints

- Templates remain the source of truth (`src/issue_flow/templates/`). Do not
  edit already-rendered `.cursor/skills/` copies as the change.
- Do not silently merge this with open #269 (system-wide settings / update-all /
  lock) or #268 (improve skills). Those overlaps go in Open questions.
- No new runtime dependency on the skillbook CLI unless we explicitly choose
  interop later.
- Follow-up work is created via `/iflow-issue` (flat) or `/iflow-epic` (staged);
  this issue does not implement children.
- Issue text requires grill-me for Task 2 — run it after the survey note exists,
  before `gh issue create`.

### Prior art

- [skill-authoring.md](../04-designs-and-guides/skill-authoring.md) — vendored
  writing-great-skills; house rules for shipped `SKILL.md.j2`.
- [pstack-skills.md](../04-designs-and-guides/pstack-skills.md) +
  `.issueflows/00-tools/vendor_pstack.py` — curated vendor, lock-to-upstream
  SHA, no network in `init`/`update`. Closest existing “external skill library”
  pattern; coexist, do not replace.
- [editor-profiles.md](../04-designs-and-guides/editor-profiles.md) —
  Claude / Codex / Cursor / OpenCode harness paths already mapped; Cursor
  skills-first (`.cursor/skills/<name>/SKILL.md`).
- [multi-editor-conversion.md](../04-designs-and-guides/multi-editor-conversion.md)
  — canonical `.issueflows/agent/skills/` vs generated editor trees. Skillbook
  uses `.skillbook/skills/` + harness symlink/copy instead.
- [modes.md](../04-designs-and-guides/modes.md) — which stems get installed.
- [create-non-epic-issue.md](../04-designs-and-guides/create-non-epic-issue.md)
  — `/iflow-issue` for Task 3.
- [grill-me-skill.md](../04-designs-and-guides/grill-me-skill.md) — Task 2.
- Open #269 — user-global config + update every local stack + per-repo lock.
  Skillbook’s `~/.skillbook` library + lockfile is the nearest external analogue.
- Open #268 — skill-writing quality; skillbook’s `lint` (Agent Skills spec) may
  feed that issue rather than a new one.
- Toolbox: `verify_scaffold.py` for render checks; `vendor_pstack.py` for
  upstream pin/drift. No skillbook helper exists (grep `skillbook` in `src/` =
  none). Graphify absent in this worktree (`graphify-out/graph.json` missing).

## Approach

Three sequential tasks, matching the issue. One PR: survey artifact + spawned
issues + status. No product-code change unless a grill decision is “tiny doc
cross-link only.”

### Task 1 — Survey

Read skillbook (clone or browse `master`): README, `src/constants.ts` / harness
map, lockfile shape, `lint`/`verify`/`sync`/`scan`, multi-file skill dirs,
`--json` agent contract.

Compare against issue-flow in a new durable note
`.issueflows/04-designs-and-guides/skillbook-lessons.md`:

| Skillbook idea | issue-flow today | Steal / skip / later |
| --- | --- | --- |
| Central library `~/.skillbook` + project copies | Packaged Jinja + `update` / `workspace update` | grill |
| Lockfile `version` + content hash | pstack SHA pin; no per-skill hash of rendered output | grill |
| `sync` / `push` / `pull` / `resolve` | `update` overwrites from templates; no user-edit round-trip | grill |
| Harness symlink vs copy | Always render/copy into editor dirs | grill |
| `lint` Agent Skills spec | writing-great-skills + house rules; no CLI linter | grill |
| `scan` discover existing skills | None | grill |
| Multi-file skill trees (scripts/refs) | Almost all single `SKILL.md` | grill |
| Extra harness (Pi) | No `EditorProfile` | likely skip or fold into #17-class work |
| Depend on skillbook CLI | None | default **skip** |

First-pass notes (planning skim, to be verified in build):

- Skillbook solves **user-owned personal/team skill libraries** across harnesses.
  issue-flow solves **product-shipped lifecycle skills** rendered from Jinja.
  Different jobs; coexistence is the default, not a merge.
- Cursor path in current skillbook README is `.cursor/skills/<name>/SKILL.md`
  (directory) — aligned with our post-#79 layout, not the older
  `.cursor/rules/<name>.md` snippet in some indexes.
- Strongest steal candidates: integrity/`verify` wording, Agent Skills `lint`,
  scan-unmanaged-skills, documenting coexistence so `update` does not clobber
  skillbook-managed files.
- Weak / dangerous: replacing `issue-flow update` with skillbook, or making
  lifecycle skills live only in `~/.skillbook` (breaks `init` determinism and
  tests).

### Task 2 — Grill-me pick

After the survey note exists, run grill-me (one question at a time) over the
table above plus:

- Coexist vs integrate vs ignore.
- #269: sibling, fold skillbook-library ideas into #269, or new issue.
- #268: give it `lint`, or keep separate.
- Whether any follow-up is yolo-sized.

Record accepted picks in the design doc and in `issue275_status.md`.

### Task 3 — Plans + GitHub issues

For each accepted pick, draft Spec + Acceptance via `/iflow-issue` (confirm
before create). If 3+ staged dependencies, offer `/iflow-issue epic` +
`/iflow-epic` instead of a pile of unrelated issues. Link each new number back
into `skillbook-lessons.md`.

This issue then closes with the design doc + issue links. Implementations stay
on those new issues.

## Files to touch

- `.issueflows/04-designs-and-guides/skillbook-lessons.md` — new survey +
  decisions + follow-up issue table.
- `.issueflows/01-current-issues/issue275_status.md` — progress + Done checkbox.
- GitHub: new issues only after confirm (`/iflow-issue`). No `src/` in this
  issue unless grill yields a one-line cross-link (e.g. README pointer).

## Test strategy

No new pytest in this issue (docs + GitHub only). `uv run pytest` still run at
close to prove we did not touch code. Follow-up issues own their tests
(`verify_scaffold.py` / unit tests as appropriate).

## Open questions

1. **Default stance:** treat skillbook as inspiration + coexistence doc, **not**
   a dependency. Confirm?
2. **#269 overlap:** keep #275 follow-ups separate from system-wide
   config/update-all/lock, and only *cite* #269 when a pick is “personal library
   of user skills”?
3. **This issue’s PR:** design doc + spawned issues is enough to close #275?
   (Recommended yes.)
4. **Epic vs flat:** wait until grill count is known, then choose
   `/iflow-issue` vs `/iflow-epic`?
