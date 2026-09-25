"""Upgrade the ``uv tool`` install of issue-flow, then refresh a project.

Used by ``issue-flow agent self-update`` (issue #382). The install step
replaces the on-PATH binary; the following ``issue-flow update`` is a
subprocess so the *new* templates are what get written.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Callable

from rich.console import Console

UV = "uv"
PACKAGE = "issue-flow"

Runner = Callable[..., subprocess.CompletedProcess[str]]


def _run(
    argv: list[str],
    cwd: Path | None = None,
    *,
    runner: Runner | None = None,
) -> subprocess.CompletedProcess[str] | None:
    run = runner or subprocess.run
    if shutil.which(argv[0]) is None:
        return None
    try:
        return run(
            argv,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, UnicodeError):
        return None


def parse_version_text(text: str) -> str | None:
    """Pull a version token from ``issue-flow --version`` output."""
    cleaned = text.strip()
    if not cleaned:
        return None
    first = cleaned.splitlines()[0].strip()
    for prefix in ("issue-flow, version ", "issue-flow "):
        if first.lower().startswith(prefix):
            first = first[len(prefix) :].strip()
            break
    return first or None


def receipt_is_local(data: dict[str, Any], raw: str = "") -> bool:
    """True when the uv-tool receipt is an editable or path install."""
    if "editable = true" in raw.lower():
        return True
    tool = data.get("tool")
    if not isinstance(tool, dict):
        return False
    reqs = tool.get("requirements")
    if not isinstance(reqs, list):
        return False
    for req in reqs:
        if not isinstance(req, dict):
            continue
        if req.get("editable") is True:
            return True
        if req.get("directory"):
            return True
        url = str(req.get("url") or "")
        if url.startswith("file:"):
            return True
        source = req.get("source")
        if isinstance(source, dict) and (
            source.get("editable") is True or source.get("directory")
        ):
            return True
    return False


def inspect_uv_tool(
    name: str = PACKAGE,
    *,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """Read the uv-tool receipt for ``name``.

    Returns ``installed``, ``editable`` (local/path/editable), ``receipt``,
    and ``notes``. Missing uv or a missing receipt is not an error — the
    install step can still create the tool.
    """
    notes: list[str] = []
    payload: dict[str, Any] = {
        "installed": False,
        "editable": False,
        "receipt": None,
        "notes": notes,
    }
    if shutil.which(UV) is None:
        notes.append("uv is not on PATH.")
        return payload

    listed = _run([UV, "tool", "dir"], runner=runner)
    if listed is None or listed.returncode != 0:
        notes.append("could not resolve `uv tool dir`.")
        return payload
    tool_dir = Path(listed.stdout.strip())
    receipt_path = tool_dir / name / "uv-receipt.toml"
    payload["receipt"] = str(receipt_path)
    if not receipt_path.is_file():
        notes.append(f"no uv-tool receipt at {receipt_path}.")
        return payload
    raw = receipt_path.read_text(encoding="utf-8")
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        notes.append(f"could not parse uv-tool receipt: {exc}")
        return payload
    payload["installed"] = True
    payload["editable"] = receipt_is_local(data, raw)
    return payload


def current_cli_version(*, runner: Runner | None = None) -> str | None:
    """Version of the ``issue-flow`` binary currently on PATH."""
    if shutil.which(PACKAGE) is None:
        return None
    result = _run([PACKAGE, "--version"], runner=runner)
    if result is None or result.returncode != 0:
        return None
    return parse_version_text(result.stdout or result.stderr)


def run_self_update(
    project_root: Path,
    console: Console,
    as_json: bool,
    *,
    runner: Runner | None = None,
) -> int:
    """Install ``issue-flow@latest`` via uv, then ``issue-flow update``.

    Skips (exit 0) when the current tool install is editable or a local
    path. Hard-fails (exit 1) when ``uv`` is missing or either step fails.
    """
    notes: list[str] = []
    payload: dict[str, Any] = {
        "ok": False,
        "action": "failed",
        "reason": None,
        "from_version": None,
        "to_version": None,
        "update_exit": None,
        "project_root": str(project_root.resolve()),
        "notes": notes,
    }

    def emit(exit_code: int) -> int:
        payload["ok"] = exit_code == 0
        if as_json:
            console.print_json(json.dumps(payload))
        else:
            _render_text(console, payload, exit_code)
        return exit_code

    if shutil.which(UV) is None:
        notes.append("uv is not on PATH.")
        payload["reason"] = "uv_unavailable"
        return emit(1)

    inspect = inspect_uv_tool(runner=runner)
    notes.extend(inspect.get("notes") or [])
    if inspect.get("editable"):
        notes.append(
            "refusing to replace an editable or path uv-tool install "
            "with PyPI latest. Re-run `uv tool install --force --editable .` "
            "from the checkout if dependencies changed."
        )
        payload["action"] = "skipped"
        payload["reason"] = "editable"
        payload["from_version"] = current_cli_version(runner=runner)
        return emit(0)

    payload["from_version"] = current_cli_version(runner=runner)
    install = _run(
        [UV, "tool", "install", f"{PACKAGE}@latest"],
        runner=runner,
    )
    if install is None:
        notes.append("could not spawn `uv tool install`.")
        payload["reason"] = "install_unspawnable"
        return emit(1)
    if install.returncode != 0:
        err = (install.stderr or install.stdout or "").strip()
        notes.append(err or f"uv tool install exited {install.returncode}.")
        payload["reason"] = "install_failed"
        return emit(1)

    payload["to_version"] = current_cli_version(runner=runner)
    update = _run(
        [PACKAGE, "update", str(project_root.resolve()), "--skip-dep-check"],
        cwd=project_root,
        runner=runner,
    )
    if update is None:
        notes.append("could not spawn `issue-flow update`.")
        payload["reason"] = "update_unspawnable"
        payload["action"] = "failed"
        return emit(1)
    payload["update_exit"] = update.returncode
    if update.returncode != 0:
        err = (update.stderr or update.stdout or "").strip()
        notes.append(err or f"issue-flow update exited {update.returncode}.")
        payload["reason"] = "update_failed"
        return emit(1)

    payload["action"] = "upgraded"
    payload["reason"] = None
    if payload["from_version"] and payload["to_version"] == payload["from_version"]:
        notes.append("already on latest; scaffold refreshed.")
    return emit(0)


def _render_text(console: Console, payload: dict[str, Any], exit_code: int) -> None:
    action = payload.get("action")
    from_v = payload.get("from_version") or "?"
    to_v = payload.get("to_version") or from_v
    if action == "skipped":
        console.print(
            f"[yellow]skipped[/yellow]  self-update ({payload.get('reason')}): {from_v}"
        )
    elif exit_code == 0:
        console.print(f"[green]ok[/green]  self-update {from_v} → {to_v}")
    else:
        console.print(
            f"[red]failed[/red]  self-update ({payload.get('reason')}): "
            f"{from_v} → {to_v}"
        )
    for note in payload.get("notes") or []:
        console.print(f"  [dim]{note}[/dim]")
