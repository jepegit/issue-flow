# Project brief scaffold

Context: issue #53 — add a generated project-summary document that agents and
humans can use for quick repo orientation.

## Decision

`this-project.md` lives at `.issueflows/04-designs-and-guides/this-project.md`
and is user-owned durable memory. `issue-flow init` and `issue-flow update`
create it from `src/issue_flow/templates/docs/this-project.md.j2` only when the
file is missing; they never overwrite existing content, including when
`init --force` is used.

The brief is deliberately not part of `build_manifest()`. Manifest outputs are
package-owned scaffold files and `run_update` refreshes them with `force=True`.
The project brief follows the special "ensure" pattern used for other
user-preserving outputs instead.

## Alternatives considered

- Put the brief in `build_manifest()` and rely on `init` skipping existing files:
  rejected because `run_update` overwrites manifest files.
- Manage a marker-delimited block inside the brief: rejected because the whole
  file should be freely hand-editable, not partly package-owned.
- Autofill from README / package metadata in v1: deferred; placeholders are
  predictable and avoid surprising generated claims.
