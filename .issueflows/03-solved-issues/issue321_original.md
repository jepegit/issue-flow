# Issue #321: Tighten pr-ready when required flags are omitted; CI on 3.12–3.14

Source: https://github.com/jepegit/issue-flow/issues/321

## Original issue text

### Problem / context

On #320, `issue-flow agent pr-ready` exited 0 (`ready`) while `test (3.11/3.12/3.13)` were still pending. GitHub omitted `isRequired` on the rollup; #317 treated that like optional noise when `mergeStateStatus=UNSTABLE`. Had to fall back to `gh pr checks --watch`.

CI still matrices 3.11 / 3.12 / 3.13. We want 3.12 / 3.13 / 3.14.

### Spec

1. **`pr-ready` omitted-required path.** If no check has `isRequired: true` or `false` (flag omitted): any pending/queued check → `pending`; any failure → `blocked`. Ignore pending/failing only when `isRequired` is **explicitly** `false`. `UNSTABLE` + `MERGEABLE` + omitted-required pending must not be `ready`. Keep: explicit required pass + explicit optional pending/fail → `ready`.
2. **CI / support floor.** `.github/workflows/ci.yml` matrix → `3.12`, `3.13`, `3.14`. Bump `requires-python` to `>=3.12`; classifiers drop 3.11, add 3.14. Align README / AGENTS.md / docs that still say 3.11+. Dev pin in `.python-version` stays 3.13 unless we decide otherwise. `publish.yml` can stay on 3.13.

### Acceptance criteria

- Unit test: UNSTABLE + MERGEABLE + omitted-required in-progress check → `pending`, exit 1.
- Existing optional-only (Cursor Approval `isRequired: false`) + required success → still `ready`.
- CI job names on a PR are `test (3.12)` / `(3.13)` / `(3.14)`; no 3.11 job.
- Package metadata claims 3.12+ only.

### Out of scope

- Changing yolo’s `gh pr merge` / `gh pr checks --watch` sequence.
- Moving the dev pin to 3.14.
