"""Scaffold a throwaway project and verify the rendered issue-flow surfaces.

Repo-internal helper (not shipped to users). It exercises the CLI end-to-end:
create a temp dir, ``git init`` it, run ``issue-flow init`` from this repo's
source, and assert that the rendered skills and the ``AGENTS.md`` rule body
contain (or omit) the expected markers. It then flips config knobs in the
throwaway's ``.issueflows/config.toml``, re-runs ``issue-flow update``, and
re-checks.

The expected file set is derived from ``issue_flow.templating`` (every default
skill router plus its mode files, and no retired skill folder or command file),
so a surface change in the templates moves the expectations with it. Markers
point at the router or mode file that carries them since the #406 merge.

Built-in check groups:

1. **defaults** — every skill router and mode file is rendered for each editor
   and no retired surface is; the pick router carries the yolo / ops label
   lanes; ``close`` splits into ``merge.md`` (``--squash --auto``),
   ``ops.md``, and ``version.md`` (publish label); ``run/yolo.md`` chains
   ``/iflow-close yolo``; build carries the early draft PR; ``AGENTS.md``
   carries the label-routing line.
2. **label_flows = false** — the label lanes, the publish-label section, and
   the rule's label-routing line disappear after ``issue-flow update``.
3. **yolo_label = "fast-track"** — a custom label is interpolated into the
   pick router and the rule.
3b. **ops_label = "ship-it"** — custom ops label rendered into the pick router.
4. **pstack_skills** — no ``skills/unslop`` etc. by default; setting
   ``pstack_skills = ["unslop", "tdd"]`` and re-running ``update`` renders the
   two vendored skills under their upstream folder names for every editor, the
   ``pstack`` rule bullet, and the membership-gated close/build nudges;
   emptying the list prunes them again (issue #249).
5. **novice mode** — a second throwaway scaffolded with ``--mode novice``
   installs the guided-setup surface, omits the hands-off/behavior skills,
   seeds the settings preset, and renders a rule that does not advertise
   commands the mode did not install.

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

from issue_flow.templating import (
    DEFAULT_SKILL_DIRS,
    RETIRED_COMMANDS,
    STEM_RENAMES,
    skill_output_name,
    skill_side_output_names,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Both editors are skills-first since #406 (no command files), so scaffolding
# both checks that the skill tree renders the same for each agent dir.
EDITORS = ("cursor", "claude")

PICK = "skills/iflow-pick/SKILL.md"
CLOSE = "skills/iflow-close/SKILL.md"
CLOSE_MERGE = "skills/iflow-close/merge.md"
CLOSE_OPS = "skills/iflow-close/ops.md"
CLOSE_VERSION = "skills/iflow-close/version.md"
BUILD = "skills/iflow-build/SKILL.md"
RUN_YOLO = "skills/iflow-run/yolo.md"
RULE = "AGENTS.md"

YOLO_LANE = "Fold the yolo confirm into the pick confirm"
OPS_LANE = "Fold the ops lane into the pick confirm"
RULE_LABELS = "Issue labels can route `/iflow-pick`"
PUBLISH_SECTION = "## Publish-on-success label"
UNSLOP_NUDGE = "*Offer* the `unslop` skill"

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


def _check_editors(
    project: Path, rel: str, needle: str, expect_present: bool = True
) -> None:
    """``_check`` the same skill-relative path under every editor's agent dir."""
    for e in EDITORS:
        _check(project / f".{e}" / rel, needle, expect_present, f".{e}/{rel}")


def _check_absent(surface: Path, label: str) -> None:
    if surface.exists():
        _failures.append(f"{label}: {surface} should not exist")
        print(f"  FAIL  {label}: unexpected file {surface}")
    else:
        print(f"  ok    {label}: {surface.name} absent")


def _check_present(surface: Path, label: str) -> None:
    if surface.is_file():
        print(f"  ok    {label}: installed")
    else:
        _failures.append(f"{label}: {surface} was not rendered")
        print(f"  FAIL  {label}: missing {surface}")


def _check_surface(project: Path, agent_dir: str) -> None:
    """Every default router + mode file present; no retired skill or command."""
    skills = project / agent_dir / "skills"
    for stem in DEFAULT_SKILL_DIRS:
        folder = skills / skill_output_name(stem)
        _check_present(folder / "SKILL.md", f"{agent_dir} {folder.name}")
        for side in sorted(skill_side_output_names(stem)):
            _check_present(folder / side, f"{agent_dir} {folder.name}/{side}")
    retired = {skill_output_name(old) for old in STEM_RENAMES}
    retired_present = sorted(name for name in retired if (skills / name).exists())
    if retired_present:
        _failures.append(f"{agent_dir}: retired skills rendered: {retired_present}")
        print(f"  FAIL  {agent_dir}: retired skills rendered: {retired_present}")
    else:
        print(f"  ok    {agent_dir}: no retired skill folder ({len(retired)} names)")
    commands = project / agent_dir / "commands"
    stale = sorted(
        name for name in RETIRED_COMMANDS if (commands / f"{name}.md").exists()
    )
    if stale:
        _failures.append(f"{agent_dir}: retired command files: {stale}")
        print(f"  FAIL  {agent_dir}: retired command files: {stale}")
    else:
        print(f"  ok    {agent_dir}: no retired command file")


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


def _verify_novice(keep: bool) -> None:
    """Scaffold a second throwaway with ``--mode novice`` and check the surface."""
    project = Path(tempfile.mkdtemp(prefix="issueflow-novice-"))
    print(f"\n[5/5] novice mode (throwaway: {project})")
    try:
        _run(["git", "init", "--quiet"], cwd=project)
        _issue_flow(project, "init", ".", "--skip-dep-check", "--mode", "novice")

        for rel in (
            ".cursor/skills/iflow-setup/SKILL.md",
            ".cursor/skills/iflow-pick/SKILL.md",
            ".cursor/skills/iflow-pick/capture.md",
            ".cursor/skills/iflow-plan/SKILL.md",
            ".cursor/skills/iflow-close/SKILL.md",
        ):
            _check_present(project / rel, f"novice {rel}")

        for rel in (
            ".cursor/skills/iflow-run/SKILL.md",
            ".cursor/skills/caveman/SKILL.md",
            ".cursor/skills/grill-me/SKILL.md",
        ):
            _check_absent(project / rel, "novice omits")

        cfg = project / ".issueflows" / "config.toml"
        _check(cfg, "auto_plan = false", True, "novice config")
        _check(cfg, 'skill_level = "basic"', True, "novice config")

        rule = project / RULE
        _check(rule, "| `iflow-setup` |", True, "novice rule")
        for absent in ("`iflow-run`", "/iflow-run", RULE_LABELS):
            _check(rule, absent, False, "novice rule")
    finally:
        if keep:
            print(f"  kept novice throwaway at {project}")
        else:
            _rmtree(project)


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
        rule = project / RULE

        print("\n[1/5] defaults (label_flows on, yolo_label = yolo)")
        for e in EDITORS:
            _check_surface(project, f".{e}")
        _check_editors(project, PICK, YOLO_LANE)
        _check_editors(project, PICK, OPS_LANE)
        _check_editors(project, PICK, "follow `yolo.md` in the `iflow-run` skill")
        _check_editors(project, PICK, "follow `ops.md` in the `iflow-close` skill")
        _check_editors(project, CLOSE, "`--draft` with the `draft` token")
        _check_editors(project, CLOSE_MERGE, "gh pr merge")
        _check_editors(project, CLOSE_MERGE, "--squash --auto")
        _check_editors(project, CLOSE_OPS, "Ops close path")
        _check_editors(project, CLOSE_OPS, "/iflow-close ops")
        _check_editors(project, CLOSE_VERSION, PUBLISH_SECTION)
        _check_editors(project, CLOSE_VERSION, "publish-intent")
        _check_editors(project, RUN_YOLO, "/iflow-close yolo")
        _check_editors(project, BUILD, "Early pull request")
        _check_editors(project, BUILD, "gh pr create --draft")
        _check(rule, RULE_LABELS, True, RULE)
        _check(rule, "`yolo` → `/iflow-run yolo`", True, RULE)

        print("\n[2/5] label_flows = false → routing text disappears")
        _set_config(project, label_flows=False)
        _issue_flow(project, "update", *editor_flags)
        _check_editors(project, PICK, YOLO_LANE, False)
        _check_editors(project, PICK, OPS_LANE, False)
        _check_editors(project, CLOSE_VERSION, PUBLISH_SECTION, False)
        _check(rule, RULE_LABELS, False, RULE)

        print('\n[3/5] yolo_label = "fast-track" → custom label rendered')
        _set_config(project, label_flows=True, yolo_label="fast-track")
        _issue_flow(project, "update", *editor_flags)
        _check_editors(project, PICK, YOLO_LANE)
        _check_editors(project, PICK, "**`fast-track` label**")
        _check(rule, "`fast-track` → `/iflow-run yolo`", True, RULE)

        print('\n[3b] ops_label = "ship-it" → custom ops label rendered')
        _set_config(project, label_flows=True, ops_label="ship-it")
        _issue_flow(project, "update", *editor_flags)
        _check_editors(project, PICK, OPS_LANE)
        _check_editors(project, PICK, "**`ship-it` label.**")

        print("\n[4/5] pstack_skills → vendored skills appear, then prune")
        for e in EDITORS:
            _check_absent(
                project / f".{e}/skills/unslop/SKILL.md", "pstack off by default"
            )
        _check(rule, "- **pstack**", False, "rule (pstack off)")
        _check_editors(project, CLOSE, UNSLOP_NUDGE, False)
        _set_config(project, pstack_skills=["unslop", "tdd"])
        _issue_flow(project, "update", *editor_flags)
        for e in EDITORS:
            unslop = project / f".{e}/skills/unslop/SKILL.md"
            _check(unslop, "name: unslop", True, f".{e} unslop")
            _check(
                unslop,
                "vendored verbatim from cursor/plugins pstack",
                True,
                f".{e} unslop",
            )
            _check(
                project / f".{e}/skills/tdd/SKILL.md", "name: tdd", True, f".{e} tdd"
            )
            _check_absent(
                project / f".{e}/skills/bro/SKILL.md", f".{e} bro not selected"
            )
        _check(rule, "- **pstack** (unslop, tdd)", True, "rule (pstack on)")
        _check_editors(project, CLOSE, UNSLOP_NUDGE)
        _check_editors(project, CLOSE, "`blast-radius` skill", False)
        _check_editors(project, BUILD, "TDD (pstack, optional)")
        _set_config(project, pstack_skills=[])
        _issue_flow(project, "update", *editor_flags)
        for e in EDITORS:
            _check_absent(
                project / f".{e}/skills/unslop/SKILL.md", f".{e} unslop pruned"
            )
            _check_absent(project / f".{e}/skills/tdd/SKILL.md", f".{e} tdd pruned")
        _check(rule, "- **pstack**", False, "rule (pstack off again)")
        _check_editors(project, CLOSE, UNSLOP_NUDGE, False)
    finally:
        if args.keep:
            print(f"\nkept throwaway project at {project}")
        else:
            _rmtree(project)

    _verify_novice(args.keep)

    if _failures:
        print(f"\n{len(_failures)} check(s) FAILED")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
