# Status: #321 Tighten pr-ready when required flags are omitted; CI on 3.12–3.14

- [x] Done

## What's done

- Classify: a check blocks unless `isRequired is False` (omitted counts).
- Test: UNSTABLE + omitted in-progress → `pending`.
- CI matrix 3.12 / 3.13 / 3.14; `requires-python` >=3.12; classifiers +
  README / AGENTS.md / this-project.md; design note #321.
- HISTORY bullet under Unreleased.

## Remaining work

- None.
