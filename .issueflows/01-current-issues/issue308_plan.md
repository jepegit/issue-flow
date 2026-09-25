# Plan — Issue #308: publish on success

## Goal

Issues carrying a configurable **publish** label auto-drive a version bump
(default **patch**) and a **post-merge GitHub release** (`gh release create`),
with label payloads that can name a bump level or an explicit version — and a
stop-and-ask path when the explicit version is not a sensible next release.

## Constraints

- Mirror existing label-flow knobs (`label_flows` / `yolo_label` / `ops_label`):
  render-time bake into skills via `issue-flow update`; no agent-side
  `config.toml` freestyle.
- Reuse `versionplan` + `iflow-version-bump` / HISTORY promote; do not invent a
  second bump arithmetic.
- Static (uv) projects still bump **in the close PR** so the version lands on
  `main` before the tag; the GitHub *release* is what happens after merge
  (matches the issue wording and `docs/developing.md`).
- Tag-derived projects: plan the tag at close (existing behaviour); create the
  GitHub release after merge (extend beyond “tag only”).
- **Templates first** — edit `src/issue_flow/templates/`, then re-render this
  repo with `issue-flow update` where self-hosted skills need the new text.
- Ops path stays no-PR / no-publish.

### Prior art

- Label routing pattern: `.issueflows/04-designs-and-guides/label-driven-flows.md`
  (`label_flows`, `yolo_label`, `ops_label`); pick/close/yolo templates.
- Config resolve: `config.py` / `modes.py` (`resolve_yolo_label`,
  `resolve_ops_label`, `DEFAULT_*`).
- Version math: `versionplan.py` + `issue-flow agent version-plan`.
- Close bump + HISTORY promote: `iflow_close` / `iflow_version_bump` /
  `iflow_history_update` templates.
- Post-merge tag offer: `iflow_cleanup` Phase A (tag-derived only today);
  yolo close step 9 planned-tag create.
- Toolbox: `verify_scaffold.py` already asserts label-driven yolo routing —
  extend for publish markers after scaffold.

## Approach

1. **Config**
   - Add `publish_label` (default `"publish"`) under `[issueflow]`, same
     precedence as `yolo_label` (toml / env `ISSUEFLOW_PUBLISH_LABEL` / default).
   - Still gated by `label_flows`. Document in config docs table +
     `label-driven-flows.md`.

2. **Label payload grammar** (case-insensitive; strip whitespace)
   - Exact match `{{ publish_label }}` → bump level **`patch`**.
   - `{{ publish_label }}:<level>` where `<level>` ∈ versionplan `LEVELS`
     (`patch`, `minor`, `major`, `stable`, `alpha`, `beta`, `rc`, `post`,
     `dev`) → that level.
   - `{{ publish_label }}:<version>` where `<version>` parses as PEP440-ish
     via `versionplan.parse_version` (optional leading `v`) → **explicit
     target version**.
   - Multiple matching labels: prefer the most specific (explicit version >
     level > bare); if two conflict, **stop and ask**.

3. **CLI fast path** — `issue-flow agent publish-intent [--issue N] [--json]`
   (or read labels from stdin / flags): returns
   `{matched, kind: level|version|none, level?, target_version?,
   planned_from_default?, logical: bool, suggestion?, notes[]}`.
   - For explicit versions: compare to current (`version-plan` current) and to
     the single-level bumps (patch/minor/major/…). Mark `logical` true when
     the target equals one of those planned results (or equals current+chosen
     channel). When false, fill `suggestion` with the default patch plan and
     any closer single-level match; agent **must ask** before bumping.

4. **Close integration** (`iflow-close` / yolo)
   - After resolving focus issue labels: if publish intent matches and not
     `ops`, treat as an implicit bump request at the resolved level / version
     (same step 2 as a bump token). Explicit `bump <level>` on the command
     line wins over the label when both present (announce).
   - Illogical explicit version → **stop** (even under yolo): show suggestion,
     wait for user (`patch` / `minor` / … / accept target / abort).
   - Record `Publish label: …` + planned version on `issue<N>_status.md`.

5. **Post-merge release** (the “publishing” the issue asks for)
   - **Yolo close step 9** (after ff pull on default): if this issue had
     publish intent, run `gh release create "v<version>" --generate-notes`
     (tag style from versionplan / existing tag convention). For tag-derived
     strategy this replaces/extends the planned-tag push with a full GitHub
     release when publish is set.
   - **`/iflow-cleanup` Phase A**: same offer/auto under the consolidated
     confirm when status/HISTORY shows a publish-planned version whose
     GitHub release is missing (covers non-yolo merges). Prefer create when
     publish was recorded; do not invent releases for ordinary bumps without
     the label.
   - Creating the GitHub release starts `publish.yml` (PyPI) for this repo;
     other projects may only get a tag+notes — that is fine.

6. **Precedence with other labels**
   - `ops` wins over publish (no PR → no release).
   - `yolo` + publish: yolo chain runs; publish supplies the bump + post-merge
     release (no extra pick routing).
   - No new pick routing skill — publish is a **close/cleanup** concern, not
     a different work mode.

7. **Docs / design**
   - Extend `label-driven-flows.md` with a “Publish on success” section.
   - Short note in `docs/how-to/` or command-reference close section +
     configuration table row.
   - HISTORY bullet on close of this issue.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/modes.py` | `DEFAULT_PUBLISH_LABEL`, read/write `publish_label` |
| `src/issue_flow/config.py` | `resolve_publish_label`, env + render context |
| `src/issue_flow/config_ops.py` | key spec for `config set` |
| `src/issue_flow/versionplan.py` or new small module | parse publish label payload; logical-version check |
| `src/issue_flow/agent.py` + `cli.py` | `agent publish-intent` |
| `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` | label → bump; post-merge release (yolo) |
| `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2` | release create when publish-planned |
| `src/issue_flow/templates/skills/iflow_version_bump/SKILL.md.j2` | optional cross-link |
| Rules / AGENTS / config docs templates | document `publish_label` |
| `.issueflows/04-designs-and-guides/label-driven-flows.md` | decision record |
| `tests/` | unit tests for label parse + logical check; config resolve; scaffold marker if needed |
| `.issueflows/00-tools/verify_scaffold.py` | assert publish_label rendered when relevant |

## Test strategy

- `uv run pytest` — new unit tests for payload grammar and `logical` /
  `suggestion` cases (e.g. current `0.5.11` + `publish:0.9.0` → not logical,
  suggest `0.5.12`; `publish:minor` → `0.6.0`; bare `publish` → patch).
- Config round-trip for `publish_label` (modes / resolve).
- Template/contract tests if this repo already greps skill text for
  `yolo_label` / `ops_label` — add `publish_label` markers the same way.
- `uv run ruff check src/ tests/`.
- Optional: `uv run .issueflows/00-tools/verify_scaffold.py` after template
  changes.

## Open questions

1. **Label name default:** `publish` (recommended) vs `release`?
2. **Payload separator:** `publish:minor` / `publish:0.6.0` (recommended) vs
   separate labels (`publish-minor`) only?
3. **Illogical explicit version under yolo:** always stop-and-ask
   (recommended, per issue) vs auto-fall-back to patch?
4. **Non-yolo close:** auto-bump from label without asking when
   `confirm_version_bump` is true, or still one confirm that pre-fills the
   level from the label? **Recommend:** treat label as an explicit bump
   request (no extra “do you want to bump?”), still ask only when the
   version is illogical.

Default answers for Accept unless you override: **`publish`**, **colon
payloads**, **stop-and-ask on illogical**, **label counts as bump request**.
