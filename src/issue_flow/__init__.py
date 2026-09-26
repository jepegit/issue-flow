"""issue-flow: Agents should behave. Let them follow the issue flow."""

from importlib.metadata import PackageNotFoundError, version as _package_version


def _resolve_version() -> str:
    """Read the installed package version so skill stamps match the CLI.

    A hardcoded string drifted from ``pyproject.toml`` (issue #386): every
    scaffolded skill claimed ``0.4.2a4`` while the CLI reported ``0.5.13``.
    """
    try:
        return _package_version("issue-flow")
    except PackageNotFoundError:  # pragma: no cover - source tree without install
        return "0.0.0+unknown"


__version__ = _resolve_version()
