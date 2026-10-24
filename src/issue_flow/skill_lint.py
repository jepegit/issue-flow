"""Mechanical Agent Skills lint for skill directories (issue #268).

Checks a skill folder against the Agent Skills spec
(https://agentskills.io/specification) plus two authoring hints from
Anthropic's skill best practices. Pure functions: callers decide how to
report the findings (``issue-flow doctor`` maps them to ``DirtyFinding``).

No YAML dependency: :func:`parse_frontmatter` reads the shapes skills use in
practice (``key: value``, quoted scalars, ``>-`` / ``|`` blocks, and indented
mappings such as ``metadata:``, whose nested lines it skips).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

LINT_ERROR = "error"
LINT_WARN = "warn"
LINT_INFO = "info"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESCRIPTION_MAX = 1024
BODY_LINE_HINT = 500
SIDE_FILE_TOC_LINES = 100
_XML_TAG_RE = re.compile(r"</?[A-Za-z][\w-]*(\s[^<>]*)?/?>")
_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")
_TOC_RE = re.compile(r"^(#+\s*)?(\*\*)?contents\b", re.IGNORECASE | re.MULTILINE)

# Spec keys, then keys editors and issue-flow add. Anything else warns: a
# typo'd key is silently ignored by every harness.
KNOWN_KEYS = frozenset(
    {
        "name",
        "description",
        "license",
        "compatibility",
        "metadata",
        "allowed-tools",
        "disable-model-invocation",
        "user-invocable",
        "argument-hint",
        "model",
        "issue-flow-version",
    }
)


@dataclass(frozen=True)
class LintFinding:
    """One spec or authoring problem in a skill directory."""

    check: str
    severity: str
    path: Path
    message: str


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    """Return ``(frontmatter, body)`` or ``None`` when there is no block."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None
    closing = text.find("\n---\n", 3)
    if closing == -1:
        if text.endswith("\n---"):
            closing = len(text) - 4
        else:
            return None
    return text[4:closing], text[closing + 5 :]


def _scalar(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        return (
            inner.replace("''", "'") if value[0] == "'" else inner.replace('\\"', '"')
        )
    return value


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Parse the top-level keys of a ``SKILL.md`` frontmatter block.

    Returns ``None`` when the file has no ``---`` delimited block. Block
    scalars (``>-``, ``>``, ``|``, ``|-``) are joined: folded with spaces,
    literal with newlines. Nested mapping lines are dropped (the key maps to
    an empty string).
    """
    split = _split_frontmatter(text)
    if split is None:
        return None
    lines = split[0].split("\n")
    data: dict[str, str] = {}
    i = 0
    while i < len(lines):
        match = _KEY_RE.match(lines[i])
        if not match:
            i += 1
            continue
        key, rest = match.group(1), match.group(2).strip()
        i += 1
        block: list[str] = []
        while i < len(lines) and (
            lines[i].startswith((" ", "\t")) or not lines[i].strip()
        ):
            block.append(lines[i].strip())
            i += 1
        if rest[:1] in (">", "|"):
            joiner = "\n" if rest.startswith("|") else " "
            data[key] = joiner.join(part for part in block if part).strip()
        else:
            data[key] = _scalar(rest)
    return data


def _toc_missing(text: str) -> bool:
    return len(text.splitlines()) > SIDE_FILE_TOC_LINES and not _TOC_RE.search(text)


def lint_skill(skill_dir: Path) -> list[LintFinding]:
    """Lint one skill folder: ``SKILL.md`` frontmatter, body, side files."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [LintFinding("missing_skill_md", LINT_ERROR, skill_dir, "no SKILL.md")]
    text = skill_md.read_text(encoding="utf-8")
    split = _split_frontmatter(text)
    data = parse_frontmatter(text)
    if split is None or data is None:
        return [
            LintFinding(
                "missing_frontmatter",
                LINT_ERROR,
                skill_md,
                "SKILL.md has no --- frontmatter block",
            )
        ]

    findings: list[LintFinding] = []

    def add(check: str, severity: str, message: str, path: Path = skill_md) -> None:
        findings.append(LintFinding(check, severity, path, message))

    name = data.get("name", "")
    if not name:
        add("name", LINT_ERROR, "frontmatter has no name")
    elif len(name) > NAME_MAX or not NAME_RE.match(name):
        add(
            "name",
            LINT_ERROR,
            f"name {name!r} must be 1-{NAME_MAX} lowercase letters, digits and "
            "single hyphens, not starting or ending with a hyphen",
        )
    elif name != skill_dir.name:
        add(
            "name_dir_mismatch",
            LINT_ERROR,
            f"name {name!r} differs from folder {skill_dir.name!r}",
        )

    description = data.get("description", "")
    if not description:
        add("description", LINT_ERROR, "frontmatter has no description")
    else:
        if len(description) > DESCRIPTION_MAX:
            add(
                "description",
                LINT_ERROR,
                f"description is {len(description)} chars (max {DESCRIPTION_MAX})",
            )
        if _XML_TAG_RE.search(description):
            add("description", LINT_ERROR, "description contains an XML tag")

    for key in sorted(set(data) - KNOWN_KEYS):
        add("unknown_key", LINT_WARN, f"unknown frontmatter key {key!r}")

    body_lines = len(split[1].splitlines())
    if body_lines > BODY_LINE_HINT:
        add(
            "long_body",
            LINT_INFO,
            f"body is {body_lines} lines (hint: under {BODY_LINE_HINT})",
        )

    for side in sorted(skill_dir.glob("*.md")):
        if side.name == "SKILL.md":
            continue
        if _toc_missing(side.read_text(encoding="utf-8")):
            add(
                "side_file_toc",
                LINT_INFO,
                f"{side.name} is over {SIDE_FILE_TOC_LINES} lines without a Contents list",
                side,
            )
    return findings


def lint_skills_root(skills_root: Path) -> list[LintFinding]:
    """Lint every skill folder directly under ``skills_root``."""
    findings: list[LintFinding] = []
    for entry in sorted(skills_root.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            findings.extend(lint_skill(entry))
    return findings
