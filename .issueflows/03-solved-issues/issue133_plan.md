# Plan — Issue #133: deterministic version-plan fast path

## Goal

`issue-flow agent version-plan [--bump LEVEL ...] [--json]` — the mechanical
half of the release-strategy work from #125: detect the strategy, read the
current version (static field or latest tag), do the PEP 440 next-version
arithmetic, and return the exact commands. "CLI for facts, prompts for
judgment", like `agent switchback`.

## Constraints

- **Read-only**: the command computes and reports; it never edits
  `pyproject.toml`, never creates tags.
- The `this-project.md` release section still beats detection — that rule is
  interpretive and stays agent-side; the payload flags whether the section
  exists (`brief_release_section`) so the agent knows to read it.
- Same level table and pre-release-aware default as the skill.
- Tag style (leading `v`) is preserved from the latest tag.

## Approach

- New `src/issue_flow/versionplan.py`: PEP 440 subset parser/formatter,
  sequential bump ops (levels applied in canonical order), strategy
  detection from `pyproject.toml` (static version → `uv`;
  `dynamic = ["version"]` + setuptools-scm / hatch-vcs / versioningit →
  `tag`; else `unknown` with a reason).
- `gitutils.latest_tag()`: `git describe --tags --abbrev=0`, falling back to
  `git tag --sort=-v:refname`.
- `agent.run_version_plan` + `agent_app` command `version-plan`.
- `iflow-version-bump` skill gains a "CLI fast path (optional)" note.
- Docs (`docs/cli.md`), HISTORY, scaffold regen.

## Semantics worth pinning (tests lock these)

- `alpha`/`beta`/`rc` on the same label → `aN+1`; promotion (`a→b→rc`) →
  new label at 1; demotion (`rc→alpha`) → refused with a note.
- `alpha` on a stable version → advance `patch` first, then `a1`
  (forward-moving; `1.0.4` + alpha → `1.0.5a1`), with an explanatory note.
- `stable` drops pre/dev segments; `dev` alone is only valid when the
  current version already has a dev segment, else it must be paired.
- Levels are applied in canonical order regardless of flag order
  (`--bump alpha --bump minor` ≡ `minor` then `alpha` → `0.5.0a1`).

## Test strategy

Unit tests for parse/bump/detection (every table example plus promotion,
demotion-refusal, stable→alpha, combined levels, `v` prefix, defaults);
CLI tests for static, tag (mocked `latest_tag`), and unknown strategies;
template test that the skill mentions the fast path (the template↔CLI
consistency suite covers the command name automatically).
