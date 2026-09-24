# Documentation usability review

Review of the published docs at <https://issue-flow.readthedocs.io/en/latest/>
(source: `docs/`, nav in `zensical.toml`), written 2026-09-24. Goal: make the
docs easier to use for a first-time reader without losing the depth that
power users and agents rely on.

Findings are ordered by priority. Each has **problem → change → where**.

---

## Priority 0 — broken links (fix first, cheap)

### 1. Read the Docs links without `/en/latest/` return 404

`https://issue-flow.readthedocs.io/how-to/for-agents/` → **404**;
`https://issue-flow.readthedocs.io/en/latest/how-to/for-agents/` → 200.
Links without the version prefix are broken in:

| File | Count |
| --- | --- |
| `docs/llms.txt` | 6 (every link — the whole "agent map" is dead) |
| `README.md` | 1 |
| `docs/issue-workflow.md` | 1 |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | 1 |
| `src/issue_flow/templates/commands/iflow-init.md.j2` | 2 |
| `src/issue_flow/templates/skills/iflow_init/SKILL.md.j2` | 3 |

**Change:** either add `/en/latest/` to every link, or (better, one place)
enable a Read the Docs "exact redirect" / set the default version so bare
paths resolve, and set `site_url = "https://issue-flow.readthedocs.io/en/latest/"`
in `zensical.toml`. Templates matter most: they ship broken links into every
scaffolded project.

### 2. Links into `.issueflows/` from the published site

`docs/configuration.md` links to `../.issueflows/04-designs-and-guides/*.md`
(e.g. `user-global-config.md`, `global-vs-local-skills.md`). Those files are
outside `docs/`, so they 404 on the site. Several other pages mention
`.issueflows/04-designs-and-guides/…` as plain text (18 hits in `docs/`).

**Change:** link to the GitHub blob URL
(`https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/<file>.md`),
or drop the link and summarize the decision inline. Plain-text mentions that
mean "in *your* scaffolded project" should say so explicitly.

**Guard:** add a link check to CI (e.g. `lychee` on the built `site/`) so this
does not regress.

---

## Priority 1 — structure and entry points

### 3. The home page tries to be four pages

`docs/index.md` contains: tagline, a vague "Why" section, a Cursor-only file
tree, installation, a quick start, a list of 13 off-path commands in one
sentence, recipes, and a "where to go next" list. It overlaps heavily with
`getting-started.md` and `README.md`, and the two quick starts disagree
(home starts with `/iflow-capture 42`; Getting started starts with
`iflow pick`).

**Change:** slim the home page to:

1. One-paragraph pitch (what problem it solves, for whom). Replace the "Why —
   I guess it is just a matter of taste…" section with a concrete benefit
   statement (agents plan before coding; every change has an issue, plan, and
   PR; state survives across sessions).
2. A lifecycle diagram (see §9).
3. Three doors, as cards or a short table:
   - **New to issue-flow** → Getting started
   - **Already set up, want to do X** → How-to guides
   - **You are an AI agent** → llms.txt / for-agents page
4. Install one-liner and a link to Getting started for the rest.

Move the file tree to a "Concepts" page (§5) and the recipes to the How-to
index. Use one canonical quick start: `iflow pick → plan → build → close →
cleanup`, same as Getting started.

### 4. Navigation order does not follow the reader's journey

Current nav: Home · Getting started · How-to (13 flat items) · The workflow ·
CLI reference · Configuration · Editor support · Graphify · Developing ·
Changelog · Acknowledgements.

**Change:** regroup into the Diátaxis split the site already half-follows:

```text
Home
Getting started
  Install and first issue          (current getting-started.md)
  Choose a mode                    (moved up from How-to)
  Editor support                   (moved up; readers need it on day 1)
Concepts                           (new, see §5)
How-to guides
  Everyday: one issue · park/resume · after a squash merge · worktrees
  Faster: yolo · cycle · fix session (new)
  Bigger changes: write an issue (new) · split (new) · epics · auto · drive (new)
  Team and repos: folder of repos · refresh dirty PRs · ops/no-PR (new)
  Troubleshooting (new, see §8)
Reference
  Commands (was "The workflow")
  CLI
  Configuration
  Graphify
For agents                         (for-agents.md + llms.txt)
Project
  Developing · Changelog · Acknowledgements
```

Use `zensical.toml` nav sections; `navigation.indexes` is already enabled so
each section can have an index page. Consider `navigation.tabs` for the
top-level groups so the sidebar is shorter.

### 5. No concepts / glossary page

Readers meet many undefined terms: *focus issue*, *on-path / off-path*,
*dispatcher*, *parked*, *sweep*, *yolo*, *epic*, *stage*, *epoch*,
*adversarial review*, *squash-landed branch*, *mode* vs *skill level* vs
*noob*, *managed block*, *harness*, *worktree-first*. Definitions exist but
are scattered inside long reference paragraphs.

**Change:** add `docs/concepts.md` covering:

- The lifecycle (capture → plan → build → close → cleanup) and what file each
  step writes.
- The `.issueflows/` folder layout and how an issue group moves
  `01-current` → `02-partly-solved` / `03-solved` (with a diagram).
- On-path vs off-path commands: why `/iflow` never runs some of them.
- Where confirmations happen (what the agent will *never* do without asking).
- A glossary table. Enable `abbr` + `content.tooltips` (already on) with a
  snippet-included glossary so terms get hover definitions site-wide.

---

## Priority 2 — the big reference pages

### 6. "The workflow" page (`issue-workflow.md`, ~650 lines)

Problems:

- Title is **"Cursor issue workflow (Agent Skills)"** because the page is the
  Cursor render of `templates/docs/issue-workflow.md.j2`. Claude Code,
  opencode, and Codex users get the wrong framing and paths (`.cursor/skills/`).
- Section numbering is hard to follow: `0a, 0, 1, 1a, 2 … 8, 8b, 9, 10, 10a,
  11 … 17`. Numbers suggest order, but most commands are off-path.
- Two near-identical tables (entry points, then Agent Skills) list the same
  25 commands before any explanation.
- A single 400-word paragraph on multi-root workspaces sits in the intro.
- History-flavoured wording: "no planning step of its own any more",
  "A new `/iflow-graphify` entry point", issue numbers in parentheses.

**Change:**

- Keep the scaffolded file as is for projects, but for the site render an
  editor-neutral version (or add a Zensical tab set: Cursor / Claude Code /
  opencode / Codex, using `pymdownx.tabbed`, already enabled). Title it
  "Command reference".
- Drop numbering; group commands under headings: **Core loop**,
  **Starting work**, **Helpers**, **Automation**, **Maintenance**.
- One table only, with columns *Command · What it does · On/off path ·
  Modes that include it*. Link each row to its section.
- Give every command section the same fixed shape: *When to use · Arguments ·
  What it does · What it asks you · Result · Related how-to*. Most sections
  already have When/What/Result — make it consistent and add the missing
  "what it asks you" line.
- Move the workspace paragraph to the workspaces how-to (it already exists).
- Remove change-log language; the changelog covers history.

### 7. Configuration page (`configuration.md`, ~440 lines)

Problems:

- Opens with the four-layer precedence model, user-global paths per OS, WSL
  caveats, and registry details — before the reader knows which knob they
  want.
- `config add` paragraph lists ~35 keys inline in one sentence.
- Internal references (`issues #281 / #285, epic #269`, `#282 / #293`).

**Change:**

- Start with "Common changes" — a short table of the 5–8 knobs people
  actually touch (`mode`, `auto_plan`, `worktree_first`, `caveman_default`,
  `grill_me_default`, `label_flows`, `pr_merge_method`, `noob`) with a
  one-line `issue-flow config set …` example each, plus the reminder to run
  `issue-flow update` afterwards.
- Then a full knob reference **table** (key · type · default · effect ·
  modes · env var), generated from code if possible so it cannot drift.
- Move precedence / user-global / registry to a "How settings are resolved"
  section near the end.
- Replace issue numbers with plain explanations (or put them in footnotes).

### 8. No troubleshooting / FAQ

Common first-hour failures are not collected anywhere: `gh` not
authenticated, `issue-flow` not on PATH after `uv tool install`, skills not
appearing in the slash menu (editor restart, wrong `--editor`), stale skills
(`issue-flow-version` stamp mismatch → `issue-flow update`), local branch
"several commits ahead" after a squash merge, dirty `01-current-issues/`
(→ `iflow doctor`), WSL vs native Windows config paths.

**Change:** add `docs/how-to/troubleshooting.md` with symptom → cause → fix
entries, and link it from Getting started and the home page.

---

## Priority 3 — coverage and polish

### 9. Add diagrams

The workflow is inherently visual but the site has no diagrams.

- Lifecycle state machine (what `/iflow` dispatches to from which state).
- Folder moves between `01` / `02` / `03`.
- Epic → stages → issues → cycle/auto.

Mermaid needs a `pymdownx.superfences` custom fence in `zensical.toml`
(check Zensical's Mermaid support); otherwise commit SVGs under
`docs/static/images/`.

### 10. How-to gaps

Commands with no how-to page: `/iflow-fix`, `/iflow-issue`, `/iflow-split`,
`/iflow-ops`, `/iflow-drive`, `/iflow-status`, `/iflow-doctor`,
`/iflow-archive`. Add short goal → steps → related pages for at least
`fix`, `issue`, `split`, `ops`, and `drive`. The How-to index (§4) should
group them by situation rather than list 13+ rows flat.

### 11. Show what a session looks like

Getting started and the core how-to describe steps but never show the
output. Add one annotated transcript (or screenshots) of `iflow pick` →
`iflow plan` → Accept → `iflow build` → `iflow close`, including an example
`issue<N>_plan.md`. This is the single most effective way to explain what
"stops for your confirmation" means.

### 12. Editor neutrality on shared pages

The home page file tree, "What it does", and examples default to Cursor
(`.cursor/skills/`, `issueflow-rules.mdc`). Use tabbed blocks per editor
where paths differ, and state the chat form (`iflow plan`) as the primary
invocation everywhere, since it works in all editors.

### 13. Smaller wording fixes

- `cli.md` intro: "The raw `--help`-style dump is folded at the bottom of
  this page intro" is unclear — it is actually folded *above* the command
  sections. Reword to "A full synopsis is in the collapsible block below."
- `cli.md`: mark the `agent …` helpers as "called by skills; you rarely run
  these by hand" so humans can skip that section.
- `getting-started.md`: "Two of the four steps below happen in a terminal" —
  fine, but add expected time and prerequisites (editor with agent, GitHub
  account) up front.
- Choose one term per concept: the pages mix *command*, *skill*, *slash
  command*, *entry point* for the same thing. Pick "command" in prose and
  explain once (in Concepts) that on some editors commands are delivered as
  skills.

---

## Suggested rollout

Split into issues so each fits one PR (candidate for `/iflow-epic`):

| Stage | Issue | Size | yolo-fit |
| --- | --- | --- | --- |
| 1 | Fix RTD links (§1) + `.issueflows` links (§2) + CI link check | S | yes |
| 1 | Wording fixes (§13) | S | yes |
| 2 | Nav regroup in `zensical.toml` + How-to index grouping (§4) | S | yes |
| 2 | New Concepts + glossary page (§5) | M | no |
| 2 | Slim home page (§3) | M | no |
| 3 | Restructure command reference, editor-neutral site render (§6) | L | no |
| 3 | Configuration page reorder + knob table (§7) | M | no |
| 4 | Troubleshooting page (§8) | M | no |
| 4 | Diagrams (§9) | M | no |
| 4 | Missing how-tos (§10) + sample transcript (§11) | M | no |

Remember: pages that are rendered from templates (`issue-workflow.md`) must
be changed in `src/issue_flow/templates/`, not in `docs/` directly.
