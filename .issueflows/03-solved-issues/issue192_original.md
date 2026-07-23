# Issue #192: Config knobs for adversarial loop budget

Source: https://github.com/jepegit/issue-flow/issues/192

## Original issue text

## Context

Part of epic #169 (advanced auto mode). Stage 1 — Design + orchestrator skeleton.

## Spec

Add `[issueflow]` key (name per design doc, e.g. `auto_adversarial_loops`, default `2`) with env override, bake into templates at `issue-flow update`, document in config guide / knobs table. Trailing / wording overrides (e.g. `loops:5`) specified in design doc and rendered into the auto skill.

## Acceptance criteria

- Round-trip tests for resolve/seed/write
- Rendered skill mentions default and override
- `issue-flow update` bakes the value

## Depends on

#191

Part of epic #169.
