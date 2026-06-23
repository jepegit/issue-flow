# Issue #71: Rename issue-* slash commands to a shorter, more consistent scheme

Source: https://github.com/jepegit/issue-flow/issues/71

Milestone: v.0.5.0

## Original issue text

## Motivation

The slash-command family has grown to 11 commands, all using the `issue-`
prefix except the dispatcher `iflow`, which is an inconsistent one-off. The
names are a bit long and the dispatcher doesn't visually belong to the family.
This issue proposes renaming the `issue-*` commands to a shorter, more
consistent scheme and making the dispatcher the namespace root.

## Goal

Pick a single naming scheme for all workflow slash commands (and their mirrored
skills) that is (a) consistent — including the dispatcher — and (b) ideally
shorter, while preserving autocomplete grouping and avoiding collisions with
generic words / other tools' commands.

## Options considered

| Scheme | Example | Shorter? | Notes |
|---|---|---|---|
| **A. Bare verbs** | `/init`, `/plan`, `/close` | Yes (most) | Shortest, but very generic — collision-prone and ambiguous in chat history; loses the `/issue…` autocomplete cluster. |
| **B. Short prefix `if-`/`is-`** | `/if`, `/if-init`, `/if-plan` | Yes | Real length savings, keeps grouping under `/if`, makes the dispatcher the root. `if` reads a little like the keyword. |
| **C. `iflow-` family (recommended)** | `/iflow`, `/iflow-init`, `/iflow-plan` | No (same length as `issue-`) | Not shorter, but consistent and on-brand: the dispatcher `/iflow` becomes the namespace root and every step reads as a child of it. |
| **D. Keep prefix, shorten verbs** | `issue-init`→`issue-new` | Marginal | The prefix is most of the length; skip. |

**Note on length:** `iflow-` and `issue-` are both 6-char prefixes, so option C
is *not* shorter — its win is structural consistency and branding, not brevity.
If brevity is the priority, option B (`if-`) is the better pick.

## Recommendation: option C (`iflow-`)

Make `/iflow` the namespace root and rename the `issue-*` commands to `iflow-*`.
Typing `/iflow` then autocompletes the dispatcher and the whole family, and the
naming ties cleanly to the project (issue-flow → iflow).

### Proposed command mapping

| Current | Proposed |
|---|---|
| `iflow` (dispatcher) | `iflow` (unchanged — now the family root) |
| `issue-pick` | `iflow-pick` |
| `issue-init` | `iflow-init` |
| `issue-plan` | `iflow-plan` |
| `issue-start` | `iflow-start` |
| `issue-pause` | `iflow-pause` |
| `issue-close` | `iflow-close` |
| `issue-cleanup` | `iflow-cleanup` |
| `issue-yolo` | `iflow-yolo` |
| `issue-fix` | `iflow-fix` |
| `graphify` | `graphify` (open question — see below) |

### Skill naming

Skills currently use a separate `issueflow-issue-*` prefix. To avoid the
redundant `issueflow-iflow-*`, collapse the skill family to `iflow-*` too:

- `issueflow-issue-init` → `iflow-init`, `issueflow-issue-plan` → `iflow-plan`, … (mirrors each command)
- `issueflow-issue-comments` → `iflow-comments`
- `issueflow-version-bump` → `iflow-version-bump`
- `issueflow-history-update` → `iflow-history-update`
- `issueflow-graphify` → `iflow-graphify` (track with the `graphify` command decision)

Keep command and skill names aligned so `/iflow-init` ↔ `iflow-init` skill.

## Blast radius (files to touch)

- `src/issue_flow/templating.py` — `COMMAND_NAMES` and `SKILL_DIRS` lists (and the `issueflow_*` skill dir → output-name mapping).
- `src/issue_flow/templates/commands/*.md.j2` — rename the template files and update every internal cross-reference (e.g. `iflow.md.j2` enumerates each `/issue-*`; `issue-yolo`, `issue-pick`, `issue-fix`, `issue-close` reference siblings).
- `src/issue_flow/templates/skills/*/SKILL.md.j2` — rename folders, update frontmatter `name:` and cross-references.
- `src/issue_flow/templates/rules/_body.md.j2` — the "Command lifecycle" section.
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — command/skill tables and per-command sections.
- `README.md` — tree listing, skills list, prose.
- `tests/test_templating.py` — the hardcoded expected command/skill name lists (manifest counts are unchanged: still a rename, not an addition).

## Backward compatibility / migration

- `issue-flow update` overwrites manifest paths but does **not** delete files, so existing installs would keep the old `.cursor/commands/issue-*.md` (and skill folders) alongside the new `iflow-*` ones. Decide how to handle:
  1. **Document only** — tell users to delete the old `issue-*` files manually.
  2. **Prune on update** — have `init`/`update` remove the known old names when writing the new ones (cleanest UX; needs a small "retired names" list).
  3. **Alias shims** — ship thin `issue-*` files that point at the new ones for one release, then remove.
- This is a user-facing breaking change to the command surface → warrants at least a **minor** version bump and a clear `HISTORY.md` entry.

## Open questions

1. Confirm option C (`iflow-`) vs. option B (`if-`, if brevity matters more).
2. Does `graphify` join the family as `iflow-graphify`, or stay `graphify` since it wraps an external tool? (The `issue-flow graphify` CLI subcommand is unaffected either way.)
3. Migration strategy (document / prune / alias) — preference?

## Out of scope

- No change to the `issue-flow` CLI subcommands (`init`, `update`, `graphify`).
- No change to the `.issueflows/` folder structure or status-file conventions.
