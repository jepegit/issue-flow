# Test registry

Living index of notable tests for the optional **essential tests** paradigm
(see [essential-tests.md](./essential-tests.md)). Seeded once by issue-flow;
**never overwritten** on `issue-flow update` — agents and humans grow the table.

When `[issueflow].essential_tests` is true, `/iflow-close` / `/iflow-build`
(per `essential_review`) should add or update rows for tests **touched by the
current issue**. `/iflow-doctor` may audit the whole suite against this table.

| Test (node id or path::name) | Essential? | Always? | Code under test | Issue | Notes / demote? |
| --- | --- | --- | --- | --- | --- |
| `tests/test_workspace_actions.py` (module) | yes | yes | `run_workspace_status` / `_doctor` / `_dirty` / `_git_status` / `_git_fetch`, `iter_workspace_members` | #318 / #381 | Fast fan-out contract |
| `tests/test_project.py::test_iter_workspace_members_dedupes_and_walks_up` | yes | yes | `project.iter_workspace_members` | #318 | |
| `tests/test_project.py::test_iter_workspace_members_none_without_toml` | yes | yes | `project.iter_workspace_members` | #318 | |
| `tests/test_templating.py::test_noob_footer_epic_gap_uses_session_not_next_command` | no | no | `_noob_next.md.j2` | #337 | Footer decision table; not marked essential on this branch |
| `tests/test_global_both_skills.py::test_init_writes_both_stems_to_cursor_global_and_keeps_project` | no | no | `materialize_user_global_both_skills` | #339 | Cursor init fans out to `~/.agents/skills` |
| `tests/test_doc_links.py::test_no_unversioned_readthedocs_page_links` | yes | yes | README, `docs/`, `src/issue_flow/templates/` links | #342 | Fast text scan; stops scaffolded projects getting 404 doc links |
| `tests/test_doc_links.py::test_no_mangled_graphify_domain` | yes | yes | README, `docs/`, `src/issue_flow/templates/` links | #353 | Blocks the `iflow-graphify.net` rename artefact |
| `tests/test_doc_quickstart.py` (module) | no | no | `docs/index.md`, `docs/getting-started.md`, `README.md` quick-start tables | #348 | Docs consistency guard; not essential |
| `tests/test_queueplan.py::test_build_queue_closed_external_dependency_does_not_block` | yes | yes | `queueplan.build_queue` (`closed_external`) | #364 | Epic stage N+1 must not look blocked by closed stage N |
| `tests/test_queueplan.py::test_build_queue_blocking_is_transitive` | yes | yes | `queueplan.build_queue` | #364 | A dependant must never be queued ahead of a blocked dep |
| `tests/test_cli.py::test_agent_queue_closed_dependency_outside_queue_is_satisfied` | no | no | `agent.run_queue` outside-dep state lookup | #364 | CLI wiring for `closed_external` |
| `tests/test_workflow_doc.py::test_command_mode_membership_lists_standard_first` | yes | yes | `modes.command_mode_membership` | #358 | Pure; feeds the Modes column |
| `tests/test_workflow_doc.py` (other tests) | no | no | `docs/issue-workflow.md.j2` structure per editor / novice | #358 | Renders via `run_init`; guards the command-reference layout |
| `tests/test_doc_configuration.py::test_all_settings_table_lists_every_config_key_once` | yes | yes | `docs/configuration.md` vs `config_ops.CONFIG_KEYS` | #359 | Adding a knob without documenting it fails fast |
| `tests/test_templating.py::test_cycle_bakes_onfail_default` | no | no | `iflow_cycle` skill/command bake of `cycle_onfail` | #248 | Config default bake; leave unmarked |
| `tests/test_doc_configuration.py` (other tests) | no | no | `docs/configuration.md` layout | #359 | Starts with Common changes; no bare issue numbers |
| `tests/test_worktree_location.py::test_default_is_sibling` / `test_workspace_folder_keeps_sibling_even_with_worktrees_dir` / `test_existing_worktrees_dir_is_used` | yes | yes | `gitutils.resolve_worktree_location` | #328 | Core location rules; pure, fast |
| `tests/test_worktree_location.py` (other tests) | no | no | fallbacks, `~`, CLI add/remove, project-vs-user override | #328 | Uses real temp git repos |
| `tests/test_self_update.py` (module) | no | no | `self_update.run_self_update`, receipt inspect | #382 | Mocked uv/CLI; leave unmarked |
| `tests/test_templating.py::test_cleanup_bakes_on_bleeding_edge` | no | no | cleanup skill/command bake of `on_bleeding_edge` | #382 | Config default bake |
| `tests/test_doc_configuration.py::test_all_settings_table_lists_every_config_key_once` | yes | yes | `docs/configuration.md` vs `CONFIG_KEYS` | #382 | Already essential; covers new knob |
| `tests/test_agent_sync_branch.py::test_stacked_child_auto_detects_squash_landed_parent` | no | no | `agent._detect_stacked_base`, `gitutils.content_landed`, `rebase_onto(base=)` | #386 | Real git repos; the drive stopper (stacked child on squash-landed parent) |
| `tests/test_agent_sync_branch.py::test_design_guide_and_status_conflicts_resolve_keep_both` | no | no | `agent._resolve_sync_conflicts`, `history.resolve_additive_conflict` | #386 | Registry-table + status-file keep-both |
| `tests/test_history.py::test_additive_resolver_refuses_heading_and_prose` | no | no | `history.resolve_additive_conflict` | #386 | Refusal floor for the widened resolver |
| `tests/test_config.py::test_cycle_nonyolo_default_and_precedence` | no | no | `Settings.resolve_cycle_nonyolo`, `modes.normalize_cycle_nonyolo` | #386 | toml > env > default; invalid ignored |
| `tests/test_cli.py::test_agent_state_reports_version_drift` | no | no | `agent.version_drift_fields`, `rendered_skills_version` | #386 | Stale-skills warning surface |
| `tests/test_version.py::test_version_comes_from_package_metadata` | yes | yes | `issue_flow.__version__` | #386 | Root cause of every stale `issue-flow-version` stamp; cheap |
| `tests/test_cleanup_yes_warning.py` (module) | no | no | `init._warn_cleanup_yes_a2` | #388 | Warning when `cleanup_yes_a2` is on; leave unmarked |
| `tests/test_templating.py::test_cleanup_bakes_yes_knobs` | no | no | cleanup/close skill bake of `cleanup_yes_*` / `auto_cleanup` | #388 | Config default bake; leave unmarked |
| `tests/test_doc_configuration.py::test_all_settings_table_lists_every_config_key_once` | yes | yes | `docs/configuration.md` vs `CONFIG_KEYS` | #388 | Already essential; digit keys (`cleanup_yes_a1`) must match |

**Columns**

- **Essential?** — currently marked with the configured pytest marker.
- **Always?** — should stay essential even after the originating issue closes.
- **Code under test** — modules/symbols (graphify can help).
- **Issue** — GitHub number that introduced or last reviewed the test.
- **Notes / demote?** — why essential, or candidate for demotion.
