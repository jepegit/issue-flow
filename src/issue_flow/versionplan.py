"""Deterministic release-version planning (a pragmatic PEP 440 subset).

Backs ``issue-flow agent version-plan``: detect the project's release
strategy, read the current version (static ``[project] version`` or latest
git tag), and compute the next version for a requested bump level — the
mechanical, fiddly arithmetic (``a2`` → ``a3``, alpha → beta promotion,
dropping the pre-segment for ``stable``) that agents otherwise re-derive by
hand. Everything here is **read-only computation**: nothing edits
``pyproject.toml`` and nothing creates tags.

The parser covers the version shapes release tags actually use
(``v1.0.4a2``, ``0.4.1rc1``, ``2.0.0.post1``, ``0.5.0.dev3``); exotic PEP 440
forms (epochs, local versions) are deliberately out of scope and simply fail
to parse, which callers report instead of guessing.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

# Bump levels, in the canonical order they are applied when combined
# (so ``--bump alpha --bump minor`` means "minor, then alpha" -> 0.5.0a1).
LEVELS = ("major", "minor", "patch", "stable", "alpha", "beta", "rc", "post", "dev")

_PRE_LABELS = {"alpha": "a", "beta": "b", "rc": "rc"}
_PRE_RANK = {"a": 0, "b": 1, "rc": 2}
_PRE_NAMES = {"a": "alpha", "b": "beta", "rc": "rc"}

_VERSION_RE = re.compile(
    r"""^(?P<v>v)?
    (?P<release>\d+(?:\.\d+)*)
    (?:(?P<pre_l>a|b|rc)(?P<pre_n>\d+))?
    (?:\.post(?P<post>\d+))?
    (?:\.dev(?P<dev>\d+))?$""",
    re.VERBOSE,
)


@dataclass(frozen=True)
class Version:
    """A parsed version. ``v_prefix`` preserves the project's tag style."""

    release: tuple[int, ...]
    pre: tuple[str, int] | None = None
    post: int | None = None
    dev: int | None = None
    v_prefix: bool = False

    def formatted(self) -> str:
        text = ("v" if self.v_prefix else "") + ".".join(
            str(part) for part in self.release
        )
        if self.pre is not None:
            text += f"{self.pre[0]}{self.pre[1]}"
        if self.post is not None:
            text += f".post{self.post}"
        if self.dev is not None:
            text += f".dev{self.dev}"
        return text


def parse_version(text: str) -> Version | None:
    """Parse a version string / tag, or ``None`` when it doesn't fit."""
    match = _VERSION_RE.match(text.strip())
    if match is None:
        return None
    release = tuple(int(part) for part in match.group("release").split("."))
    pre = None
    if match.group("pre_l"):
        pre = (match.group("pre_l"), int(match.group("pre_n")))
    post = int(match.group("post")) if match.group("post") else None
    dev = int(match.group("dev")) if match.group("dev") else None
    return Version(
        release=release,
        pre=pre,
        post=post,
        dev=dev,
        v_prefix=match.group("v") is not None,
    )


def _bump_release(version: Version, index: int) -> Version:
    """Bump release component ``index`` (0=major), zeroing everything after."""
    release = list(version.release)
    while len(release) <= index:
        release.append(0)
    release[index] += 1
    for i in range(index + 1, len(release)):
        release[i] = 0
    # Normalise to at least three components so `patch` on "1.0" works.
    while len(release) < 3:
        release.append(0)
    return Version(release=tuple(release), v_prefix=version.v_prefix)


def bump(current: Version, levels: list[str]) -> tuple[Version | None, list[str]]:
    """Apply ``levels`` (canonical order) to ``current``.

    Returns ``(planned, notes)``; ``planned`` is ``None`` when the request is
    invalid (unknown level, pre-release demotion, unpaired ``dev``), with the
    reason in ``notes``.
    """
    notes: list[str] = []
    for level in levels:
        if level not in LEVELS:
            return None, [f"unknown bump level '{level}' (use: {', '.join(LEVELS)})"]

    ordered = sorted(levels, key=LEVELS.index)
    if ordered != levels:
        notes.append(f"levels applied in canonical order: {', '.join(ordered)}")

    version = current
    release_bumped = False
    for level in ordered:
        if level in ("major", "minor", "patch"):
            version = _bump_release(version, ("major", "minor", "patch").index(level))
            release_bumped = True
        elif level == "stable":
            version = replace(version, pre=None, dev=None)
        elif level in ("alpha", "beta", "rc"):
            label = _PRE_LABELS[level]
            if version.pre is not None:
                current_label, number = version.pre
                if current_label == label:
                    pre = (label, number + 1)
                elif _PRE_RANK[current_label] < _PRE_RANK[label]:
                    pre = (label, 1)
                else:
                    return None, [
                        f"cannot go from {_PRE_NAMES[current_label]} back to "
                        f"{level}: pre-release channels only move forward "
                        "(a -> b -> rc)."
                    ]
            elif release_bumped:
                pre = (label, 1)
            else:
                # Forward-moving choice: starting a pre-release series from a
                # stable version advances patch first (1.0.4 + alpha -> 1.0.5a1).
                version = _bump_release(version, 2)
                notes.append(
                    "current version is stable; advanced patch before starting "
                    f"the {level} series."
                )
                pre = (label, 1)
            version = replace(version, pre=pre, post=None, dev=None)
        elif level == "post":
            version = replace(version, post=(version.post or 0) + 1, dev=None)
        elif level == "dev":
            if version.dev is None and not release_bumped and len(ordered) == 1:
                return None, [
                    "bump 'dev' must be paired with another component (e.g. "
                    "patch + dev) unless the current version already has a "
                    ".devN segment."
                ]
            version = replace(version, dev=(version.dev or 0) + 1)
    return version, notes


def default_levels(current: Version) -> list[str]:
    """The pre-release-aware default when no level is given.

    Mirrors the iflow-version-bump skill: stay on the current pre-release
    channel; from a stable release, bump ``patch``.
    """
    if current.dev is not None:
        return ["dev"]
    if current.pre is not None:
        return [_PRE_NAMES[current.pre[0]]]
    return ["patch"]


# ---------------------------------------------------------------------------
# strategy detection
# ---------------------------------------------------------------------------

# Substrings that mark a tag-driven version backend in build requirements.
_TAG_BACKEND_HINTS = ("setuptools-scm", "setuptools_scm", "hatch-vcs", "versioningit")


def detect_strategy(project_root: Path) -> tuple[str, str, str | None]:
    """Detect the release strategy from ``pyproject.toml``.

    Returns ``(strategy, reason, static_version)`` where ``strategy`` is
    ``"uv"`` (static ``[project] version``), ``"tag"`` (dynamic version from a
    tag-driven backend), or ``"unknown"``.
    """
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        return "unknown", "no pyproject.toml found", None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return "unknown", "pyproject.toml could not be parsed", None

    project = data.get("project")
    project = project if isinstance(project, dict) else {}
    version = project.get("version")
    if isinstance(version, str):
        return "uv", "static [project] version in pyproject.toml", version

    dynamic = project.get("dynamic")
    if isinstance(dynamic, list) and "version" in dynamic:
        tool = data.get("tool")
        tool = tool if isinstance(tool, dict) else {}
        if "setuptools_scm" in tool:
            return "tag", "dynamic version via [tool.setuptools_scm]", None
        if "versioningit" in tool:
            return "tag", "dynamic version via [tool.versioningit]", None
        hatch_version = tool.get("hatch", {})
        if isinstance(hatch_version, dict):
            source = hatch_version.get("version", {})
            if isinstance(source, dict) and source.get("source") == "vcs":
                return "tag", "dynamic version via hatch-vcs", None
        requires = data.get("build-system", {})
        requires = requires.get("requires", []) if isinstance(requires, dict) else []
        joined = " ".join(str(req).lower() for req in requires)
        for hint in _TAG_BACKEND_HINTS:
            if hint in joined:
                return "tag", f"dynamic version via {hint} (build requires)", None
        return (
            "unknown",
            "dynamic [project] version with an unrecognized backend",
            None,
        )

    return "unknown", "no version information in pyproject.toml", None
