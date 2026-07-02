"""Scaffold a throwaway project and verify the rendered issue-flow surfaces.

Repo-internal helper (not shipped to users). It exercises the CLI end-to-end:
create a temp dir, ``git init`` it, run ``issue-flow init`` from this repo's
source, and assert that the rendered skills / commands / rules contain (or
omit) the expected markers. It then flips config knobs in the throwaway's
``.issueflows/config.toml``, re-runs ``issue-flow update``, and re-checks.

Built-in check groups:

1. **defaults** — label-driven yolo routing is rendered (``label_flows``
   defaults to true), the close surfaces carry the hands-off ``yolo`` token
   (``gh pr merge --squash`` + ``--auto`` fallback), and the yolo surfaces
   chain ``/iflow-close yolo``.
2. **label_flows = false** — the label routing text disappears from the pick
   surfaces after ``issue-flow update``.
3. **yolo_label = "fast-track"** — a custom label is interpolated into the
   pick surfaces after ``issue-flow update``.

Usage (from the repo root):

    uv run .issueflows/00-tools/verify_scaffold.py [--keep]

``--keep`` leaves the throwaway project on disk (its path is printed) for
manual inspection. Exit code 0 = all checks passed, 1 = at least one failed.
"""

from __future__ import annotations

import argparse
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import tomlkit

REPO_ROOT = Path(__file__).resolve().parents[2]

# Rendered surfaces to inspect. Cursor is skills-first (no command files);
# Claude renders the command templates, so scaffolding both covers every
# template family touched by the label-flow work.
EDITORS = ("cursor", "claude")

PICK_SURFACES = (
    ".cursor/skills/iflow-pick/SKILL.md",
    ".claude/commands/iflow-pick.md",
)
CLOSE_SURFACES = (
    ".cursor/skills/iflow-close/SKILL.md",
    ".claude/commands/iflow-close.md",
)
YOLO_SURFACES = (
    ".cursor/skills/iflow-yolo/SKILL.md",
    ".claude/commands/iflow-yolo.md",
)

LABEL_ROUTING_MARKER = "Label-driven yolo flow"

_failures: list[str] = []


def _run(args: list[str], cwd: Path) -> None:
    result = subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        sys.exit(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"{result.stdout}\n{result.stderr}"
        )


def _issue_flow(project: Path, *cli_args: str) -> None:
    """Run the issue-flow CLI from this repo's source against ``project``."""
    _run(
        ["uv", "run", "--project", str(REPO_ROOT), "issue-flow", *cli_args],
        cwd=project,
    )


def _check(surface: Path, needle: str, expect_present: bool, label: str) -> None:
    text = surface.read_text(encoding="utf-8") if surface.is_file() else None
    if text is None:
        _failures.append(f"{label}: {surface} was not rendered")
        print(f"  FAIL  {label}: missing file {surface.name}")
        return
    found = needle in text
    if found == expect_present:
        verb = "contains" if expect_present else "omits"
        print(f"  ok    {label}: {verb} {needle!r}")
    else:
        verb = "should contain" if expect_present else "should not contain"
        _failures.append(f"{label}: {surface} {verb} {needle!r}")
        print(f"  FAIL  {label}: {verb} {needle!r}")


def _set_config(project: Path, **issueflow_keys: object) -> None:
    """Upsert ``[issueflow]`` keys (plain ``init`` does not create config.toml)."""
    cfg_path = project / ".issueflows" / "config.toml"
    if cfg_path.is_file():
        doc = tomlkit.parse(cfg_path.read_text(encoding="utf-8"))
    else:
        doc = tomlkit.document()
    section = doc.get("issueflow")
    if not isinstance(section, dict):
        section = tomlkit.table()
        doc["issueflow"] = section
    for key, value in issueflow_keys.items():
        section[key] = value
    cfg_path.write_text(tomlkit.dumps(doc), encoding="utf-8")


def _rmtree(path: Path) -> None:
    """rmtree that clears the read-only bit .git objects carry on Windows."""

    def _onerror(func, p, _exc):  # noqa: ANN001
        Path(p).chmod(stat.S_IWRITE)
        func(p)

    shutil.rmtree(path, onerror=_onerror)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--keep",
        action="store_true",
        help="leave the throwaway project on disk for manual inspection",
    )
    args = parser.parse_args()

    project = Path(tempfile.mkdtemp(prefix="issueflow-verify-"))
    print(f"throwaway project: {project}")

    try:
        _run(["git", "init", "--quiet"], cwd=project)
        editor_flags = [flag for e in EDITORS for flag in ("-e", e)]
        _issue_flow(project, "init", ".", "--skip-dep-check", *editor_flags)

        print("\n[1/3] defaults (label_flows on, yolo_label = yolo)")
        for rel in PICK_SURFACES:
            _check(project / rel, LABEL_ROUTING_MARKER, True, rel)
            _check(project / rel, "`yolo`", True, rel)
        for rel in CLOSE_SURFACES:
            _check(project / rel, "gh pr merge", True, rel)
            _check(project / rel, "--squash --auto", True, rel)
        for rel in YOLO_SURFACES:
            _check(project / rel, "/iflow-close yolo", True, rel)

        print("\n[2/3] label_flows = false → routing text disappears")
        _set_config(project, label_flows=False)
        _issue_flow(project, "update", *editor_flags)
        for rel in PICK_SURFACES:
            _check(project / rel, LABEL_ROUTING_MARKER, False, rel)

        print('\n[3/3] yolo_label = "fast-track" → custom label rendered')
        _set_config(project, label_flows=True, yolo_label="fast-track")
        _issue_flow(project, "update", *editor_flags)
        for rel in PICK_SURFACES:
            _check(project / rel, LABEL_ROUTING_MARKER, True, rel)
            _check(project / rel, "fast-track", True, rel)
    finally:
        if args.keep:
            print(f"\nkept throwaway project at {project}")
        else:
            _rmtree(project)

    if _failures:
        print(f"\n{len(_failures)} check(s) FAILED")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
