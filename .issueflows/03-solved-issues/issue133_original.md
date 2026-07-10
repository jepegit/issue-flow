# Issue #133: deterministic fast path

Source: https://github.com/jepegit/issue-flow/issues/133

## Original issue text

Follow up for #125 

Phase 2:  â€” a deterministic fast path: issue-flow agent version-plan [--bump LEVEL] --json returning {strategy, current_version, latest_tag, next_version, commands}. PEP 440 pre-release arithmetic (a2â†’a3, alphaâ†’beta promotion, dropping the pre-segment for stable) is exactly the mechanical-but-fiddly work LLMs fumble; uv version --dry-run already covers static projects but nothing covers tag projects. That would follow the same "CLI for facts, prompts for judgment" move as switchback.
