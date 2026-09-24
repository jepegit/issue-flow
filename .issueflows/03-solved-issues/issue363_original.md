# Issue #363: docs: add an annotated sample session

Source: https://github.com/jepegit/issue-flow/issues/363

## Original issue text

## Context and spec

Final-review finding for epic #341 (acceptance criterion "sample session"; review §11). The docs describe the steps but never show what the agent actually prints, so "stops for your confirmation" stays abstract.

Add an annotated transcript, as a new how-to or a section of Getting started, covering: `iflow pick` → choose → `iflow plan` (show a short example `issue<N>_plan.md`) → **Accept** → `iflow build` → `iflow close` (show the PR/HISTORY summary) → `iflow cleanup`. Use admonitions to explain each confirmation point. Base it on a real run in a throwaway repo. Trim it, but don't invent output.

**Goal:** a published page shows one full issue from pick to cleanup, with an example plan file and the confirmation points labelled. It is linked from Getting started.

**Model:** deep

Depends on: #348

Part of epic #341.
