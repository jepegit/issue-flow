# Label-driven flows (yolo label)

**Context.** Issue #106: typing slash commands for small issues is tedious;
GitHub labels already carry intent.

**Decision.**

- Two `[issueflow]` config keys, mirroring the `caveman_default` pattern
  (persisted `config.toml` > `ISSUEFLOW_*` env > default; re-render on
  `issue-flow update`): `label_flows` (default `true`) and `yolo_label`
  (default `"yolo"`).
- The hook lives in `/iflow-pick` only: a picked issue carrying the yolo label
  is routed through `/iflow-yolo`, with pick's confirmation folded together
  with yolo's consolidated confirm (one prompt total). `/iflow-init` stays
  untouched.
- Yolo's close step closes the loop via a `yolo` token on `/iflow-close`:
  changelog bullet written without a confirm prompt, PR merged with
  `gh pr merge --squash` (fallback `--squash --auto` when branch protection or
  pending checks block it; `draft` skips the merge), then default-branch
  switch + `git pull --ff-only`. Branch deletion stays in `/iflow-cleanup`.

**Alternatives considered.**

- Always `gh pr merge --auto` — rejected: on repos without required checks the
  merge would silently rely on GitHub state; immediate `--squash` with `--auto`
  fallback is more deterministic.
- Runtime reading of `config.toml` by the agent — rejected: baking values at
  render time matches every other knob and keeps commands self-contained.

**Link.** Issue #106, `issue106_plan.md` (archived with the issue group).
