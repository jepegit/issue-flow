# Issue #267: chore: remote branch audit (2026-09-12)

Source: https://github.com/jepegit/issue-flow/issues/267

## Original issue text

## Remote branch audit

From `/iflow-cleanup github` on 2026-09-12 (`issue-flow agent branches`).

### Deletable
None — no remote heads were safe to delete. Squash-landed `265-howto-subchapters` was already gone from `origin` (likely auto-delete on merge of #266).

### Unique work (do not delete without review)

| Branch | Unique commits | Notes |
| --- | --- | --- |
| `140-agent-queue-cli` | 3 | No open/merged PR linked. Subjects: agent queue, epic-status, `/iflow-epic` publish + draft surface. |
| `cursor/163-github-branches-e2ca` | 5 | Merged PR #188 (2026-07-20) but tip still differs from `main`. |
| `cursor/gha-sync-issueflows-08d1` | 4 | Merged PR #160 (2026-07-13) but tip still differs from `main`. |

### Skipped
- `main` (default)

### Suggested follow-up
- Eyeball the three unique-work remotes; delete by hand only if the tip work is discarded or recovered elsewhere.
- Local `258-agent-name-issue-no-confirm` also has unique work after #259 — not a remote-audit item, but same hygiene class.
