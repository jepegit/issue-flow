# Graph Report - issue-flow  (2026-06-16)

## Corpus Check
- 39 files · ~27,589 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 571 nodes · 775 edges · 59 communities (29 shown, 30 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 163 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bd8d4332`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]

## God Nodes (most connected - your core abstractions)
1. `run_init()` - 58 edges
2. `render_template()` - 33 edges
3. `_default_context()` - 26 edges
4. `run_update()` - 20 edges
5. `_fake_console()` - 17 edges
6. `Cursor issue workflow (slash commands)` - 17 edges
7. `run_build()` - 15 edges
8. `get_profile()` - 14 edges
9. `History` - 14 edges
10. `Cursor issue workflow (slash commands)` - 14 edges

## Surprising Connections (you probably didn't know these)
- `get_environment()` --calls--> `Environment`  [INFERRED]
  src/issue_flow/templating.py → local/copy-of-other-repo/03-solved-issues/issue6_status.md
- `test_init_creates_cursor_rule()` --calls--> `run_init()`  [INFERRED]
  tests/test_init.py → src/issue_flow/init.py
- `test_init_all_editors_scaffolds_every_agent_dir()` --calls--> `run_init()`  [INFERRED]
  tests/test_init.py → src/issue_flow/init.py
- `main()` --calls--> `run_update()`  [INFERRED]
  scripts/update_issueflow_setup.py → src/issue_flow/init.py
- `test_default_settings()` --calls--> `Settings`  [INFERRED]
  tests/test_config.py → src/issue_flow/config.py

## Communities (59 total, 30 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (72): build_manifest(), Return the ``(template, output_path_template)`` entries for ``profile``., Render a single template by name and return the result string., render_template(), _default_context(), Tests for issue_flow.templating., Non-cursor editors must not write under .cursor/ or mention "Cursor"., Every expected slash command and skill has a manifest entry. (+64 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (54): _build_graphify_argv(), _candidate_install_locations(), find_orphan_install(), _graphify_dependency(), is_available(), _print_install_hints(), Graphify integration for issue-flow.  Graphify (PyPI: ``graphifyy``, CLI: ``gr, Return the ``Dependency`` entry for graphify from the recommended list. (+46 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (39): _already_initialized(), _create_issueflow_dirs(), _dotenv_documents_key(), _ensure_agents_md(), _ensure_dotenv_file(), _graphify_postinstall(), issue-flow: Agents should behave. Let them follow the issue flow., Render templates from ``manifest`` and write under project_root.      When ``f (+31 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (35): check_dependencies(), check_recommended(), Dependency, format_missing_report(), prompt_or_skip(), External CLI dependency detection for issue-flow.  The scaffolded workflow she, Return the subset of ``dependencies`` not on ``PATH``.      Mirrors :func:`che, Return the subset of ``dependencies`` whose ``command`` is not on ``PATH``. (+27 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (30): 1. Make sure tests pass, 2. Bump the version, 3. Commit and push, 4. Create a release, code:bash (git clone https://github.com/jepegit/issue-flow.git), code:bash (git add pyproject.toml uv.lock), code:bash (release), code:bash (gh release create v0.2.0 --generate-notes) (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (29): Branch hygiene, code:bash (uv sync                 # install/refresh all deps from the ), code:bash (uv run pytest                      # run the test suite), code:text (src/issue_flow/), code:bash (# Either activate the environment first…), code:bash (# ❌ BAD: bare interpreter), code:bash (# Add or upgrade dependencies), code:bash (issue-flow/) (+21 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (25): Changelog, code:text (your-project/), code:bash (uv tool install graphifyy   # recommended), code:bash (uv tool install issue-flow), code:bash (uv add --dev issue-flow), code:bash (cd your-project), code:block6 (issue-flow init [PROJECT_DIR] [--force] [--skip-dep-check]), code:bash (issue-flow init                          # Cursor (default)) (+17 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (17): agent_dir(), _detect_project_name(), Configuration for issue-flow, backed by .env files and environment variables., Try to read the project name from pyproject.toml, fall back to dir name., Runtime settings for issue-flow.      Values come from environment variables (, Agent directory for ``profile``: explicit override wins, else profile default., Build the Jinja2 template context dictionary for ``profile``.          When ``, Settings (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.14
Nodes (18): EditorProfile, get_profile(), Editor profiles for issue-flow's multi-tool scaffolding.  issue-flow renders t, Resolve a raw ``--editor`` selection into ordered, de-duplicated profiles., How issue-flow should scaffold itself for one AI coding tool.      Attributes:, Return the :class:`EditorProfile` for ``editor_id``.      Raises:         Val, resolve_editors(), Tests for issue_flow.editors (editor profile registry and resolution). (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (15): _plain(), Tests for the `issue-flow` Typer CLI., A leading subcommand and trailing flags must reach `graphify` verbatim., When graphify is not installed, `issue-flow graphify` exits with the error code, Strip ANSI color/style codes so help text can be matched reliably.      Rich c, `issue-flow --help` must mention the `graphify` command., `issue-flow init --help` must advertise the --editor option., `issue-flow init --editor codex` writes the codex tree without commands. (+7 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (17): 0. `/iflow` — smart dispatcher (quick start), 0a. `/issue-pick` — choose the next issue (front door), 1. `/issue-init` — capture the issue locally, 2. `/issue-plan` — design the approach, 2. `/issue-start` — plan and implement, 3. `/issue-close` — land the work, 3. `/issue-start` — implement the plan, 4. `/issue-pause` — park work safely (+9 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (14): CLI options added, Dependencies, Environment, Issue #6 Status: Improve user experience through more advanced logging and status updates, Logging (loguru), Progress bar (tqdm), Summary of changes, Tests (+6 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (15): CLI options, code:bash (# Install dependencies and create a uv-managed virtual envir), code:python (from volta.query import load_test, get_cycles), code:block3 (Cycle   Cycle - additional   Cycle type   rows   row no   Ch), code:block4 (<Cycle>  <Cycle-additional>  <Cycle type>  <Feature name>  <), code:block5 (volta/), Data file – `Cell_ID_xxx_Test_nnnnn.txt`, Documentation (+7 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (15): 0. `/iflow` — smart dispatcher (quick start), 0a. `/issue-pick` — choose the next issue (front door), 1. `/issue-init` — capture the issue locally, 2. `/issue-plan` — design the approach, 3. `/issue-start` — implement the plan, 4. `/issue-pause` — park work safely, 5. `/issue-close` — land the work, 6. `/issue-cleanup` — post-merge branch hygiene (+7 more)

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (14): [0.1.0] - 2026-04-03, [0.1.1] - 2026-04-04, [0.1.2] - 2026-04-15, [0.1.3] - 2026-04-15, [0.1.4] - 2026-04-15, [0.2.0] - 2026-04-15, [0.2.1] - 2026-04-16, [0.2.1.post1] - 2026-04-16 (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.17
Nodes (11): _callback(), graphify(), init(), main(), Command-line interface for issue-flow., Rebuild the graphify knowledge graph for the project.      With no extra argum, Entry point for the `issue-flow` console script., Agents should behave. Let them follow the issue flow. (+3 more)

### Community 16 - "Community 16"
Cohesion: 0.2
Nodes (10): Scaffold .issueflows/ directories and editor config (commands, rules, skills)., run_init(), Running init should create all three slash-command files., Non-interactive stdin (CI) must auto-skip the prompt., init writes AGENTS.md containing the issue-flow managed block., test_init_continues_in_non_tty_when_deps_missing(), test_init_creates_agents_md_with_managed_block(), test_init_creates_cursor_commands() (+2 more)

### Community 17 - "Community 17"
Cohesion: 0.2
Nodes (9): Tests for issue_flow.init (the init command)., init should create .env with commented ISSUEFLOW_* defaults when absent., --editor claude scaffolds under .claude/ with a CLAUDE.md rules file., An unknown --editor value aborts with a non-zero exit and no scaffold., test_init_all_editors_scaffolds_every_agent_dir(), test_init_claude_editor_writes_claude_tree_and_claude_md(), test_init_creates_cursor_rule(), test_init_creates_dotenv_with_commented_keys() (+1 more)

### Community 18 - "Community 18"
Cohesion: 0.33
Nodes (5): Additional comment (GitHub), code:bash, Issue #5: More granular option for outputs, Original issue text, Usage

### Community 19 - "Community 19"
Cohesion: 0.33
Nodes (5): Improve logging, Improve status feedback, Issue #6: Improve user experience through more advanced logging and status updates, Original issue text, Testing

### Community 20 - "Community 20"
Cohesion: 0.4
Nodes (4): code:bash (uv run pytest), Done, How to run, Issue #1 status: Create initial test suite

### Community 21 - "Community 21"
Cohesion: 0.4
Nodes (4): code:bash (uv run pytest), Done, How to run, Issue #2 status: set up environment handling

### Community 22 - "Community 22"
Cohesion: 0.5
Nodes (3): Implementation notes, Issue #5 — status, Scope

### Community 23 - "Community 23"
Cohesion: 0.5
Nodes (3): Shared pytest fixtures for issue-flow tests., Make ``check_dependencies`` a no-op by default.      The production dep-check, _stub_dependency_check()

## Knowledge Gaps
- **284 isolated node(s):** `Refresh this repository's issue-flow scaffold from packaged templates.  Equiva`, `Command-line interface for issue-flow.`, `Agents should behave. Let them follow the issue flow.`, `Scaffold issue-flow directories and editor config files in a project.`, `Refresh packaged editor commands, rules, and workflow doc from this package.` (+279 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_init()` connect `Community 16` to `Community 0`, `Community 2`, `Community 3`, `Community 7`, `Community 8`, `Community 15`, `Community 17`, `Community 26`, `Community 27`, `Community 28`, `Community 29`, `Community 30`, `Community 31`, `Community 32`, `Community 33`, `Community 34`, `Community 35`, `Community 36`, `Community 37`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 44`, `Community 45`, `Community 46`, `Community 47`, `Community 48`, `Community 49`, `Community 50`, `Community 51`, `Community 52`?**
  _High betweenness centrality (0.213) - this node is a cross-community bridge._
- **Why does `render_template()` connect `Community 0` to `Community 2`, `Community 11`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `graphify()` connect `Community 15` to `Community 1`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `run_init()` (e.g. with `init()` and `Settings`) actually correct?**
  _`run_init()` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `render_template()` (e.g. with `_write_manifest_files()` and `_ensure_agents_md()`) actually correct?**
  _`render_template()` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `run_update()` (e.g. with `main()` and `update()`) actually correct?**
  _`run_update()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Refresh this repository's issue-flow scaffold from packaged templates.  Equiva`, `Command-line interface for issue-flow.`, `Agents should behave. Let them follow the issue flow.` to the rest of the system?**
  _284 weakly-connected nodes found - possible documentation gaps or missing edges._