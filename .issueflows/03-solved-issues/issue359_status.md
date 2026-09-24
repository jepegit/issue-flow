# Status — Issue #359

- [x] Done

## What's done

- `docs/configuration.md` reordered: intro → Common changes → All settings (38 keys) → topical sections → How settings are resolved.
- Removed the issue-number references (#281, #282, #285, #286, #287, #293, #328, epic #269, #23/#101).
- `tests/test_doc_configuration.py` (3 tests; the key-coverage one is essential). All three fail on the old page and pass on the new one. Registry rows added.
- Link check: 0 errors (the inbound anchors #modes, #skill-levels, #pstack-skills, #per-repo-lock, #label-driven-flows and #creating-configtoml all still resolve). `uv run pytest` passes.

## Deviations from the spec

- No per-key "modes" column (see plan).

## Remaining work

- None.
