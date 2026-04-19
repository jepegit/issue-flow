# Plan for issue #45: include issue comments

## Goal

Make `/issue-init` comment-aware: fetch GitHub issue comments along with the body, and append a curated summary section to `issue<N>_original.md` that distills follow-up tasks, clarifications, and superseded points. Ship a companion skill (`issueflow-issue-comments`) that the init command and future work can lean on when interpreting comment threads.

## Constraints

- Preserve the existing `## Original issue text` contract: the body is kept byte-for-byte as GitHub returns it. Comments go in a new, separate section so diffs of the original body stay clean.
- Both deliverables must render cleanly through `issue_flow.templating.render_template` (defaults: `{{ issueflows_dir }}`, `{{ agent_dir }}`, etc.).
- `TEMPLATE_MANIFEST` in [src/issue_flow/templating.py](src/issue_flow/templating.py) must list the new skill, and `tests/test_templating.py` expectations must stay green.
- Keep changes cohesive with the existing tone/structure of [commands/issue-init.md.j2](src/issue_flow/templates/commands/issue-init.md.j2) and [skills/issueflow_issue_init/SKILL.md.j2](src/issue_flow/templates/skills/issueflow_issue_init/SKILL.md.j2).
- No design/guide doc needed under `.issueflows/04-designs-and-guides/` for this change (behavior is fully captured in the command + skill templates).

## Approach

1. **Fetch shape.** Switch the `gh` call in the `/issue-init` spec from `--json title,body,url,number` to `--json title,body,url,number,comments`. That returns each comment with `author.login`, `body`, and `createdAt`, which is enough for curation.

2. **File layout inside `issue<N>_original.md`.** Add one new optional section after the original body. The body section is unchanged (still byte-for-byte). If the issue has no comments, omit the new section entirely. Template:

   ```markdown
   # Issue #<number>: <title>

   Source: <url>

   ## Original issue text

   <body exactly as in GitHub issue>

   ## Comments (curated summary)

   - **Additional tasks**: <bullets distilled from comments that add real work>
   - **Clarifications / constraints**: <bullets the agent should honour>
   - **Superseded / retracted**: <earlier points later contradicted or walked back>

   _Note: this section is an interpretive summary, not a verbatim comment dump. Source comments: <count>, last comment by @<login> on <date>._
   ```

   - The curated summary is produced by the agent at init time using the new skill.
   - No verbatim paste of comments (per the issue: "does not have to be a 1-to-1 representation").

3. **Command edits** — [src/issue_flow/templates/commands/issue-init.md.j2](src/issue_flow/templates/commands/issue-init.md.j2):
   - Step 2: fetch `title, body, url, number, comments`.
   - New step 2a "Triage comments": call out the new skill `issueflow-issue-comments` as the playbook; list what counts as an additional task, a clarification, or a superseded point; explicitly allow collapsing/dropping noise.
   - Step 5: extend the file-content format with the optional `## Comments (curated summary)` section, and state the "omit if no comments" rule.
   - Constraints section: clarify that the body remains byte-for-byte; only the new section is interpretive.
   - Output section: include "N comments triaged" in the summary to the user.

4. **Init skill edits** — [src/issue_flow/templates/skills/issueflow_issue_init/SKILL.md.j2](src/issue_flow/templates/skills/issueflow_issue_init/SKILL.md.j2):
   - Mirror the fetch change and add a short "Triage comments" step right before the write step.
   - Point to the new `issueflow-issue-comments` skill for the triage rules.
   - Update the "Write" section to show the optional curated-comments block.

5. **New skill** — create `src/issue_flow/templates/skills/issueflow_issue_comments/SKILL.md.j2` with the standard frontmatter (`disable-model-invocation: true`, name `issueflow-issue-comments`) and sections:
   - **When to use** — invoked by `/issue-init` (and reusable by any workflow that needs to re-triage comments later).
   - **Inputs** — the JSON array of comments from `gh issue view --json comments` (author, body, createdAt).
   - **Triage rules** — chronological precedence (later wins conflicts); explicit negations move earlier items into Superseded; collapse duplicates; ignore chit-chat, LGTMs, bot messages; three buckets (additional tasks / clarifications / superseded); paraphrase, quote sparingly.
   - **Output contract** — the exact markdown block shown in step 2.
   - **Edge cases** — zero comments (skip section), only bot comments (skip section), heated/multi-author threads (note the disagreement rather than guessing a winner).

6. **Manifest + tests** — [src/issue_flow/templating.py](src/issue_flow/templating.py):
   - Add `("skills/issueflow_issue_comments/SKILL.md.j2", "{agent_dir}/skills/issueflow-issue-comments/SKILL.md")` to `TEMPLATE_MANIFEST`.
   - [tests/test_templating.py](tests/test_templating.py):
     - Bump `test_manifest_entry_count` from 20 to 21 and fix the inline comment.
     - Add `issueflow_issue_comments` to the list in `test_manifest_has_expected_commands_and_skills`.
     - Add `test_issue_init_fetches_and_triages_comments` asserting the rendered `issue-init` command mentions comments fetching, the curated-summary section header, and the new skill name.
     - Add `test_issue_comments_skill_documents_triage_rules` asserting the new skill renders, mentions chronological precedence and the three buckets.

## Files to touch

- [src/issue_flow/templates/commands/issue-init.md.j2](src/issue_flow/templates/commands/issue-init.md.j2) — fetch comments, add triage step, extend file-content format, update constraints + output.
- [src/issue_flow/templates/skills/issueflow_issue_init/SKILL.md.j2](src/issue_flow/templates/skills/issueflow_issue_init/SKILL.md.j2) — mirror the command changes; point at the new skill.
- `src/issue_flow/templates/skills/issueflow_issue_comments/SKILL.md.j2` (new) — full triage skill.
- [src/issue_flow/templating.py](src/issue_flow/templating.py) — register the new skill in `TEMPLATE_MANIFEST`.
- [tests/test_templating.py](tests/test_templating.py) — bump count, extend lists, add two focused tests.

## Test strategy

- `uv run pytest` (full suite).
- New assertions above.
- Manual smoke: render both templates via `render_template` and eyeball the output.

## Open questions

Resolved pre-implementation:

1. Skill name: `issueflow-issue-comments` (accepted).
2. No raw-comment appendix — keep it lean with only the curated summary.
3. No explicit edits to `/issue-yolo` or `/iflow`; they inherit the new behavior via `/issue-init`.
