# Issue #203: Wire loop budget + ask UX into `/iflow-auto`

Source: https://github.com/jepegit/issue-flow/issues/203

## Original issue text

## Context

Part of epic #169 (advanced auto mode). Stage 2 — Adversarial inter-epoch gate.

## Spec

After each adversarial pass, increment loop counter; if issues remain open/reopened and counter < budget, re-queue those issues via cycle and re-run adversarial; when budget exhausted, **stop and ask** (accept current / grant N more loops / abort) per design doc; honour config + trailing overrides.

## Acceptance criteria

- Unit/contract tests or scaffold assertions for budget wording
- Manual scenario documented in design doc
- Honour `auto_adversarial_loops` and trailing `loops:<n>`

## Depends on

- #192
- #202

Part of epic #169.
