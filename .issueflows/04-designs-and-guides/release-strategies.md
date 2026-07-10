# Release strategies (version bump)

Context: issue #125 — in tag-versioned projects (cellpy), the
`iflow-version-bump` skill's `uv version --bump` advice was wrong: the built
version comes from git tags, so "bumping" means tagging, not editing
`pyproject.toml`.

## Decision

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

## Alternatives considered

- `version_strategy` key in `.issueflows/config.toml` — rejected for now:
  the brief is the human-facing place for project conventions, and no code
  reads the value yet. Revisit if a deterministic `issue-flow agent
  version-plan` CLI (PEP 440 next-tag arithmetic) lands as a follow-up.
- Tagging during `/iflow-close` (pre-merge) — rejected: wrong commit under
  squash merges.
