# Issue #118 plan: slash-less iflow invocation

Source: [issue118_original.md](./issue118_original.md) · GitHub: <https://github.com/jepegit/issue-flow/issues/118>

## Goal

Let users invoke **every** issue-flow lifecycle entry point in chat as **`iflow plan`** (space-separated, no `/` or `@`), while keeping `/iflow-plan` working for slash-menu users. Hyphen form `iflow-plan` remains a supported alias. Scope is the full lifecycle set (`iflow`, `iflow pick`, `iflow init`, `iflow plan`, `iflow start`, `iflow pause`, `iflow close`, `iflow cleanup`, `iflow yolo`, `iflow fix`, `iflow status`, `iflow archive`, `iflow graphify`) — not plan alone.

## Constraints

- **Cursor product limit:** Agent Skills with `disable-model-invocation: true` (all lifecycle skills per [skill-authoring.md](../04-designs-and-guides/skill-authoring.md)) only enter context via explicit invocation — today that means `/skill-name` in the slash menu or `@skill-name` attachment ([Cursor skills docs](https://cursor.com/help/customization/skills)). issue-flow **cannot** register a slash-menu alias without `/`. **`@` is not a viable workaround** for Norwegian keyboards (awkward key, same class of pain as `/`). The **primary** no-special-key path is **`iflow <step>` in chat** (letters + space only), backed by always-on rules that tell agents to treat it as explicit invocation.
- **Skill folder names unchanged.** Skills stay at `.cursor/skills/iflow-plan/SKILL.md` etc. (hyphenated folder/skill `name:`). Only **chat aliases** gain the space form; we do not rename shipped skill directories.
- **Do not flip lifecycle skills to model-invoked.** Removing `disable-model-invocation: true` or adding trigger-bait descriptions would violate #117 house rules and risk auto-loading heavy playbooks every turn.
- **Templates are source of truth.** Edit `src/issue_flow/templates/`; re-render with `issue-flow update`. Cursor is skills-first (`commands_dir=None` per [editor-profiles.md](../04-designs-and-guides/editor-profiles.md)); Claude/opencode still emit slash-command files — wording must stay profile-aware.
- **Behavior-preserving:** Off-path markers, confirmations, and dispatch semantics stay unchanged; this issue only broadens *how users trigger* existing skills.
- **Small, doc+rules focused PR** — no new CLI subcommands unless we later find agents ignore the rule.

### Prior art

- `src/issue_flow/editors.py` — Cursor `commands_dir=None`; Codex already documents skill-name invocation without slash commands.
- `src/issue_flow/templates/rules/_body.md.j2` — always-on rules merged into `.cursor/rules/issueflow-rules.mdc` and `AGENTS.md`; right place for agent-side alias recognition.
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — lifecycle table + “Agent Skills” section; already shows `/iflow-plan` everywhere.
- `src/issue_flow/templating.py` — `COMMAND_NAMES` lists canonical hyphenated stems (`iflow-plan`, …); alias table in rules should be derived from the same list (step token = part after `iflow-`).
- `src/issue_flow/templates/skills/*/SKILL.md.j2` — titles use `` (`/iflow-plan`) `` form; 18 lifecycle/behavior skills.
- `.issueflows/04-designs-and-guides/skill-authoring.md` — user-invoked skills: one-line descriptions, no trigger lists; invocation note lives in skill **body** or shared rules, not `description` frontmatter.
- `.issueflows/00-tools/verify_scaffold.py` — end-to-end scaffold assertions after template edits.
- `tests/test_templating.py` — locks rendered command/skill/doc markers; extend for slash-less rule text.
- graphify-out absent — skipped.

## Approach

### 1. Always-on alias rule (primary fix)

Add a **“Chat invocation (no slash)”** section to `templates/rules/_body.md.j2` (flows into `AGENTS.md` + `.cursor/rules/issueflow-rules.mdc`):

**Recognized forms** (case-insensitive; message is exactly the form, or starts with it followed by a space and trailing args):

| User types | Maps to skill |
|------------|----------------|
| `iflow` | `iflow` (dispatcher) |
| `iflow plan` | `iflow-plan` |
| `iflow pick` | `iflow-pick` |
| … | … (every `COMMAND_NAMES` entry: `init`, `start`, `pause`, `close`, `cleanup`, `yolo`, `fix`, `status`, `archive`, `graphify`) |
| `iflow-plan` | `iflow-plan` (hyphen alias) |
| `/iflow-plan` | `iflow-plan` (slash form, unchanged) |
| `/iflow plan` | `iflow-plan` (slash + space alias) |

**Matching rules for agents:**

- **Primary chat form:** `iflow <step>` where `<step>` is one of the known step tokens (`plan`, `pick`, `init`, …). This is what docs recommend.
- **Aliases:** same with hyphen (`iflow-plan`) or leading slash (`/iflow-plan`, `/iflow plan`).
- On match: read and follow the corresponding skill immediately — same obligation as slash-menu invocation. Forward any trailing text verbatim (e.g. `iflow pick fix` → `iflow-pick` with arg `fix`).
- **Do not** treat incidental prose as invocation (e.g. “help me iflow plan this refactor” is not a command unless the message **starts with** `iflow plan` as a token boundary).
- State that this rule exists for layouts where `/` and `@` are awkward (Norwegian keyboard called out in docs).
- Mention `@iflow-plan` only in passing — not promoted.

Skill folder / `name:` in frontmatter stay hyphenated; only user-facing chat aliases use spaces.

### 2. Documentation pass

Update `templates/docs/issue-workflow.md.j2`:

- **Callout near the top:** “Type **`iflow plan`** in chat” as the recommended entry (letters + space; no `/`, `@`, or `-` required). Slash menu: `/iflow-plan`. Hyphen chat alias `iflow-plan` noted briefly.
- **Agent Skills table — Invoke column:** lead with `iflow plan`, then `iflow-plan`, then `/iflow-plan`.
- **Command lifecycle section** in rules/docs: where examples today say `/iflow-plan`, add parallel “or type `iflow plan` in chat” at least once in the intro — avoid rewriting every bullet (noise).
- Keyboard note: Norwegian layout — `/` and `@` both awkward; space form is intentional.

Optional one-line README tweak.

### 3. Skill body hint (shared include)

Add `templates/skills/_invocation_forms.md.j2` with a per-skill `step` variable (e.g. `plan`):

```markdown
**Invoke:** type `iflow plan` in chat, or `/iflow-plan` from the slash menu (`iflow-plan` also works).
```

Included near the top of each **user-invoked lifecycle** skill template (`iflow_*` except `caveman`, `grill-me`, `iflow_comments`, `iflow_version_bump`, `iflow_history_update`). Dispatcher `iflow` template uses: “type `iflow` in chat, or `/iflow` from the slash menu.”

### 4. Re-render + verify

- `issue-flow update` on this repo.
- `uv run .issueflows/00-tools/verify_scaffold.py`
- `uv run pytest` + `uv run ruff check src/ tests/`

### 5. Design doc

Add `.issueflows/04-designs-and-guides/slash-less-invocation.md` — space form primary, hyphen/slash aliases, Cursor limitation, `@` not promoted, link to #118.

## Files to touch

| Path | Change |
|------|--------|
| `src/issue_flow/templates/rules/_body.md.j2` | Chat invocation section + alias table |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Docs: `iflow plan` primary, keyboard note |
| `src/issue_flow/templates/skills/_invocation_forms.md.j2` | **New** shared include (`step` param) |
| `src/issue_flow/templates/skills/iflow_*/SKILL.md.j2` | Include invocation line (lifecycle skills) |
| `tests/test_templating.py` | Assert `iflow plan` in rules/docs/skill render |
| `README.md` | Optional quick-start wording |
| `.issueflows/04-designs-and-guides/slash-less-invocation.md` | Durable design note |

No Python module changes expected unless we later DRY the alias table from `COMMAND_NAMES` in templating (optional follow-up).

## Test strategy

```bash
uv run ruff check src/ tests/
uv run pytest
uv run .issueflows/00-tools/verify_scaffold.py
```

New/updated assertions:

- Rendered rules/`AGENTS.md` block contains `iflow plan` and explicit “chat invocation” instruction.
- Rendered `iflow-plan` skill body recommends `iflow plan` first.
- `issue-workflow.md` callout mentions space form before slash form.

## Resolved / open questions

1. **Space vs hyphen in chat:** **Resolved** — `iflow plan` is primary; `iflow-plan` is alias. Skill dirs stay hyphenated.
2. **Slash menu:** Still `/iflow-plan` only (Cursor product). Chat `iflow plan` is the keyboard-friendly path.
3. **Config opt-out:** No for v1.
4. **Helper skills:** Lifecycle + dispatcher only; helpers unchanged.
