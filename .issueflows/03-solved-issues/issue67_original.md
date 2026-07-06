# Issue #67: Multi-repo Cursor workspaces: issue-flow assumes a single project root

Source: https://github.com/jepegit/issue-flow/issues/67

## Original issue text

## Problem

issue-flow assumes **one repo == one project root**: a single `.issueflows/`, one `AGENTS.md`/rules file, and slash commands that operate on "the current directory". That breaks down when a single editor workspace contains **two (or more) sibling repositories** that are developed together.

Concrete setup that surfaced this: a Cursor workspace with two scaffolded repos open at once —
- `cellpy-core` (the engine library)
- `cellpy` (the consumer that depends on it)

Both have their own `.issueflows/`, `AGENTS.md`, and `.cursor/` scaffold. Working an issue that touches both repos (an engine migration on one side, the integration/verification on the other) was noticeably more awkward than the single-repo flow.

## Specific friction points

1. **Ambiguous target repo.** `/iflow`, `/issue-init`, `/issue-close`, `/issue-cleanup` all key off the current working directory. With two roots the agent has to *guess* which repo a command targets. We had to disambiguate by invoking the command from a specific folder (e.g. `/cellpy-core/issue-init 13`), but the command *body* still assumes single-root semantics.

2. **`gh` resolves the repo from cwd.** `/issue-init` (fetch), `/issue-close` (open PR), and `/issue-cleanup` (check merge status) all let `gh` infer the repo from cwd. From the wrong cwd they silently target the wrong repository — easy to fetch/PR against the wrong repo in a multi-root workspace.

3. **Always-on rules collide.** Both repos' always-applied rules (`AGENTS.md` + `issueflow-rules.mdc` + a `this-project.mdc`) are injected into the agent context simultaneously. They duplicate and sometimes *conflict* — e.g. cellpy says "use conda `cellpy_dev_313` for pytest" while cellpy-core says "use `.venv`/`uv`". The agent can't tell which environment applies to which repo from the merged rule soup.

4. **Cross-repo issues have no first-class support.** The migration was inherently paired (core change + consumer bump/verify). issue-flow has no notion of a linked issue across repos; we hand-created paired GitHub issues, cross-referenced them in the bodies, and manually made a shared label + milestone in *each* repo.

5. **Per-repo cleanup/branch hygiene.** `/issue-cleanup` and branch hygiene are single-root; in a multi-root workspace you must remember to run them once per repo, in the right cwd, against the right default branch.

## Suggested improvements (options, not all required)

- **Make every command resolve an explicit project root + repo slug** rather than trusting cwd: derive the target from the active file / branch, or accept `--repo <name>`; always `git -C <root>` and pass `gh --repo <owner/name>` explicitly. This alone fixes 1, 2 and 5.
- **A workspace/multi-root mode**: `issue-flow init --workspace` (or a top-level `.issueflows/workspace.toml`) that registers the set of project roots so commands know the repo set and can prompt "which repo?" when ambiguous. `/issue-pick` could then rank across all registered repos.
- **Scope the always-on rules to their repo.** Attach `issueflow-rules.mdc` / `this-project.mdc` via path globs so each repo's rules only apply to files under that repo, avoiding the merged-rules conflict (point 3). Or namespace them by repo.
- **Cross-repo linked issues** (extends #12 to *across* repos): a `links:` field in the issue status front-matter, `/issue-init` mirroring cross-references, and a helper to create paired issues + a shared label/milestone in each repo automatically.
- **Multi-repo `issue-flow status`** (relates to #20): a dashboard spanning all roots in the workspace.

## Environment

- Editor: Cursor, single workspace, two scaffolded repos (`cellpy-core`, `cellpy`).
- issue-flow scaffold present in both repos.

Happy to help test or draft a doc/section on "recommended multi-repo workspace layout" if useful.

## Comments (curated summary)

- **Clarifications / constraints**: `/iflow-pick <n> repo:<repo-name>` reportedly picked the correct repo in a 3-repo workspace — may be LLM-dependent, not guaranteed deterministic behavior.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-06._
