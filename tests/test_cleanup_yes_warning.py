"""issue-flow update warns when cleanup_yes_a2 is on (issue #388)."""

from __future__ import annotations

from pathlib import Path

from issue_flow.init import _warn_cleanup_yes_a2


def test_update_warns_when_cleanup_yes_a2(tmp_path: Path, capsys) -> None:
    flows = tmp_path / ".issueflows"
    flows.mkdir()
    (flows / "config.toml").write_text(
        "[issueflow]\ncleanup_yes_a2 = true\n", encoding="utf-8"
    )
    _warn_cleanup_yes_a2(tmp_path)
    out = capsys.readouterr().out
    assert "cleanup_yes_a2 is on" in out
    assert "git branch -D" in out


def test_update_silent_when_cleanup_yes_a2_off(tmp_path: Path, capsys) -> None:
    _warn_cleanup_yes_a2(tmp_path)
    assert capsys.readouterr().out.strip() == ""
