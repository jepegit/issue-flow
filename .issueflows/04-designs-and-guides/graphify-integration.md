# Graphify integration: design decisions

**Issue:** [#49 — add graphify](https://github.com/jepegit/issue-flow/issues/49)
**Status:** decided 2026-05-14, implemented in the same issue.
**Scope:** how issue-flow integrates with [graphify](https://graphify.net) (PyPI: `graphifyy`, CLI: `graphify`).

## Context

Graphify turns a project (code + docs + papers + images + videos) into a queryable knowledge graph that AI assistants can read instead of grepping through files. Issue #49 asked for an opt-in integration so issue-flow's scaffold sets graphify up automatically, agents know the graph exists, and there is a one-shot command to refresh it.

## Decisions

### 1. External CLI, no Python dependency

issue-flow does **not** depend on `graphifyy` — not as a hard dependency and
not as an optional extra. The integration is purely a runtime PATH lookup
plus subprocess passthrough to the `graphify` CLI. Users install graphify as
its own standalone tool (`uv tool install graphifyy`), the same way they
install issue-flow.

**Alternatives considered**

- *Hard dependency* — pull `graphifyy` for every install. Rejected: graphify
  has a large transitive footprint (tree-sitter, optional video/PDF/MCP
  extras). issue-flow has 4 small dependencies today; we want to keep that.
- *Optional Python extra* (`uv tool install 'issue-flow[graphify]'`,
  `pyproject.toml` declaring `[project.optional-dependencies] graphify =
  ["graphifyy>=0.7"]`). Initially shipped, then **rolled back** before
  release. Reason: `uv tool install <pkg>` only exposes `<pkg>`'s own
  entry-point scripts on PATH; extras get installed into the same venv but
  their CLIs stay hidden. So `uv tool install 'issue-flow[graphify]'` would
  pull graphifyy in but leave `/build` and `graphify cursor install`
  broken — the extra promised something it could not deliver to the primary
  install audience. Plain `pip install issue-flow[graphify]` would work,
  but that is not the recommended install path.
- *`issue-flow install-graphify` helper* that runs `uv tool install
  graphifyy` for the user. Rejected: too magic, picks the wrong installer
  for some users, and the manual two-step install is one extra command for
  what's now a fully external dependency. Same posture as `git` / `gh`.

### 2. Auto-detect at runtime, no `--with graphify` flag

`init` / `update` call `shutil.which("graphify")`. If the CLI is on `PATH`, they run `graphify cursor install` (best-effort; failures are reported but never abort the parent command). Otherwise they print install hints and continue.

The graphify-flavored mentions in our scaffolded markdown (rules, `/issue-start`, `/issue-close`, `/iflow`) are **always rendered** so there is nothing to "switch on". Agents are told to consult `graphify-out/GRAPH_REPORT.md` *if it exists* — when the user has not opted in, the file is absent and the guidance is a no-op.

**Alternatives considered**

- *`--with graphify` flag persisted in `.env`* (the original issue suggestion). Rejected: introduces hidden state, doubles the surface area of `init`/`update` (`--with` and `--without`), and the auto-detect path achieves the same UX with less code. Surfaced this trade-off to the user; they confirmed auto-detect.
- *One-shot flag, no persistence* — same surface area as the sticky version but with worse UX (must re-pass on every `update`).

### 3. Medium lifecycle integration

What we ship:

- New CLI: `issue-flow build [PROJECT_DIR] [...args]` — pure passthrough wrapper around `graphify` (forward every flag verbatim, do not re-implement graphify's flag set).
- New slash command `/build` and matching `/issueflow-build` agent skill.
- `init` / `update` auto-run `graphify cursor install` (best-effort) when graphify is on PATH.
- `issueflow-rules.mdc` gains a "Knowledge graph" section pointing at `graphify-out/GRAPH_REPORT.md`.
- `/issue-start` suggests skimming the graph report; `/issue-close` suggests `/build` after structural changes. Neither runs `graphify` automatically.

What we deliberately **do not** ship:

- No automatic `graphify .` from `/issue-close`. Building the graph can be slow (LLM passes for docs/PDFs) and may have cost implications; we keep it opt-in.
- No `graphify hook install`. The user can run it directly if they want post-commit rebuilds; we do not want to touch `.git/hooks` from `issue-flow`.
- No deep wrapper over graphify flags. `issue-flow build` is a thin passthrough; if graphify adds or renames flags upstream, we do not need a release.

**Alternatives considered**

- *Light* (only `/build` + `cursor install`, leave existing rules/commands untouched). Rejected: agents would not know the graph exists.
- *Heavy* (auto-rebuild from `/issue-close` and/or `graphify hook install`). Rejected: too much magic, surprises users who do not know their changes trigger an LLM pass.

## Consequences

- Two new modules: `src/issue_flow/graphify.py` (`is_available`, `register_with_cursor`, `run_build`) and a new `RECOMMENDED_DEPENDENCIES` list in `dependencies.py`.
- One new template (`commands/build.md.j2`) + one new skill (`skills/issueflow_build/SKILL.md.j2`); manifest count goes from 21 to 23.
- `issue-flow build` exits `2` (not `1`) when `graphify` is missing, to distinguish "tool not installed" from "graphify ran and failed".
- Graphify is a fast-moving upstream. Because we only shell out to the CLI, version-skew between issue-flow and graphify is harmless: agents see whatever flags the installed `graphify` supports.

## Notes for future work

- If we add `issue-flow status` (already on the README's Future plans), it could surface graph freshness (`graphify-out/manifest.json` mtime vs source tree) without re-implementing graphify's freshness check.
- If multi-tool support lands (Claude Code, Windsurf, etc.), `register_with_cursor` should grow a sibling `register_with_<tool>` that calls `graphify <tool> install`.
