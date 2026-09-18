# Plan — #297 Opt-in discover of `.issueflows/` trees

## Goal

`register --discover` adds only confirmed `.issueflows/` roots; `update --all` still never walks the disk.

## Approach

Walk START (default cwd) for dirs that contain the issueflows folder.
Bounded depth, no symlink follow. Print candidates; write after confirm
or `--yes`. Not hooked from `init` / `update --all` / `workspace update`.

## Tests

Two scaffolds + decoy; depth cap; `--yes` registers only scaffolds.
