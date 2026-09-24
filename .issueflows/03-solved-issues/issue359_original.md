# Issue #359: docs: reorder the configuration page around common changes

Source: https://github.com/jepegit/issue-flow/issues/359

## Original issue text

## Context and spec

Final-review finding for epic #341 (goal part 4; review §7). `docs/configuration.md` (~440 lines) has these problems:

- it opens with the four-layer precedence model, user-global paths per OS, and registry details;
- the `config add` paragraph lists ~35 keys in one sentence;
- it refers to internal issue numbers ("issues #281 / #285, epic #269").

Change:

- Start with **Common changes**: a short table of the knobs people actually touch (`mode`, `auto_plan`, `worktree_first`, `caveman_default`, `grill_me_default`, `label_flows`, `pr_merge_method`, `noob`), each with an `issue-flow config set …` example and the reminder to run `issue-flow update`.
- Then a **full knob table** (key · type · default · effect · modes · env var). Generate it from code if that's feasible, so it can't drift. Otherwise add a test that every key `config add` writes appears in the table.
- Move precedence, user-global config and the registry to a "How settings are resolved" section near the end.
- Replace issue-number references with plain explanations (footnotes are fine).

**Goal:** the page starts with Common changes, every `config.toml` key appears exactly once in the full table (checked by a test), and the prose has no bare issue-number references.

**Model:** deep

Depends on: #348

Part of epic #341.
