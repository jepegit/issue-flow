# Issue #193: Epic plan markers — Stage Goal + issue Goal/Model

Source: https://github.com/jepegit/issue-flow/issues/193

## Original issue text

## Context

Part of epic #169 (advanced auto mode). Stage 1 — Design + orchestrator skeleton.

## Spec

Extend `/iflow-epic` plan structure (skill + `epicplan.py` as needed) so each Stage has an explicit **Goal** line/paragraph and each Issue Spec includes **Goal:** and **Model: deep|fast|default** (publish copies Model into the GitHub issue body).

## Acceptance criteria

- Parser/tests accept the markers
- `publish` bodies include Goal + Model
- Old plans without markers still parse
- Skill docs updated

## Depends on

#191

Part of epic #169.
