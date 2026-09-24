# Status — Issue #342

- [x] Done

## What's done

- Rewrote unversioned page URLs to `/en/latest/…` in `docs/llms.txt`, `README.md`, and the `iflow-init` command and skill templates, plus the workflow-doc template. Re-rendered `docs/issue-workflow.md` and `.cursor/skills/iflow-init`.
- `zensical.toml` `site_url` → `https://issue-flow.readthedocs.io/en/latest/`.
- Kept the bare root URL and `/llms.txt`; both return 200.
- Updated the URL assertions in `tests/test_init.py` and `tests/test_templating.py`.
- New essential test `tests/test_doc_links.py` (scans README, `docs/` and templates). Confirmed it fails on the old tree. Added a registry row.
- curl: every rewritten URL returns 200. Full suite: 855 passed.

## Remaining work

- None.
