"""Tests for issue_flow.step_profiles."""

from __future__ import annotations

from pathlib import Path

from issue_flow.step_profiles import (
    PACKAGED_DEFAULTS,
    enrich_render_context,
    resolve_all,
    skill_stem_for_template,
)


def _write_config(tmp_path: Path, body: str) -> Path:
    cfg = tmp_path / ".issueflows" / "config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(body, encoding="utf-8")
    return cfg


def test_packaged_defaults_cover_lifecycle_skills() -> None:
    assert PACKAGED_DEFAULTS["iflow_init"] == "economy"
    assert PACKAGED_DEFAULTS["iflow_plan"] == "reasoning"
    assert PACKAGED_DEFAULTS["iflow_yolo"] == "reasoning"
    assert PACKAGED_DEFAULTS["iflow_auto"] == "reasoning"


def test_project_override_wins(tmp_path: Path) -> None:
    cfg = _write_config(
        tmp_path,
        '[issueflow]\n\n[issueflow.step_profiles]\niflow_init = "reasoning"\n',
    )
    merged = resolve_all(cfg)
    assert merged["iflow_init"] == "reasoning"
    assert merged["iflow_close"] == "economy"


def test_skill_stem_for_template_maps_commands() -> None:
    assert skill_stem_for_template("skills/iflow_plan/SKILL.md.j2") == "iflow_plan"
    assert skill_stem_for_template("commands/iflow-plan.md.j2") == "iflow_plan"
    assert skill_stem_for_template("commands/iflow.md.j2") == "iflow_iflow"
    assert skill_stem_for_template("skills/caveman/SKILL.md.j2") is None
    assert skill_stem_for_template("skills/gh_ci/SKILL.md.j2") is None


def test_enrich_render_context_sets_step_profile() -> None:
    base = {
        "step_profiles": PACKAGED_DEFAULTS,
        "step_directives": True,
        "editor": "cursor",
    }
    ctx = enrich_render_context(base, "skills/iflow_plan/SKILL.md.j2")
    assert ctx["step_profile"] == "reasoning"
