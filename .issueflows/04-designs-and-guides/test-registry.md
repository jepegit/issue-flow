# Test registry

Living index of notable tests for the optional **essential tests** paradigm
(see [essential-tests.md](./essential-tests.md)). Seeded once by issue-flow;
**never overwritten** on `issue-flow update` — agents and humans grow the table.

When `[issueflow].essential_tests` is true, `/iflow-close` / `/iflow-build`
(per `essential_review`) should add or update rows for tests **touched by the
current issue**. `/iflow-doctor` may audit the whole suite against this table.

| Test (node id or path::name) | Essential? | Always? | Code under test | Issue | Notes / demote? |
| --- | --- | --- | --- | --- | --- |
| `tests/test_workspace_actions.py` (module) | yes | yes | `run_workspace_status` / `_doctor` / `_dirty`, `iter_workspace_members` | #318 | Fast fan-out contract |
| `tests/test_project.py::test_iter_workspace_members_dedupes_and_walks_up` | yes | yes | `project.iter_workspace_members` | #318 | |
| `tests/test_project.py::test_iter_workspace_members_none_without_toml` | yes | yes | `project.iter_workspace_members` | #318 | |
| `tests/test_templating.py::test_noob_footer_epic_gap_uses_session_not_next_command` | no | no | `_noob_next.md.j2` | #337 | Footer decision table; not marked essential on this branch |
| `tests/test_global_both_skills.py::test_init_writes_both_stems_to_cursor_global_and_keeps_project` | no | no | `materialize_user_global_both_skills` | #339 | Cursor init fans out to `~/.agents/skills` |
| `tests/test_doc_links.py::test_no_unversioned_readthedocs_page_links` | yes | yes | README, `docs/`, `src/issue_flow/templates/` links | #342 | Fast text scan; stops scaffolded projects getting 404 doc links |
| `tests/test_doc_links.py::test_no_mangled_graphify_domain` | yes | yes | README, `docs/`, `src/issue_flow/templates/` links | #353 | Blocks the `iflow-graphify.net` rename artefact |
| `tests/test_doc_quickstart.py` (module) | no | no | `docs/index.md`, `docs/getting-started.md`, `README.md` quick-start tables | #348 | Docs consistency guard; not essential |

**Columns**

- **Essential?** — currently marked with the configured pytest marker.
- **Always?** — should stay essential even after the originating issue closes.
- **Code under test** — modules/symbols (graphify can help).
- **Issue** — GitHub number that introduced or last reviewed the test.
- **Notes / demote?** — why essential, or candidate for demotion.
