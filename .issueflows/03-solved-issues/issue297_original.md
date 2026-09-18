# Issue #297: Opt-in discover of .issueflows/ trees

Source: https://github.com/jepegit/issue-flow/issues/297

## Original issue text

### Problem / context

Epic #269 forbids a default whole-disk git scan. Registering many local scaffolds today is one `issue-flow register` per root.

### Spec

Add `issue-flow register --discover [START]` (START default = cwd): walk for directories that already contain the project's issueflows dir (bounded depth, no symlink escape), print the candidate list, write only after one confirm (or `--yes` in tests). Never run from `update --all` / `init` / `workspace update`. Missing / locked roots stay skip-and-report. Relative START is resolved; discovered roots stored absolute. Docs in `docs/cli.md` + `user-global-config.md` (strike “scanning is Later”). Tests: tmp tree with two scaffolds + one decoy; only scaffolds register; depth cap respected.

### Goal

`register --discover` adds only confirmed `.issueflows/` roots; `update --all` still never walks the disk.

### Model

default

### Depends on

#287

Part of epic #269.
