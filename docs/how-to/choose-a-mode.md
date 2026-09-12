---
title: Choose a mode
---

# Choose a mode

## Goal

Pick which command surface `issue-flow init` installs, and how chatty the
lifecycle is.

## Steps

1. Decide the fit:

   | Mode | Fit |
   | --- | --- |
   | `novice` | Learning the loop; stop-and-ask defaults; no yolo/epic/auto |
   | `simple` | Markdown-only lifecycle; no PR automation |
   | `standard` | Full surface (default) |

2. Scaffold or switch:

   ```bash
   issue-flow init --mode novice    # first install
   issue-flow init --mode standard  # expand later
   ```

3. Mode is stored in `.issueflows/config.toml` as `[issueflow].mode`.
   `issue-flow update` honours it; it does not silently change the mode.
4. Tune knobs (`auto_plan`, `label_flows`, …) in that same file, then
   `issue-flow update` so skills re-render.

`novice` also seeds stop-and-ask settings on a **new** `config.toml`; an
existing config keeps your knobs when you only change the mode surface.

## Related

- [Configuration — Modes](../configuration.md#modes)
- [Getting started](../getting-started.md)
- [Create and run epics](epics.md) — needs a mode that includes epic (not novice)
