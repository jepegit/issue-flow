# Plan — #195 Stage 1 tests and HISTORY

## Goal

Close Stage 1 coverage gaps: pytest for knobs / epic markers / `/iflow-auto`
scaffold; docs for `auto_adversarial_loops`; HISTORY Unreleased bullet.

## Approach

1. Init integration test that scaffolds `iflow-auto` with stub + status tokens.
2. Assert `PACKAGED_DEFAULTS["iflow_auto"] == "reasoning"`.
3. Template tests: epic skill documents Goal/Model; env override for
   `auto_adversarial_loops`.
4. Document knob in `docs/configuration.md`; clear "later Stage 1" wording in
   design knobs table.
5. HISTORY Unreleased bullet for #195.

## Test strategy

`uv run pytest` + `uv run ruff check src/ tests/`.
