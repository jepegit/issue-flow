# Linguist `.gitattributes` (issue #168)

## Context

GitHub Linguist language stats can be skewed by non-library trees (especially
`graphify-out/graph.html` as HTML). issue-flow offers an optional managed
`.gitattributes` block so consumers can keep stats focused on library source.

## Decision

- Config key: `[issueflow].linguist_attributes` (default **`false`**, opt-in).
- Env fallback: `ISSUEFLOW_LINGUIST_ATTRIBUTES`.
- When true, `issue-flow init` / `update` append a marker-delimited block to
  root `.gitattributes` (same idempotent pattern as the editor `.gitignore`
  block). Existing user rules outside the markers are left alone.
- When false: do not write; do **not** strip an existing managed block.
- Shared path set is fixed/generic (issue #168 example); no per-project path
  discovery in v1.

## Alternatives considered

- Dogfood-only committed file with no user option — rejected; users hit the
  same Linguist skew with graphify / docs / `.issueflows/`.
- Default on — rejected; writing root git metadata is surprising for existing
  projects.
