# Plan — #298 Native Windows APPDATA tests

## Goal

win32 APPDATA paths have tests; WSL still ignores Windows home.

## Approach

Monkeypatch `sys.platform` + `APPDATA` / `HOME`. No `/mnt/c` lookup.
Short docs note. No Linux/WSL behavior change.
