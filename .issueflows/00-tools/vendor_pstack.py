"""Vendor the curated pstack skills into issue-flow's skill templates.

Repo-internal helper (not shipped to users). pstack is Lauren Tan's (poteto)
MIT-licensed skills library that lives in ``cursor/plugins`` under
``pstack/``. issue-flow ships a curated subset of its single-file skills as
``src/issue_flow/templates/skills/pstack_<name>/SKILL.md.j2`` so a project can
opt in via ``[issueflow].pstack_skills`` (see docs/configuration.md).

The bodies are vendored **verbatim** (wrapped in ``{% raw %}`` so Jinja never
touches them) with a single provenance comment inserted right after the YAML
frontmatter. Re-running this script against a newer upstream is therefore a
plain diff review, not a rewrite.

What it does:

1. sparse-clones ``https://github.com/cursor/plugins`` (only ``pstack/``),
2. reads the plugin version from ``pstack/.cursor-plugin/plugin.json`` and the
   upstream short SHA,
3. for every name in ``CURATED`` (kept in sync with
   ``issue_flow.templating.PSTACK_SKILL_NAMES``) writes the ``SKILL.md.j2``
   template,
4. refreshes ``templates/skills/_pstack_LICENSE.txt``.

Usage (from the repo root):

    uv run .issueflows/00-tools/vendor_pstack.py            # rewrite templates
    uv run .issueflows/00-tools/vendor_pstack.py --check    # exit 1 on drift
    uv run .issueflows/00-tools/vendor_pstack.py --ref <sha-or-branch>

Requires ``git`` and network access.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_SKILLS = REPO_ROOT / "src" / "issue_flow" / "templates" / "skills"
LICENSE_OUT = TEMPLATES_SKILLS / "_pstack_LICENSE.txt"

UPSTREAM_URL = "https://github.com/cursor/plugins.git"
UPSTREAM_SUBDIR = "pstack"

# Upstream skill folder names that issue-flow vendors. Keep in sync with
# ``PSTACK_SKILL_NAMES`` in ``src/issue_flow/templating.py``.
CURATED: tuple[str, ...] = (
    "unslop",
    "tdd",
    "blast-radius",
    "technical-writing",
    "bro",
    "principle-prove-it-works",
    "principle-subtract-before-you-add",
    "principle-fix-root-causes",
    "principle-test-behavior-not-implementation",
)


def _stem(name: str) -> str:
    return "pstack_" + name.replace("-", "_")


def _clone(ref: str | None) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="pstack-vendor-"))
    subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--depth",
            "1",
            "--filter=blob:none",
            "--sparse",
            *(["--branch", ref] if ref else []),
            UPSTREAM_URL,
            str(tmp / "plugins"),
        ],
        check=True,
    )
    repo = tmp / "plugins"
    subprocess.run(
        ["git", "-C", str(repo), "sparse-checkout", "set", UPSTREAM_SUBDIR],
        check=True,
    )
    return repo


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("upstream SKILL.md has no YAML frontmatter")
    closing = text.find("\n---\n", 4)
    if closing == -1:
        raise ValueError("upstream SKILL.md frontmatter is not closed")
    end = closing + len("\n---\n")
    return text[:end], text[end:]


def render_template(upstream_text: str, version: str, sha: str) -> str:
    frontmatter, body = _split_frontmatter(upstream_text)
    provenance = (
        f"<!-- vendored verbatim from cursor/plugins pstack v{version} @ {sha} (MIT); "
        "re-sync with .issueflows/00-tools/vendor_pstack.py -->\n"
    )
    return (
        frontmatter + provenance + "{% raw %}" + body.rstrip("\n") + "\n{% endraw %}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--check", action="store_true", help="report drift, write nothing"
    )
    parser.add_argument("--ref", default=None, help="upstream branch/tag to clone")
    args = parser.parse_args()

    repo = _clone(args.ref)
    try:
        pstack = repo / UPSTREAM_SUBDIR
        sha = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        version = json.loads(
            (pstack / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8")
        )["version"]
        print(f"upstream pstack v{version} @ {sha}")

        outputs: dict[Path, str] = {}
        for name in CURATED:
            src = pstack / "skills" / name / "SKILL.md"
            if not src.is_file():
                print(
                    f"error: upstream skill {name!r} not found at {src}",
                    file=sys.stderr,
                )
                return 1
            extra = [
                p
                for p in (pstack / "skills" / name).rglob("*")
                if p.is_file() and p != src
            ]
            if extra:
                rel = ", ".join(
                    str(p.relative_to(pstack / "skills" / name)) for p in extra
                )
                print(
                    f"error: {name!r} is no longer single-file upstream ({rel}); "
                    "issue-flow only vendors single-file skills",
                    file=sys.stderr,
                )
                return 1
            outputs[TEMPLATES_SKILLS / _stem(name) / "SKILL.md.j2"] = render_template(
                src.read_text(encoding="utf-8"), version, sha
            )
        outputs[LICENSE_OUT] = (pstack / "LICENSE").read_text(encoding="utf-8")

        drift = 0
        for path, content in outputs.items():
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            rel = path.relative_to(REPO_ROOT)
            if current == content:
                print(f"  ok      {rel}")
                continue
            drift += 1
            if args.check:
                print(f"  DRIFT   {rel}")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"  wrote   {rel}")

        if args.check and drift:
            print(f"{drift} vendored file(s) differ from upstream", file=sys.stderr)
            return 1
        return 0
    finally:
        shutil.rmtree(repo.parent, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
