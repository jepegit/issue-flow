# Plan — Issue #168: fix GitHub Linguist skew

## Goal

Stop GitHub Linguist from skewing language stats toward non-library trees
(`graphify-out/` HTML, docs, issue-tracking markdown), **and** give issue-flow
users the same fix as an **optional, config-gated** managed `.gitattributes`
block (on/off in `.issueflows/config.toml`).

## Answer to the revise ask

**Today: no.** There is no config key or scaffold path that writes
`.gitattributes`. Closest patterns to mirror:

| Precedent | Where | Behaviour |
|-----------|--------|-----------|
| Managed `.gitignore` editor block | [`ensure_editor_gitignore`](src/issue_flow/surfaces.py) | Begin/end markers; append once; skip if present |
| Bool toggles (`caveman_default`, `label_flows`, …) | `[issueflow]` in `config.toml` + `modes.read_*` / `Settings.resolve_*` | Persisted; env fallback; `config add` seeds keys |

So the feature **should** be a new `[issueflow]` flag + managed-file writer,
not a one-off dogfood-only file with no user path.

## Constraints

- Templates / `modes.py` / `config.py` / `surfaces.py` / `init`+`update` are
  the source of truth for scaffold behaviour (edit those, not already-rendered
  copies in this repo’s `.cursor/`).
- Writing into a user’s root `.gitattributes` is invasive → **default OFF
  (opt-in)** unless you override in Open questions.
- Never clobber user content outside the managed marker block.
- Keep Linguist path rules **generic** (same set as the issue example); do not
  invent per-project path discovery in v1.
- Follow existing resolution order: `config.toml` > env > default.

### Prior art

- [`ensure_editor_gitignore`](src/issue_flow/surfaces.py) — marker-block pattern
  to copy for `.gitattributes`.
- Config plumbing for bools: `modes.read_*` / `write_default_config` /
  `Settings.resolve_*` / `config add` / docs in `docs/configuration.md`.
- Toolbox / graph: nothing Linguist-specific (`- None beyond the above`).

## Approach

### 1. Config flag

Add under `[issueflow]`:

```toml
linguist_attributes = false   # default: off (opt-in)
```

- Env fallback: `ISSUEFLOW_LINGUIST_ATTRIBUTES` (same shape as other bools).
- Wire through: `modes.read_linguist_attributes`, `Settings.resolve_linguist_attributes`,
  `write_default_config` / `_commented_issueflow_table`, `config add` seed list,
  docs table in `docs/configuration.md`.

### 2. Managed `.gitattributes` writer

New helper (next to gitignore ensure), e.g. `ensure_linguist_gitattributes(project_root) -> bool`:

- Markers: `# BEGIN issue-flow linguist` / `# END issue-flow linguist`
- Block body ≈ issue example:

  ```
  graphify-out/** linguist-generated
  docs/** linguist-documentation
  tests/** linguist-documentation
  .issueflows/** linguist-documentation
  dev/** linguist-documentation
  scripts/** linguist-documentation
  .aliases     text eol=lf
  *.sh         text eol=lf
  *.lock       text eol=lf
  ```

- If file missing → create with block.
- If markers already present → **skip** (idempotent; matches gitignore).
- If file exists without markers → **append** block (do not rewrite user’s rules).
- When flag is **false**: do **not** write; do **not** strip an existing managed
  block (safe leave-alone; stripping is a follow-up if wanted).

### 3. Hook into scaffold refresh

- On `issue-flow init` and `issue-flow update`: if
  `resolve_linguist_attributes(project_root)` is true → call the ensure helper.
- No new CLI flag required for v1 (config + `update` is enough); optional
  `init`/`update` mention in docs only.

### 4. Dogfood this repo

- Set `linguist_attributes = true` in this repo’s `.issueflows/config.toml`.
- Commit the resulting root `.gitattributes` (so Linguist is fixed even before
  someone runs `update`).
- Re-run `issue-flow update` (or the ensure path) so behaviour matches what
  users get.

### 5. Docs

- Short section in `docs/configuration.md` (toggle + re-run `update`).
- One line in `docs/developing.md` or graphify docs only if useful; not required.

## Files to touch

| Path | Change |
|------|--------|
| `src/issue_flow/modes.py` | read/write + default for `linguist_attributes` |
| `src/issue_flow/config.py` | `resolve_linguist_attributes` + seed/context dicts |
| `src/issue_flow/surfaces.py` (or small sibling) | `ensure_linguist_gitattributes` |
| `src/issue_flow/init.py` (+ update path) | call ensure when flag true |
| `src/issue_flow/agent.py` / `cli.py` | config-add help / guide mention if other keys listed |
| `docs/configuration.md` | document key + default |
| `.issueflows/config.toml` | `linguist_attributes = true` (dogfood) |
| `.gitattributes` | managed block (dogfood commit) |
| `tests/test_modes.py`, `tests/test_config.py`, new/extend surface/init tests | flag round-trip + ensure idempotence + init/update honour flag |

## Test strategy

- `uv run pytest`
- Unit: config resolve default/`true`/`false`; `write_default_config` seeds key.
- Unit: ensure helper creates / appends / skips when markers present; no-op when
  not invoked.
- Integration-ish: `init`/`update` with flag on writes `.gitattributes`; flag off
  leaves tree without it.
- Manual: after merge, GitHub language bar for this repo should drop HTML skew.

## Scope check

Still one PR: config plumbing + one ensure helper + dogfood file. Not inventing
per-project path customization or Linguist `vendor` overrides.

## Open questions

1. **Default OFF (opt-in)** — recommended, because root `.gitattributes` touches
   git metadata for every consumer. Prefer default **ON**?
2. **Turning the flag off later** — plan **leaves** an existing managed block in
   place (no auto-delete). Want `update` to **strip** the managed block when
   false?
3. **`tests/**` as `linguist-documentation`** — still following the issue
   example for the shared template. Prefer tests counted as code in the
   shipped block?
