# Archived issues — 2026-07-12

Pre-archive git ref: `84a348cbb7afd3c080e1b3daa57fdccd706f0d9d`
Recover any archived file with `git show 84a348cbb7afd3c080e1b3daa57fdccd706f0d9d:<path>` (or browse `git log -- <path>`).

## Issue #1: commands versus skills

- Source: https://github.com/jepegit/issue-flow/issues/1
- Archived files: issue1_original.md, issue1_status.md
- Summary: Investigated Agent Skills vs slash commands and implemented templating for three bundled skills (init/start/close) wired into issue-flow init/update. Documented skills in README and workflow docs.

## Issue #2: Enhance issue-init so that it selects issue related to current branch if no issue number is given

- Source: https://github.com/jepegit/issue-flow/issues/2
- Archived files: issue2_original.md, issue2_status.md
- Summary: Extended /issue-init to infer issue number from branch name (NN-slug pattern), refuse on main/master, and ask when ambiguous. Added tests and workflow docs.

## Issue #4: update issueflow for already initialized projects

- Source: https://github.com/jepegit/issue-flow/issues/4
- Archived files: issue4_original.md, issue4_status.md
- Summary: Made re-running init preserve user issue content and added issue-flow update subcommand to refresh commands/structure without destroying tracking files.

## Issue #7: trailing newlines

- Source: https://github.com/jepegit/issue-flow/issues/7
- Archived files: issue7_original.md, issue7_status.md
- Summary: Added agent-efficiency rules to issue-init so agents skip trailing-newline churn and redundant verification during capture.

## Issue #10: enhance issue-close with ability to bump version number

- Source: https://github.com/jepegit/issue-flow/issues/10
- Archived files: issue10_original.md, issue10_status.md
- Summary: Added optional semver bump to /issue-close via uv version --bump, packaged issueflow-version-bump skill, and aligned templates/docs/tests.

## Issue #13: Rename environment variable

- Source: https://github.com/jepegit/issue-flow/issues/13
- Archived files: issue13_original.md, issue13_status.md
- Summary: Renamed ISSUEFLOW_CURSOR_DIR to IDE-agnostic ISSUEFLOW_AGENT_DIR across config, templates, tests, and docs.

## Issue #14: Add a history file

- Source: https://github.com/jepegit/issue-flow/issues/14
- Archived files: issue14_original.md, issue14_status.md
- Summary: Created top-level HISTORY.md with Keep-a-Changelog-style release sections and linked it from README.

## Issue #15: update history when making changes worthy of mentioning

- Source: https://github.com/jepegit/issue-flow/issues/15
- Archived files: issue15_original.md, issue15_plan.md, issue15_status.md
- Summary: Extended /issue-close with HISTORY.md update step and issueflow-history-update skill (append to Unreleased or promote on bump); added ISSUEFLOW_HISTORY_FILE.

## Issue #16: can issueflow init command also create a dot env file

- Source: https://github.com/jepegit/issue-flow/issues/16
- Archived files: issue16_original.md, issue16_status.md
- Summary: issue-flow init now creates or augments a commented .env with ISSUEFLOW_* defaults without overwriting existing secrets.

## Issue #18: better documentation on dependencies

- Source: https://github.com/jepegit/issue-flow/issues/18
- Archived files: issue18_original.md, issue18_plan.md, issue18_status.md
- Summary: Added dependencies.py with git/gh detection, install hints, and init/update prompts; documented prerequisites in README with --skip-dep-check bypass.

## Issue #20: status of issues

- Source: https://github.com/jepegit/issue-flow/issues/20
- Archived files: issue20_original.md, issue20_plan.md, issue20_status.md
- Summary: Added read-only off-path /issue-status command and paired skill reporting local tracking state plus open GitHub issues cross-referenced.

## Issue #22: modern python best practices and issuflow init options

- Source: https://github.com/jepegit/issue-flow/issues/22
- Archived files: issue22_original.md, issue22_plan.md, issue22_status.md
- Summary: Added --skill-level init option (basic/standard/advanced) persisting to config.toml; advanced mode scaffolds optional python-quality-tools doc.

## Issue #24: utilize the tools folder and status files better

- Source: https://github.com/jepegit/issue-flow/issues/24
- Archived files: issue24_original.md, issue24_plan.md, issue24_status.md
- Summary: Made 00-tools discoverable via README template, prior-art checks, contribute-back nudges, and up-front status file seeding in /iflow-start.

## Issue #25: improve the issue close functionality

- Source: https://github.com/jepegit/issue-flow/issues/25
- Archived files: issue25_original.md, issue25_status.md
- Summary: Enhanced /issue-close to surface unrelated uncommitted changes before commit and remind users they remain on the issue branch after PR creation.

## Issue #26: create a new folder for storing designs and design decissions

- Source: https://github.com/jepegit/issue-flow/issues/26
- Archived files: issue26_original.md, issue26_status.md
- Summary: Added 04-designs-and-guides folder to scaffold, preserved on update, and wired plan/start/close/rules to read and record design decisions.

## Issue #31: problems with branches and merging

- Source: https://github.com/jepegit/issue-flow/issues/31
- Archived files: issue31_original.md, issue31_status.md
- Summary: Added branch preflight, stale-current-issues sweep, post-merge cleanup (later moved to cleanup), archived-issue guard, and hygiene rules.

## Issue #32: add grill-me skill

- Source: https://github.com/jepegit/issue-flow/issues/32
- Archived files: issue32_original.md, issue32_status.md
- Summary: Bundled grill-me planning interview skill with grill_me_default config toggle; integrated into iflow-plan when enabled.

## Issue #39: Expand issue-flow workflow with additional slash commands

- Source: https://github.com/jepegit/issue-flow/issues/39
- Archived files: issue39_original.md, issue39_status.md
- Summary: Added /iflow-plan, /iflow-pause, /iflow-cleanup, /iflow-yolo; strict migration moving planning out of start and cleanup out of close; added /iflow dispatcher.

## Issue #45: include issue comments

- Source: https://github.com/jepegit/issue-flow/issues/45
- Archived files: issue45_original.md, issue45_plan.md, issue45_status.md
- Summary: Made /issue-init fetch and triage GitHub comments into a curated summary; added issueflow-issue-comments skill with chronological precedence rules.

## Issue #48: Create options for issue flow modes

- Source: https://github.com/jepegit/issue-flow/issues/48
- Archived files: issue48_original.md, issue48_plan.md, issue48_status.md
- Summary: Implemented data-driven mode system (standard/simple + custom modes in config.toml); init --mode selects surfaces, update respects persisted mode.

## Issue #49: add graphify

- Source: https://github.com/jepegit/issue-flow/issues/49
- Archived files: issue49_original.md, issue49_plan.md, issue49_status.md
- Summary: Integrated optional graphify knowledge graph: graphify.py helper, issue-flow graphify CLI, /iflow-graphify command+skill, and rules/start/close hints.

## Issue #53: Add a project-summary doc (this-project.md) generated/maintained by issue-flow

- Source: https://github.com/jepegit/issue-flow/issues/53
- Archived files: issue53_original.md, issue53_plan.md, issue53_status.md
- Summary: Added this-project.md project brief under 04-designs-and-guides via create-if-missing ensure helper; referenced from rules, plan, and start.

## Issue #54: Allow for more interactive sessions

- Source: https://github.com/jepegit/issue-flow/issues/54
- Archived files: issue54_original.md, issue54_plan.md, issue54_status.md
- Summary: Added off-path /iflow-fix for iterative small fixes on one long-lived branch+issue with per-fix plans and status log entries ending in /iflow-close.

## Issue #55: agent tab improvement

- Source: https://github.com/jepegit/issue-flow/issues/55
- Archived files: issue55_original.md, issue55_plan.md, issue55_status.md
- Summary: Improved agent-facing documentation so lifecycle skills are easier to discover and invoke from the agent tab.

## Issue #56: rename from build to graphify

- Source: https://github.com/jepegit/issue-flow/issues/56
- Archived files: issue56_original.md, issue56_plan.md, issue56_status.md
- Summary: Renamed build command/skill/CLI to graphify across templates, docs, tests, and dogfood copies for naming alignment with the graphify tool.

## Issue #57: /issue-plan: add explicit 'prior-art discovery' step (codebase grep + graph hubs)

- Source: https://github.com/jepegit/issue-flow/issues/57
- Archived files: issue57_original.md, issue57_status.md
- Summary: Added prior-art discovery step to /iflow-plan (graphify GRAPH_REPORT.md + grep) recorded under ### Prior art; start reads it before implementing.

## Issue #58: Allow for not using uv

- Source: https://github.com/jepegit/issue-flow/issues/58
- Archived files: issue58_original.md, issue58_plan.md, issue58_status.md
- Summary: Made issue-flow toolchain-agnostic in templates/rules: respect conda/pip/poetry when documented, default to uv only when appropriate.

## Issue #62: Make issue-flow editor-agnostic (Cursor, Claude Code, opencode, Codex)

- Source: https://github.com/jepegit/issue-flow/issues/62
- Archived files: issue62_original.md, issue62_plan.md, issue62_status.md
- Summary: Made issue-flow editor-agnostic via editor profiles (Cursor, Claude Code, Codex, opencode) with profile-specific manifest outputs.

## Issue #63: Pick next issue

- Source: https://github.com/jepegit/issue-flow/issues/63
- Archived files: issue63_original.md, issue63_plan.md, issue63_status.md
- Summary: Added /iflow-pick front-door command to rank parked work and open GitHub issues, create branch, and run init; off-path explicit invocation.

## Issue #67: Multi-repo Cursor workspaces: issue-flow assumes a single project root

- Source: https://github.com/jepegit/issue-flow/issues/67
- Archived files: issue67_original.md, issue67_plan.md, issue67_status.md
- Summary: Added multi-repo workspace support: issue-flow agent resolve, issueflow-workspace.toml default, scoped rules, and design doc.

## Issue #70: Iterative small fixes

- Source: https://github.com/jepegit/issue-flow/issues/70
- Archived files: issue70_original.md, issue70_status.md
- Summary: Established /iflow-fix iterative-fixes session pattern with dated status log bullets (first of several iterative-small-fixes issues).

## Issue #71: Rename issue-* slash commands to a shorter, more consistent scheme

- Source: https://github.com/jepegit/issue-flow/issues/71
- Archived files: issue71_original.md, issue71_plan.md, issue71_status.md
- Summary: Renamed issue-* slash commands and skills to shorter iflow-* scheme; added pruning of retired scaffold files on update.

## Issue #75: Iterative small fixes

- Source: https://github.com/jepegit/issue-flow/issues/75
- Archived files: issue75_original.md, issue75_status.md
- Summary: Continued iterative-small-fixes session work with additional small fixes recorded in status log.

## Issue #79: new cursor conventions

- Source: https://github.com/jepegit/issue-flow/issues/79
- Archived files: issue79_original.md, issue79_plan.md, issue79_status.md
- Summary: Updated scaffolded rules/skills for current Cursor conventions (skills format, rules structure, disable-model-invocation patterns).

## Issue #81: add caveman skill

- Source: https://github.com/jepegit/issue-flow/issues/81
- Archived files: issue81_original.md, issue81_plan.md, issue81_status.md
- Summary: Added caveman terse-response Agent Skill for token-efficient replies; opt-in via invocation, later made config-driven in #91.

## Issue #82: switch back to main if clean

- Source: https://github.com/jepegit/issue-flow/issues/82
- Archived files: issue82_original.md, issue82_plan.md, issue82_status.md
- Summary: Added guidance to switch back to default branch when working tree is clean after merge, reducing accidental work on stale issue branches.

## Issue #84: archive issueflow

- Source: https://github.com/jepegit/issue-flow/issues/84
- Archived files: issue84_original.md, issue84_plan.md, issue84_status.md
- Summary: Designed and implemented /iflow-archive skill to condense old solved issues into dated summary files recoverable via git ref.

## Issue #85: Align issues with plan

- Source: https://github.com/jepegit/issue-flow/issues/85
- Archived files: issue85_original.md, issue85_plan.md, issue85_status.md
- Summary: Aligned GitHub issue metadata with local plan/status tracking conventions and documentation.

## Issue #88: enhance issue-flow cli tool for agentic use

- Source: https://github.com/jepegit/issue-flow/issues/88
- Archived files: issue88_original.md, issue88_plan.md, issue88_status.md
- Summary: Added agent-facing CLI subcommands (resolve, stage, sweep, etc.) for deterministic machine-readable issue-flow operations.

## Issue #91: add config-driven always-on caveman style (caveman_default)

- Source: https://github.com/jepegit/issue-flow/issues/91
- Archived files: issue91_original.md, issue91_status.md
- Summary: Added caveman_default config flag so terse caveman style can be always-on per project via config.toml and ISSUEFLOW_CAVEMAN_DEFAULT.

## Issue #94: missing requirement - tomlkit

- Source: https://github.com/jepegit/issue-flow/issues/94
- Archived files: issue94_original.md, issue94_plan.md, issue94_status.md
- Summary: Added missing tomlkit dependency required by modes/config.toml read-write helpers.

## Issue #96: cli command for creating config.toml file

- Source: https://github.com/jepegit/issue-flow/issues/96
- Archived files: issue96_original.md, issue96_plan.md, issue96_status.md
- Summary: Added CLI command to create/seed .issueflows/config.toml for projects missing configuration.

## Issue #104: Iterative small fixes

- Source: https://github.com/jepegit/issue-flow/issues/104
- Archived files: issue104_original.md, issue104_status.md
- Summary: Another iterative-small-fixes session tranche recorded in issue status log.

## Issue #106: chose flow details from issue labels

- Source: https://github.com/jepegit/issue-flow/issues/106
- Archived files: issue106_original.md, issue106_plan.md, issue106_status.md
- Summary: Added label-driven flow routing (yolo label triggers /iflow-yolo) controlled by label_flows and yolo_label in config.toml.

## Issue #108: lacking ref to grill-me

- Source: https://github.com/jepegit/issue-flow/issues/108
- Archived files: issue108_original.md, issue108_plan.md, issue108_status.md
- Summary: Added grill-me references to planning templates where the skill was previously undocumented.

## Issue #113: The different steps in iflow requires different models

- Source: https://github.com/jepegit/issue-flow/issues/113
- Archived files: issue113_original.md, issue113_plan.md, issue113_status.md
- Summary: Added per-step MODEL & EXECUTION DIRECTIVE profiles (economy vs reasoning) with step_directives config and optional model labels at pick time.

## Issue #114: Iterative small fixes

- Source: https://github.com/jepegit/issue-flow/issues/114
- Archived files: issue114_original.md, issue114_status.md
- Summary: Iterative-small-fixes session tranche with additional recorded fixes.

## Issue #117: great skills

- Source: https://github.com/jepegit/issue-flow/issues/117
- Archived files: issue117_original.md, issue117_plan.md, issue117_status.md
- Summary: Applied writing-great-skills guidance to improve issue-flow skill structure, descriptions, and frontmatter across lifecycle skills.

## Issue #118: slash is annoying

- Source: https://github.com/jepegit/issue-flow/issues/118
- Archived files: issue118_original.md, issue118_plan.md, issue118_status.md
- Summary: Added keyboard-friendly chat invocation (iflow plan, iflow pick, etc.) as alternative to slash commands for awkward keyboard layouts.

## Issue #121: have I updated my flow skills

- Source: https://github.com/jepegit/issue-flow/issues/121
- Archived files: issue121_original.md, issue121_plan.md, issue121_status.md
- Summary: Verified and refreshed flow skill templates so dogfood scaffold matches packaged templates after upstream skill changes.

## Issue #125: version bump skill must be more flexible

- Source: https://github.com/jepegit/issue-flow/issues/125
- Archived files: issue125_original.md, issue125_plan.md, issue125_status.md
- Summary: Made version-bump skill document all uv version --bump levels with pre-release-aware default channel selection.

## Issue #126: workspace issue flow

- Source: https://github.com/jepegit/issue-flow/issues/126
- Archived files: issue126_original.md, issue126_plan.md, issue126_status.md
- Summary: Added workspace-level issue-flow registry (issueflow-workspace.toml) for multi-root editor workspaces.

## Issue #133: deterministic fast path

- Source: https://github.com/jepegit/issue-flow/issues/133
- Archived files: issue133_original.md, issue133_plan.md, issue133_status.md
- Summary: Added deterministic CLI fast paths for agent operations reducing LLM interpretation for version bump, archive, and plan parsing.

## Issue #136: Epic planning, stage 1: /iflow-epic skill + 05-epics scaffold (draft-only)

- Source: https://github.com/jepegit/issue-flow/issues/136
- Archived files: issue136_original.md, issue136_plan.md, issue136_status.md
- Summary: Epic stage 1: /iflow-epic skill drafts staged epic plans under 05-epics/ anchored to a GitHub issue (draft-only, no auto-publish).

## Issue #137: Epic planning, stage 1: publish a confirmed epic plan to GitHub issues

- Source: https://github.com/jepegit/issue-flow/issues/137
- Archived files: issue137_original.md, issue137_plan.md, issue137_status.md
- Summary: Epic stage 1 publish: /iflow-epic publish creates confirmed stage issues on GitHub with yolo labels and idempotent Published markers in plan.

## Issue #138: Epic planning, stage 2: deterministic issue-flow agent epic-status CLI

- Source: https://github.com/jepegit/issue-flow/issues/138
- Archived files: issue138_original.md, issue138_plan.md, issue138_status.md
- Summary: Epic stage 2: issue-flow agent epic-status CLI for deterministic epic/stage progress reporting from plan files.

## Issue #139: Epic planning, stage 2: /iflow-pick and /iflow epic awareness + stage gates

- Source: https://github.com/jepegit/issue-flow/issues/139
- Archived files: issue139_original.md, issue139_status.md
- Summary: Epic stage 2: /iflow-pick and /iflow gained epic awareness and stage-gate checks before picking issues from epic stages.

## Issue #140: Cycling mode, stage 1: deterministic issue-flow agent queue CLI

- Source: https://github.com/jepegit/issue-flow/issues/140
- Archived files: issue140_original.md, issue140_plan.md, issue140_status.md
- Summary: Cycling stage 1: issue-flow agent queue CLI resolves explicit lists, label: filters, or epic stage queues with toposort ordering.
