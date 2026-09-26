"""``issue_flow.__version__`` must track the installed package (issue #386).

A hard-coded ``__version__`` silently went stale for a dozen releases and every
rendered skill carried the wrong ``issue-flow-version`` stamp, so drift between
CLI and skills could never be detected.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

import issue_flow

_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


@pytest.mark.essential
def test_version_comes_from_package_metadata() -> None:
    declared = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))["project"][
        "version"
    ]
    assert issue_flow.__version__ == declared
    assert not re.search(
        r'__version__\s*=\s*"\d', Path(issue_flow.__file__).read_text(encoding="utf-8")
    ), "__version__ must be resolved from importlib.metadata, not hard-coded"
