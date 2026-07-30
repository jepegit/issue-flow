# Plan — Issue #231: Add badges to readme

## Goal

Add PyPI, documentation, and downloads badges near the top of `README.md`.

## Approach

Place a badge row under the H1: PyPI version (shields.io), Read the Docs, and the Pepy downloads badge from the issue body. Keep existing prose; link targets match current docs/PyPI URLs.

## Files to touch

- `README.md` — badge row under title

## Test strategy

No code change — visual/markdown only. `uv run pytest` still run for yolo gate.
