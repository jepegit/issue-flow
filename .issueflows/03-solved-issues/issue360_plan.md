# Plan — Issue #360: docs: add a troubleshooting page

(Epic #341 stage 4, via /iflow-drive run 2 → auto → cycle; yolo chain, auto-confirmed.)

## Goal

The page is in the nav, covers the listed symptoms, is linked from Getting started, the How-to index and Concepts, and the link check passes.

## Approach

- `docs/how-to/troubleshooting.md`: symptom → cause → fix for the 8 symptoms in the issue, plus "PR became CONFLICTING" (→ `iflow pr-sync`).
- Every command it suggests was checked against the CLI (`uv tool update-shell`, `issue-flow doctor --fix`, `agent default-sync`, `config show --global`). `update --editor claude` was tested and does add a missing editor tree to an existing project.
- Nav: "Troubleshooting" as the last entry under How-to guides. Links from Getting started (Where to go next), the How-to index (new "Something went wrong?" section) and Concepts.

## Test strategy

Link check + pytest.
