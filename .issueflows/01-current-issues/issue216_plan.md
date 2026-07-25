# Plan — Issue #216: possible bug in gitutils

## Goal

Make `gitutils` subprocess wrappers robust on Windows when `gh`/`git` emit
non-cp1252 bytes (UTF-8 issue bodies), and stop skills from teaching the invalid
`gh repo view --repo …` flag so agents stop hitting that footgun.

## Constraints

- Keep the existing degrade-to-`None` contract from
  [agentic-cli.md](.issueflows/04-designs-and-guides/agentic-cli.md): missing
  tools / failed commands return `None`, never raise into CLI callers.
- No `shell=True`. Keep argv-list style.
- Templates under `src/issue_flow/templates/` are source of truth; do not
  hand-edit only the already-rendered `.cursor/` copies.
- Scope stays Windows encoding + skill guidance; no broader `gh` API rewrite.

### Prior art

- `issue_flow.gitutils._run` / `_stdout` — sole subprocess capture path for
  agent `git`/`gh` helpers; currently `text=True` with **no** `encoding` /
  `errors` (locale default → cp1252 on the reporter’s Windows machine).
- `issue_flow.graphify` — same `subprocess.run(..., text=True)` pattern but
  not on the capture hot path; leave alone unless we want a tiny mirror later.
- `tests/test_gitutils.py` + `_fake_runner` — monkeypatches `subprocess.run`;
  extend for encoding kwargs + `stdout is None` defense.
- Templates already say “always `gh … --repo <owner/repo>`” in
  `_resolve_project_root.md.j2` / multi-repo docs — correct for most `gh`
  commands, **wrong** for `gh repo view` (positional repo only). Concrete bug
  in `skills/iflow_cleanup/SKILL.md.j2`: `gh repo view --repo <owner/repo> …`.

## Approach

1. **Diagnose (confirmed from stack):**
   - Primary: `subprocess.run(..., text=True)` on Windows decodes with the
     locale (`cp1252`). `gh issue view --json` can return UTF-8 bytes that
     fail (`UnicodeDecodeError` in `_readerthread`).
   - Secondary: after that failure, `CompletedProcess.stdout` can be `None`
     while `_run` still returns a process object → `_stdout` does
     `result.stdout.strip()` → `AttributeError` (the user-visible crash in
     `agent capture`).
   - Separate agent footgun (comment): `gh repo view --repo …` is invalid;
     form is `gh repo view <owner/repo> --json …`.

2. **Fix `_run`:** pass `encoding="utf-8"` and `errors="replace"` with
   `text=True` (or equivalent bytes+decode). Prefer `replace` over hard-fail
   so one weird byte never kills capture; JSON parse already returns `None`
   on garbage.

3. **Harden `_stdout` and stderr readers:** if `result.stdout` (or `.stderr`
   where stripped for errors) is `None`, treat as failure (`None` / fallback
   message) — never call `.strip()` on `None`.

4. **Skill / docs correction (same PR — comment asked for it):**
   - Fix `iflow_cleanup` skill template: `gh repo view <owner/repo> --json …`.
   - Narrow the blanket resolve-root line: most `gh` commands use
     `--repo <owner/repo>`; **`gh repo view` is the exception** (positional).
   - Short design note in
     `.issueflows/04-designs-and-guides/` (or a paragraph on
     `agentic-cli.md` / multi-repo doc) so the exception stays documented.
   - Re-run / note that `issue-flow update` refreshes rendered skills in
     dogfooded/target projects; this repo’s `.cursor/` copies refresh via
     the usual update path when we want them in sync.

5. **Tests:** unit-test that `_run` passes `encoding="utf-8"` (and
   `errors="replace"`) into `subprocess.run`; unit-test that `_stdout`
   returns `None` when `stdout` is `None` even if `returncode == 0`.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/gitutils.py` | UTF-8 decode in `_run`; None-safe `_stdout` / error-message helpers |
| `tests/test_gitutils.py` | Encoding kwargs + None-stdout coverage |
| `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2` | Fix `gh repo view` argv |
| `src/issue_flow/templates/skills/_resolve_project_root.md.j2` | Document `repo view` positional exception |
| `src/issue_flow/templates/commands/…` only if they copy the bad `--repo` on `repo view` | Mirror fix if present |
| `.issueflows/04-designs-and-guides/` (agentic-cli or multi-repo / new short note) | Record encoding + `gh repo view` exception |
| Optionally refresh this repo’s rendered `.cursor/skills/iflow-cleanup/SKILL.md` via `issue-flow update` | Keep dogfood skills consistent |

## Test strategy

```bash
uv run pytest tests/test_gitutils.py
uv run ruff check src/issue_flow/gitutils.py tests/test_gitutils.py
```

Optional smoke: `uv run issue-flow agent capture <N>` against a known UTF-8-heavy
issue body (if available) — not required if unit tests pin the contract.

## Open questions

1. **`errors=` policy:** prefer `replace` (keep going) vs `strict` (return
   `None` / surface failure)? **Recommendation: `replace`** — matches
   “best-effort wrappers” and avoids killing capture on one bad glyph.
2. **Skill fix in this PR?** Comment explicitly wants agent guidance fixed.
   **Recommendation: yes, same PR** (cleanup template + resolve-root nuance).
   Say **Revise** if you want encoding-only and a follow-up issue for skills.
