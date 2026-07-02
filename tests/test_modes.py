"""Tests for issue_flow.modes (mode registry, resolution, persistence)."""

from __future__ import annotations

from pathlib import Path

import pytest

from issue_flow import modes
from issue_flow.modes import (
    DEFAULT_LABEL_FLOWS,
    DEFAULT_MODE,
    DEFAULT_YOLO_LABEL,
    available_modes,
    config_path,
    read_active_mode,
    read_caveman_default,
    read_grill_me_default,
    read_label_flows,
    read_yolo_label,
    resolve_mode,
    write_active_mode,
    write_default_config,
)
from issue_flow.templating import COMMAND_NAMES, SKILL_DIRS


def test_default_mode_is_standard() -> None:
    assert DEFAULT_MODE == "standard"


def test_standard_includes_every_surface() -> None:
    mode = resolve_mode("standard")
    assert mode.skills == frozenset(SKILL_DIRS)
    assert mode.commands == frozenset(COMMAND_NAMES)


def test_simple_is_strict_subset() -> None:
    simple = resolve_mode("simple")
    assert simple.skills < frozenset(SKILL_DIRS)
    assert simple.commands < frozenset(COMMAND_NAMES)
    # Core markdown lifecycle is present.
    for stem in ("iflow_iflow", "iflow_init", "iflow_plan", "iflow_start", "iflow_pause"):
        assert stem in simple.skills
    # Heavy git/PR automation is excluded.
    for stem in ("iflow_close", "iflow_yolo", "iflow_fix", "iflow_graphify"):
        assert stem not in simple.skills


def test_caveman_in_standard_not_in_simple() -> None:
    """The caveman behavior skill ships in standard but is omitted by simple."""
    assert "caveman" in resolve_mode("standard").skills
    assert "caveman" not in resolve_mode("simple").skills


def test_unknown_mode_raises_with_known_list() -> None:
    with pytest.raises(ValueError) as exc:
        resolve_mode("bogus")
    msg = str(exc.value)
    assert "bogus" in msg
    assert "standard" in msg and "simple" in msg


def test_available_modes_lists_builtins() -> None:
    assert set(available_modes()) >= {"standard", "simple"}


def _write_config(tmp_path: Path, body: str) -> Path:
    cfg = config_path(tmp_path, ".issueflows")
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(body, encoding="utf-8")
    return cfg


def test_project_config_can_define_custom_mode_via_extends_add(tmp_path: Path) -> None:
    """Scenario 3: a project defines a custom mode that adds a packaged skill."""
    cfg = _write_config(
        tmp_path,
        "[issueflow]\nmode = \"mine\"\n\n"
        "[modes.mine]\nname = \"Mine\"\nextends = \"simple\"\n"
        'add = ["iflow_graphify"]\n',
    )
    mine = resolve_mode("mine", cfg)
    simple = resolve_mode("simple", cfg)
    assert mine.skills == simple.skills | {"iflow_graphify"}
    assert "mine" in available_modes(cfg)


def test_custom_mode_unknown_stem_raises(tmp_path: Path) -> None:
    cfg = _write_config(
        tmp_path,
        "[modes.broken]\nextends = \"standard\"\nadd = [\"does_not_exist\"]\n",
    )
    with pytest.raises(ValueError) as exc:
        resolve_mode("broken", cfg)
    assert "does_not_exist" in str(exc.value)


def test_project_config_can_override_builtin(tmp_path: Path) -> None:
    cfg = _write_config(
        tmp_path,
        '[modes.simple]\nname = "Tiny"\nskills = ["iflow_init"]\ncommands = ["iflow-init"]\n',
    )
    simple = resolve_mode("simple", cfg)
    assert simple.skills == frozenset({"iflow_init"})
    assert simple.name == "Tiny"


def test_extends_remove(tmp_path: Path) -> None:
    cfg = _write_config(
        tmp_path,
        '[modes.noyolo]\nextends = "standard"\nremove = ["iflow_yolo", "iflow-yolo"]\n',
    )
    mode = resolve_mode("noyolo", cfg)
    assert "iflow_yolo" not in mode.skills
    assert "iflow-yolo" not in mode.commands
    assert "iflow_init" in mode.skills


def test_circular_extends_raises(tmp_path: Path) -> None:
    cfg = _write_config(
        tmp_path,
        '[modes.a]\nextends = "b"\n\n[modes.b]\nextends = "a"\n',
    )
    with pytest.raises(ValueError) as exc:
        resolve_mode("a", cfg)
    assert "circular" in str(exc.value).lower()


def test_read_active_mode_missing_returns_none(tmp_path: Path) -> None:
    assert read_active_mode(config_path(tmp_path, ".issueflows")) is None


def test_write_active_mode_creates_file(tmp_path: Path) -> None:
    cfg = config_path(tmp_path, ".issueflows")
    write_active_mode(cfg, "simple")
    assert cfg.is_file()
    assert read_active_mode(cfg) == "simple"


def test_write_active_mode_preserves_user_modes_and_comments(tmp_path: Path) -> None:
    """Round-trip: updating the active mode keeps [modes.*] and comments intact."""
    cfg = _write_config(
        tmp_path,
        "# my project config\n\n[issueflow]\nmode = \"simple\"\n\n"
        "[modes.mine]\nextends = \"standard\"\nadd = [\"iflow_graphify\"]\n",
    )
    write_active_mode(cfg, "standard")
    text = cfg.read_text(encoding="utf-8")
    assert read_active_mode(cfg) == "standard"
    # User content survived the round-trip.
    assert "my project config" in text
    assert "[modes.mine]" in text
    assert "iflow_graphify" in text
    # The custom mode is still resolvable afterwards.
    assert "mine" in available_modes(cfg)


def test_persisted_config_beats_env_with_env_as_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Resolution order: persisted config.toml > ISSUEFLOW_MODE env > default."""
    from issue_flow.config import Settings

    settings = Settings()
    cfg = config_path(tmp_path, ".issueflows")

    # No persisted config yet: env acts as the fallback above the default.
    monkeypatch.setenv("ISSUEFLOW_MODE", "simple")
    assert settings.resolve_active_mode_id(tmp_path) == "simple"

    # Persisted (init-chosen) mode wins over a stray env var.
    write_active_mode(cfg, "standard")
    assert settings.resolve_active_mode_id(tmp_path) == "standard"

    # With neither env nor config, fall back to the default.
    monkeypatch.delenv("ISSUEFLOW_MODE", raising=False)
    assert settings.resolve_active_mode_id(tmp_path) == "standard"  # from config
    cfg.unlink()
    assert settings.resolve_active_mode_id(tmp_path) == DEFAULT_MODE


def test_read_caveman_default_missing_returns_none(tmp_path: Path) -> None:
    """No config file -> caveman_default is unset (None), not False."""
    assert read_caveman_default(config_path(tmp_path, ".issueflows")) is None


def test_read_caveman_default_unset_key_returns_none(tmp_path: Path) -> None:
    """A config without the key -> unset (None), so env/default can apply."""
    cfg = _write_config(tmp_path, '[issueflow]\nmode = "standard"\n')
    assert read_caveman_default(cfg) is None


def test_read_caveman_default_true_and_false(tmp_path: Path) -> None:
    """An explicit boolean is read back as that boolean."""
    cfg_true = _write_config(tmp_path, "[issueflow]\ncaveman_default = true\n")
    assert read_caveman_default(cfg_true) is True
    cfg_false = _write_config(tmp_path, "[issueflow]\ncaveman_default = false\n")
    assert read_caveman_default(cfg_false) is False


def test_read_grill_me_default_missing_returns_none(tmp_path: Path) -> None:
    """No config file -> grill_me_default is unset (None), not False."""
    assert read_grill_me_default(config_path(tmp_path, ".issueflows")) is None


def test_read_grill_me_default_unset_key_returns_none(tmp_path: Path) -> None:
    """A config without the key -> unset (None), so env/default can apply."""
    cfg = _write_config(tmp_path, '[issueflow]\nmode = "standard"\n')
    assert read_grill_me_default(cfg) is None


def test_read_grill_me_default_true_and_false(tmp_path: Path) -> None:
    """An explicit boolean is read back as that boolean."""
    cfg_true = _write_config(tmp_path, "[issueflow]\ngrill_me_default = true\n")
    assert read_grill_me_default(cfg_true) is True
    cfg_false = _write_config(tmp_path, "[issueflow]\ngrill_me_default = false\n")
    assert read_grill_me_default(cfg_false) is False


def test_read_label_flows_missing_returns_none(tmp_path: Path) -> None:
    """No config file -> label_flows is unset (None), not a boolean."""
    assert read_label_flows(config_path(tmp_path, ".issueflows")) is None


def test_read_label_flows_unset_key_returns_none(tmp_path: Path) -> None:
    """A config without the key -> unset (None), so env/default can apply."""
    cfg = _write_config(tmp_path, '[issueflow]\nmode = "standard"\n')
    assert read_label_flows(cfg) is None


def test_read_label_flows_true_and_false(tmp_path: Path) -> None:
    """An explicit boolean is read back as that boolean."""
    cfg_true = _write_config(tmp_path, "[issueflow]\nlabel_flows = true\n")
    assert read_label_flows(cfg_true) is True
    cfg_false = _write_config(tmp_path, "[issueflow]\nlabel_flows = false\n")
    assert read_label_flows(cfg_false) is False


def test_read_yolo_label_missing_returns_none(tmp_path: Path) -> None:
    """No config file -> yolo_label is unset (None)."""
    assert read_yolo_label(config_path(tmp_path, ".issueflows")) is None


def test_read_yolo_label_unset_key_returns_none(tmp_path: Path) -> None:
    """A config without the key -> unset (None), so env/default can apply."""
    cfg = _write_config(tmp_path, '[issueflow]\nmode = "standard"\n')
    assert read_yolo_label(cfg) is None


def test_read_yolo_label_value(tmp_path: Path) -> None:
    """An explicit label is read back verbatim."""
    cfg = _write_config(tmp_path, '[issueflow]\nyolo_label = "fast-track"\n')
    assert read_yolo_label(cfg) == "fast-track"


def test_write_default_config_includes_label_flow_keys(tmp_path: Path) -> None:
    """A freshly written config.toml carries label_flows and yolo_label."""
    cfg = config_path(tmp_path, ".issueflows")
    assert write_default_config(
        cfg,
        mode="standard",
        skill_level="standard",
        caveman_default=False,
        grill_me_default=False,
    )
    assert read_label_flows(cfg) is DEFAULT_LABEL_FLOWS
    assert read_yolo_label(cfg) == DEFAULT_YOLO_LABEL


def test_write_default_config_upserts_label_flow_keys(tmp_path: Path) -> None:
    """Overwrite upserts the label-flow keys while preserving user content."""
    cfg = _write_config(
        tmp_path,
        '# keep me\n[issueflow]\nmode = "simple"\nlabel_flows = false\n',
    )
    assert write_default_config(
        cfg,
        mode="standard",
        skill_level="standard",
        caveman_default=False,
        grill_me_default=False,
        label_flows=True,
        yolo_label="speedy",
        overwrite=True,
    )
    text = cfg.read_text(encoding="utf-8")
    assert "# keep me" in text
    assert read_label_flows(cfg) is True
    assert read_yolo_label(cfg) == "speedy"


def test_resolve_mode_module_alias() -> None:
    """The module exposes resolve_mode at package import (used by config/init)."""
    assert modes.resolve_mode("standard").id == "standard"
