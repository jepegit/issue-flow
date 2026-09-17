# Issue #276 plan

## Goal

`issue-flow update` (and `init --force` overwrite of an existing skill dir)
must not silently clobber a packaged output path that is not ours — symlink,
extra files, or content that drifted from our last write. Default: **warn +
skip**. `--force` still overwrites.

## Constraints

- No skillbook CLI. Name collision + filesystem shape is enough.
- Unchanged packaged skills must still refresh when templates change.
  Therefore **do not** treat “on-disk hash ≠ new render” as foreign — that
  would skip every stale-but-ours skill.
- User folders whose names are **not** in `SKILL_DIRS` output names stay
  untouched (`_prune_excluded_surfaces` already). #277 only reports them.
- Out of scope: #269 library, #268 lint, #277 scan (shipped).
- `skillbook-lessons.md` follow-up table already links #276.

### Prior art

- `write_manifest_files()` / `materialize_editor_profile()` in `surfaces.py`
  — `update` passes `force=True` (always overwrite). Hook ownership here,
  skill paths only (`<agent_dir>/skills/<name>/SKILL.md`).
- `init --force` already means overwrite existing manifest files; `update`
  has **no** `--force` today. Add one for foreign overwrite.
- `_prune_excluded_surfaces()` / `_prune_retired_files()` in `init.py` —
  `rmtree` packaged/retired names. Must **not** delete a foreign collision
  when the mode excludes that stem (same detector).
- `stamp_skill_version()` / `issue-flow-version` frontmatter — migration
  signal when no stamp file exists yet. Not a content hash.
- `packaged_skill_output_names()` (#277) — set of protected folder names.
- Canonical store `.issueflows/agent/manifest.json` — reuse that directory
  for stamps, not sidecars under `.cursor/skills/` (those get committed
  and look like extra files).
- Toolbox: no helper. Graph: `materialize_editor_profile` / `run_update`.

## Approach

**Policy (issue default):** warn + skip foreign skill dirs. `update --force`
and `init --force` overwrite them. No interactive confirm.

**“Ours” vs foreign** for a packaged skill directory:

Foreign if any of:

1. The dir or `SKILL.md` is a symlink.
2. Unexpected extra entries besides `SKILL.md` (packaged skills are
   single-file).
3. Stamp present and SHA-256 of `SKILL.md` (LF-normalized) ≠ stored hash.
4. No stamp, and `SKILL.md` lacks `issue-flow-version` (skillbook/user copy
   using our output name).

Ours otherwise: missing dir (fresh write); or regular `SKILL.md` + no extras
+ (stamp matches **or** no stamp + our version key). First `update` after
upgrade writes stamps; existing scaffolds keep updating.

**Cannot** compare to the *new* render hash — that would skip legitimate
template refreshes.

**Stamp store:** `.issueflows/agent/skill-stamps.json` keyed by repo-relative
skill dir (e.g. `.cursor/skills/iflow-plan`). Written only after a successful
ours (or `--force`) write. Never put stamp files inside editor skill dirs.

**Write path.** In `write_manifest_files`, before overwriting a skill
`SKILL.md`: if the parent dir is foreign and `overwrite_foreign` is false,
skip, warn with the relative path + reason. Non-skill manifest paths
unchanged. After a write, update the stamp.

**Prune path.** `_prune_excluded_surfaces` (and retired-skill rmtree): skip
foreign dirs; warn instead of delete.

**CLI.** `issue-flow update --force` / `-f`. `init --force` already exists
and becomes the foreign-overwrite switch on skill dirs too.

**Docs.** `docs/cli.md` update section; one line in `skillbook-lessons.md`
that #276 is the implementation (table already links).

## Files to touch

- `src/issue_flow/surfaces.py` — ownership check in `write_manifest_files`.
- `src/issue_flow/init.py` — `run_update(force=…)`; prune skips foreign.
- New small helper (same module or `src/issue_flow/skill_ownership.py`) —
  hash, classify, stamp read/write.
- `src/issue_flow/cli.py` — `update --force`.
- `tests/test_update.py` / `tests/test_init.py` — symlink, extra files,
  stamp mismatch skip; ours still refresh; `--force` overwrites; prune
  leaves foreign.
- `docs/cli.md` — document `--force` and skip behavior.

## Test strategy

`uv run pytest`. Throwaway tmp projects: seed a packaged `iflow-plan`, then
(1) symlink, (2) extra `notes.md`, (3) edit body after a stamp exists, (4)
plain stale ours (change template version / body) still overwrites. Assert
`--force` writes. Assert `doctor` unmanaged scan still only sees *other*
names (`my-notes`), not this path.

## Open questions

1. Confirm **warn + skip + `--force`** (recommended) vs warn + interactive
   confirm each path. Reply Accept to take the recommended policy.
