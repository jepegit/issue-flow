"""Read/write the opt-in epic session file (issue #333).

``epic_session.md`` lives in ``01-current-issues/`` beside ``auto_status.md``.
It is not an ``issue<N>_*`` group, so sweep/doctor ignore it. v1 only
recognises ``mode: one-and-ask``; any other mode is treated as missing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

EPIC_SESSION_FILENAME = "epic_session.md"
MODE_ONE_AND_ASK = "one-and-ask"
KNOWN_MODES = frozenset({MODE_ONE_AND_ASK})

_KEY_RE = re.compile(r"^(epic|mode)\s*:\s*(.+?)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class EpicSession:
    """Parsed contents of ``epic_session.md``."""

    epic: int
    mode: str

    def as_dict(self) -> dict[str, int | str]:
        return {"epic": self.epic, "mode": self.mode}


def session_path(current_dir: Path) -> Path:
    """Path to ``epic_session.md`` under a current-issues folder."""
    return current_dir / EPIC_SESSION_FILENAME


def read_epic_session(current_dir: Path) -> EpicSession | None:
    """Return the session, or ``None`` if missing / invalid / unknown mode."""
    path = session_path(current_dir)
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        match = _KEY_RE.match(line.strip())
        if match is None:
            continue
        parsed[match.group(1).lower()] = match.group(2).strip()
    raw_epic = parsed.get("epic")
    raw_mode = parsed.get("mode")
    if raw_epic is None or raw_mode is None:
        return None
    try:
        epic = int(raw_epic)
    except ValueError:
        return None
    if epic < 1:
        return None
    mode = raw_mode.lower()
    if mode not in KNOWN_MODES:
        return None
    return EpicSession(epic=epic, mode=mode)


def write_epic_session(
    current_dir: Path,
    epic: int,
    mode: str = MODE_ONE_AND_ASK,
) -> Path:
    """Write a two-line session file. Rejects unknown modes."""
    normalized = mode.strip().lower()
    if normalized not in KNOWN_MODES:
        raise ValueError(f"unknown epic session mode: {mode!r}")
    if epic < 1:
        raise ValueError(f"epic must be a positive issue number, got {epic}")
    current_dir.mkdir(parents=True, exist_ok=True)
    path = session_path(current_dir)
    path.write_text(f"epic: {epic}\nmode: {normalized}\n", encoding="utf-8")
    return path


def clear_epic_session(current_dir: Path) -> bool:
    """Delete the session file. Return True if a file was removed."""
    path = session_path(current_dir)
    if not path.is_file():
        return False
    path.unlink()
    return True
