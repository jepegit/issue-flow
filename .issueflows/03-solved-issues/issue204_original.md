# Issue #204: Gate next epoch on clear queue

Source: https://github.com/jepegit/issue-flow/issues/204

## Original issue text

## Context

Part of epic #169 (advanced auto mode). Stage 2 — Adversarial inter-epoch gate.

## Spec

`/iflow-auto` must not start stage `k+1` while stage `k` has open published issues or open inter-epoch blockers (reuse `issue-flow agent queue` / `epic-status` blockers).

## Acceptance criteria

- epic-status/queue based gate covered by tests or deterministic CLI checks
- Design doc updated

## Depends on

- #202

Part of epic #169.
