# Issue #298: Native Windows APPDATA tests (not a WSL bridge)

Source: https://github.com/jepegit/issue-flow/issues/298

## Original issue text

### Problem / context

The contract already says WSL uses the Linux home and a native Windows install is a **separate machine view** — do **not** read `%APPDATA%` / `%USERPROFILE%` from WSL Python. The `sys.platform == "win32"` branch exists; it is under-tested.

### Spec

Prove `os_config_home` / `user_config_dir` / editor global skills on the win32 branch with monkeypatched `sys.platform` + `APPDATA` / `USERPROFILE`, plus a short note in `docs/configuration.md` and both design docs. No `/mnt/c/Users/…` lookup. No change to Linux/WSL behaviour.

### Goal

win32 APPDATA paths have tests; WSL still ignores Windows home.

### Model

fast

### Depends on

#285

Part of epic #269.
