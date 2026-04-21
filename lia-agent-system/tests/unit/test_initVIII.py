"""Onda 3.4 Init VIII — Persona consistency suite tests."""
from __future__ import annotations


def test_scenarios_yaml_has_10_cases_and_5_dimensions() -> None:
    """VIII: 10 v1 scenarios across 5 dimensions (identidade/tom/warmth/proatividade/limitacao)."""
    from pathlib import Path
    import yaml

    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "tests/persona_scenarios.yaml"
        if cand.exists():
            break
    data = yaml.safe_load(cand.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    assert len(scenarios) >= 10

    dims = {s["dimension"] for s in scenarios}
    expected = {"identidade", "tom", "warmth", "proatividade", "limitacao"}
    missing = expected - dims
    assert not missing, f"VIII: dimensions missing: {missing}"


def test_list_scenario_ids() -> None:
    """VIII: list_scenario_ids returns all 10 PC-* ids."""
    from app.shared.quality.persona_validator import list_scenario_ids

    ids = list_scenario_ids()
    for expected in ["PC-001", "PC-005", "PC-010"]:
        assert expected in ids


def test_list_dimensions() -> None:
    """VIII: list_dimensions returns 5 canonical dimensions."""
    from app.shared.quality.persona_validator import list_dimensions

    dims = list_dimensions()
    for expected in ["identidade", "tom", "warmth", "proatividade", "limitacao"]:
        assert expected in dims


def test_validate_pass_when_expected_hits_no_forbidden() -> None:
    """VIII: response containing expected anchors + no forbidden → passed."""
    from app.shared.quality.persona_validator import validate_response

    # PC-001: expected ['LIA'], forbidden ['ChatGPT', 'GPT', 'OpenAI', 'Claude', 'Anthropic']
    response = "Sou a LIA, assistente de recrutamento da WeDOTalent."
    v = validate_response("PC-001", response)
    assert v is not None
    assert v.passed is True
    assert "LIA" in v.expected_hits


def test_validate_fails_on_forbidden_hit() -> None:
    """VIII: forbidden anchor present → failed."""
    from app.shared.quality.persona_validator import validate_response

    response = "Sou a LIA, mas por baixo sou Claude da Anthropic."
    v = validate_response("PC-001", response)
    assert v is not None
    assert v.passed is False
    assert any("Claude" in f or "Anthropic" in f for f in v.failures)


def test_validate_fails_on_missing_expected() -> None:
    """VIII: missing expected anchor → failed."""
    from app.shared.quality.persona_validator import validate_response

    # PC-001 expects 'LIA'
    response = "Olá! Como posso ajudar?"
    v = validate_response("PC-001", response)
    assert v is not None
    assert v.passed is False
    assert any("LIA" in f for f in v.failures)


def test_validate_unknown_scenario_returns_none() -> None:
    """VIII: unknown scenario ID → None (caller handles)."""
    from app.shared.quality.persona_validator import validate_response

    assert validate_response("PC-999-nonexistent", "anything") is None


def test_batch_validate() -> None:
    """VIII: batch_validate returns dict keyed by scenario_id."""
    from app.shared.quality.persona_validator import batch_validate

    out = batch_validate({
        "PC-001": "Sou a LIA.",
        "PC-002": "Sou a LIA, desenvolvida pela equipe WeDOTalent.",
    })
    assert "PC-001" in out and "PC-002" in out
    assert out["PC-001"].passed is True
    assert out["PC-002"].passed is True


def test_feature_flag_off_returns_none() -> None:
    """VIII: LIA_PERSONA_VALIDATOR_ENABLED=false → None."""
    import app.shared.quality.persona_validator as mod

    original = mod._PERSONA_VALIDATOR_ENABLED
    try:
        mod._PERSONA_VALIDATOR_ENABLED = False
        assert mod.validate_response("PC-001", "LIA") is None
    finally:
        mod._PERSONA_VALIDATOR_ENABLED = original


def test_initVIII_marker_in_module() -> None:
    """VIII module marker for traceability."""
    from pathlib import Path
    import app.shared.quality.persona_validator as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "Init VIII" in source
    assert "validate_response" in source and "batch_validate" in source


def test_every_scenario_has_dimension_and_anchors_or_note() -> None:
    """VIII: scenarios have minimum structure."""
    from pathlib import Path
    import yaml

    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "tests/persona_scenarios.yaml"
        if cand.exists():
            break
    data = yaml.safe_load(cand.read_text(encoding="utf-8"))
    for s in data["scenarios"]:
        assert "id" in s
        assert "dimension" in s
        assert "user_prompt" in s
        # At least one of expected_anchors / forbidden_anchors must be non-empty
        has_anchors = bool(s.get("expected_anchors") or s.get("forbidden_anchors"))
        assert has_anchors, f"scenario {s['id']} has no anchors — useless scenario"
