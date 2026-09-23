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

**Columns**

- **Essential?** — currently marked with the configured pytest marker.
- **Always?** — should stay essential even after the originating issue closes.
- **Code under test** — modules/symbols (graphify can help).
- **Issue** — GitHub number that introduced or last reviewed the test.
- **Notes / demote?** — why essential, or candidate for demotion.
