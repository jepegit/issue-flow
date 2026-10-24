# Status: issue #410

- [x] Done

## What's done

- **Plan.** Accepted on 2026-10-24, including the ratchet test and the one-PR approach.
- **Negation pass** over the 26 `iflow_*/<mode>.md.j2` mode files, counted with the word-bounded, case-insensitive regex `do not|don't|never|must not`:
  - Hits went from **204 to 48**: 113 converted, 43 removed, 48 kept. The issue's 195 came from a looser count.
  - Mode-file words went from 20,067 to 19,655, and no file grew.
  - The kept count equals the remaining count in every file, checked file by file.
  - Kept hits are guardrails paired with a positive target, plus 4 descriptive uses:
    - destructive git (`-D`, `--force`, `--admin`, the default branch);
    - split confirms (A1/A2, Phase B);
    - silent picks or creates;
    - merge, push and PR scope;
    - `HISTORY.md`;
    - no auto-run of `/iflow-cleanup`;
    - pinned guardrails, such as "never tag an issue-branch commit".

  Per file (hits: converted / removed / kept):

  | Mode file | Hits | Converted | Removed | Kept |
  | --- | --- | --- | --- | --- |
  | `iflow_issue/epic` | 22 | 15 | 5 | 2 |
  | `iflow_close/changelog` | 17 | 10 | 4 | 3 |
  | `iflow_run/cycle` | 17 | 10 | 3 | 4 |
  | `iflow_run/auto` | 15 | 11 | 2 | 2 |
  | `iflow_run/drive` | 14 | 9 | 3 | 2 |
  | `iflow_close/version` | 12 | 8 | 2 | 2 |
  | `iflow_pick/comments` | 10 | 6 | 4 | 0 |
  | `iflow_setup/harness` | 9 | 7 | 1 | 1 |
  | `iflow_run/yolo` | 9 | 4 | 1 | 4 (1 descriptive) |
  | `iflow_issue/split` | 9 | 5 | 3 | 1 |
  | `iflow_pick/capture` | 7 | 4 | 2 | 1 |
  | `iflow_status/doctor` | 7 | 4 | 3 | 0 |
  | `iflow_cleanup/archive` | 7 | 4 | 1 | 2 |
  | `iflow_issue/review` | 6 | 5 | 1 | 0 |
  | `iflow_issue/fix` | 5 | 2 | 1 | 2 |
  | `iflow_issue/new` | 5 | 1 | 2 | 2 |
  | `iflow_status/graph` | 5 | 3 | 1 | 1 |
  | `iflow_cleanup/prs` | 5 | 2 | 0 | 3 |
  | `iflow_cleanup/workspace` | 5 | 0 | 2 | 3 |
  | `iflow_close/merge` | 5 | 1 | 0 | 4 (1 descriptive) |
  | `iflow_cleanup/github` | 4 | 1 | 0 | 3 |
  | `iflow_close/ops` | 3 | 0 | 1 | 2 |
  | `iflow_close/ci` | 2 | 1 | 1 | 0 |
  | `iflow_cleanup/classify` | 2 | 0 | 0 | 2 (both descriptive) |
  | `iflow_close/sync` | 1 | 0 | 0 | 1 |
  | `iflow_status/git` | 1 | 0 | 0 | 1 |
  | **Total** | **204** | **113** | **43** | **48** |

  A few non-counted `Do **not**` phrases on touched lines were rephrased too: `extract`, the how-to command order, and the epoch gate.
- **Tests:**
  - New ratchet test, `test_command_surface.py::test_mode_file_prohibitions_do_not_creep_back` (cap 48). It fails at 47.
  - Three pins moved to the positive wording: `test_init.py` (parallel refuse, Reuse the original consolidated confirm) and `test_templating.py` (`never edit, stage, or create`).
- **Re-rendered** `.cursor/skills/**` with `issue-flow update`.
- **Docs:**
  - The `skills-and-styles.md` #268 decision record marks #410 done, with the counts.
  - `test-registry.md` has a row for the ratchet.

## Verification

- `uv run pytest`: 968 passed.
- `uv run ruff check src/ tests/`: clean. `tests/test_command_surface.py` already had format drift before this change and was left alone.
- `uv run issue-flow doctor`: exit 0, no `skill_spec_*` findings.
- `uv run .issueflows/00-tools/verify_scaffold.py`: all checks passed.

## Remaining work

- None. Closed via `/iflow-close` on 2026-10-24 (`ruff format` also normalized whitespace drift in three test files).
