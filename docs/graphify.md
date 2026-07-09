# Optional graphify integration

issue-flow has a lightweight integration with [graphify](https://iflow-graphify.net)
(PyPI: `graphifyy`, CLI: `graphify`) — a tool that turns the project into a
queryable knowledge graph that AI assistants can read instead of grepping
through files. The integration is **opt-in by installing `graphifyy` as its
own tool** (the same way you installed issue-flow): there is no enable flag and
no extras to remember — detection is purely PATH-based. (You *can* keep an LLM
API key in `.env` for the optional `extract` pass; see below.)

## What issue-flow does when `graphify` is on PATH

- `issue-flow init` and `issue-flow update` run `graphify cursor install` so
  the graphify Cursor skill is registered alongside the issue-flow scaffold.
  If graphify is not installed, both commands just print install hints and
  continue — they never block.
- A new `/iflow-graphify` entry point (skill on Cursor/Codex, command + skill
  for command-emitting editors) wraps `issue-flow graphify`. With no extra args
  it runs `graphify update <project>` — AST-only, **no LLM API key required**,
  so the no-arg case "just works". For richer semantic relationships add
  `extract` (`issue-flow graphify extract`) and configure a backend
  (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MOONSHOT_API_KEY`,
  or `--backend ollama` for a local LLM). You can set that key in the project
  `.env` — `issue-flow graphify` loads `.env` from the project root before
  invoking graphify — or export it in your shell environment. Your editor's own
  LLM is not available to subprocesses, so graphify needs its own backend.
  Other subcommands (`watch`, `cluster-only`, …) pass through too; trailing
  flags forward verbatim.
- The scaffolded rules and `/iflow-start` mention `graphify-out/GRAPH_REPORT.md`
  as a recommended pre-read when the file exists. `/iflow-graphify` is
  **off-path** — `/iflow` never auto-dispatches to it.

## Enabling

Install graphify as its own standalone tool:

```bash
uv tool install graphifyy   # recommended
# or
pipx install graphifyy
# or
pip install graphifyy
```

After installing, run `issue-flow update` once so the graphify Cursor skill
gets registered.

> **Why not an `issue-flow[graphify]` extra (or `uv tool install issue-flow --with graphifyy`)?**
> `uv tool install` only puts the **host package's** entry-point scripts on
> PATH. An extra (or `--with graphifyy`) pulls graphifyy into issue-flow's
> venv but leaves the `graphify` CLI invisible to the shell, so `/iflow-graphify`
> and `graphify cursor install` would still fail. Installing graphify as
> its own tool puts a real `graphify` shim on PATH and matches how we
> treat `git` / `gh`.

> **Just installed graphifyy and `issue-flow init` says it's still missing?**
> uv prints `~/.local/bin is not on your PATH` after the first
> `uv tool install`. Run `uv tool update-shell` (refreshes shell rc files),
> then **restart your shell and editor** so the new PATH takes effect.
> issue-flow's missing-CLI hint also detects this case and tells you the
> exact directory to add.

## The `issue-flow graphify` command

| Argument / Option               | Description |
| ------------------------------- | ----------- |
| `-C`, `--project-dir`           | Project root directory to scan with graphify. Defaults to `.` (current directory). Modeled on `git -C` so positional args can flow into graphify untouched. |
| `...graphify subcommand + args` | Optional graphify subcommand + flags. With no extras runs `graphify update <PROJECT_DIR>` — AST-only, **no LLM API key required**. The first extra arg, if it is a recognized build subcommand (`update`, `extract`, `watch`, `cluster-only`, `check-update`), picks the action; trailing tokens forward verbatim. |

Examples:

```bash
issue-flow graphify                       # AST-only rebuild, no API key needed
issue-flow graphify extract               # semantic LLM pass (needs an API key or --backend ollama)
issue-flow graphify cluster-only --no-viz # re-cluster an existing graph
issue-flow graphify ./subdir              # scan a subdirectory
```

When the `graphify` CLI is missing, the command prints install hints and exits
with code `2`. Outputs land in `graphify-out/` (`graph.html`,
`GRAPH_REPORT.md`, `graph.json`).

## API keys

Beyond the `ISSUEFLOW_*` settings, `issue-flow graphify` reads an LLM API key
from `.env` when present (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`, or `MOONSHOT_API_KEY`) and passes it through to the
`graphify extract` semantic pass. The no-arg `graphify update` build is
AST-only and needs no key.

## What to commit

`graphify-out/GRAPH_REPORT.md` is worth tracking in git — the scaffolded
skills read it as project context. The bulk outputs (`graph.html`,
`graph.json`, `graphify-out/cache/`) are multi-megabyte files that are fully
regenerated on every run; add them to `.gitignore`.
