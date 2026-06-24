# Issue #53: Add a project-summary doc (this-project.md) generated/maintained by issue-flow

Source: https://github.com/jepegit/issue-flow/issues/53

## Original issue text

## Background

Right now `issue-flow init` / `issue-flow update` scaffolds commands, skills, rules, and the `.issueflows/` folder structure, but it doesn't produce any per-project description file. Each project's "what is this repo about" context ends up living in `README.md`, AGENTS/Cursor rules, or in the head of whoever has been working on it.

It would be useful to have a small, durable, project-specific brief that:

- LLMs/agents (Cursor, the issueflow skills) can read early to get oriented.
- Humans can update by hand without it being clobbered.
- Lives alongside the other issue-flow artifacts.

Working title: `this-project.md`.

## Sketch of the design

### Location

Place it under `.issueflows/04-designs-and-guides/this-project.md` (or at repo root — open question, see below).

`04-designs-and-guides/` is already the project's durable memory and is explicitly **not overwritten** by `issue-flow update`, which matches the desired semantics.

### Contents (suggested skeleton)

A short markdown file with a few canonical sections:

- **What this project is** — one-paragraph elevator pitch.
- **Stack / runtime** — language(s), package manager, key frameworks (e.g. "Python 3.12, uv, pytest, Jinja2").
- **How to run / test** — the 2-3 commands that matter (e.g. `uv sync`, `uv run pytest`).
- **Conventions** — anything non-obvious (commit style, branch naming, formatting).
- **Entry points** — main package(s), CLI name, key modules.
- **Non-goals / known limitations** — optional.

### Generation behavior

- `issue-flow init` creates `this-project.md` from a Jinja template (`src/issue_flow/templates/docs/this-project.md.j2`) with placeholders, **only if it does not already exist**.
- `issue-flow update` does **not** overwrite an existing `this-project.md` (same rule as the rest of `04-designs-and-guides/`). If missing, it can re-create the stub.
- Optional flag: `issue-flow init --autofill-project` could try a best-effort autofill by reading `pyproject.toml` / `package.json` / `README.md` to pre-populate stack and entry-point fields. Default off.

### Integration with skills / rules

- Update `issueflow-rules.mdc.j2` to mention: "Before planning, skim `.issueflows/04-designs-and-guides/this-project.md` for project context."
- Update `issueflow_issue_plan` and `issueflow_issue_start` SKILLs to read it as part of their orientation step.

### Open questions

1. **Location**: `.issueflows/04-designs-and-guides/this-project.md` vs. repo-root `this-project.md` vs. piggyback on `AGENTS.md`. The 04-folder is the cleanest fit but is less discoverable to humans.
2. **Autofill scope**: do we try to parse `pyproject.toml` / `package.json` on init, or keep the template purely placeholder-based for v1?
3. **Naming**: `this-project.md` vs. `PROJECT.md` vs. `project-brief.md`. `this-project.md` is friendly but unconventional.

## Out of scope

- Full project-documentation generation (that's what `README.md` and the wider `docs/` tree are for).
- Any auto-updating based on code changes.

## Acceptance criteria

- A new Jinja template under `src/issue_flow/templates/docs/` for the project brief.
- `issue-flow init` creates the file from the template when missing.
- `issue-flow update` leaves any existing file untouched (and creates the stub only if missing).
- Rules / relevant skills reference the file as part of their orientation step.
- Tests in `tests/` covering: file is created on init, not overwritten on update, and is skipped on update if already present.
