"""
Onda 3.B4 — trigger_mode × target_type validation matrix contract.

Pin canonical da matriz definida em app/shared/trigger_mode_validation.py.

Cada combinação válida e inválida é exercitada via parametrize. Mudanças
nessa matriz exigem update concomitante deste teste (que vira parte do
contrato canonical).
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.shared.trigger_mode_validation import (
    LEGACY_TRIGGER_MODES,
    VALID_TRIGGER_MODES_BY_TARGET,
    validate_trigger_mode,
)


# ─────────────────────────────────────────────────────────────────────────────
# Matriz exaustiva de combinações VÁLIDAS
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "target_type,trigger_mode",
    [
        # talent_pool
        ("talent_pool", "on_create"),
        ("talent_pool", "on_schedule"),
        ("talent_pool", "manual"),
        # job
        ("job", "on_create"),
        ("job", "on_schedule"),
        ("job", "manual"),
        ("job", "on_apply"),
        # pipeline_stage
        ("pipeline_stage", "on_enter_stage"),
        ("pipeline_stage", "on_exit_stage"),
        ("pipeline_stage", "on_stuck_in_stage"),
        ("pipeline_stage", "on_stage_change"),
        # candidate_list
        ("candidate_list", "on_schedule"),
        ("candidate_list", "manual"),
    ],
)
def test_valid_combos_pass(target_type, trigger_mode):
    """Cada combo canonical aceito não levanta exceção."""
    # Should not raise
    validate_trigger_mode(target_type, trigger_mode)


# ─────────────────────────────────────────────────────────────────────────────
# Matriz exaustiva de combinações INVÁLIDAS
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "target_type,trigger_mode",
    [
        # talent_pool não aceita stage modes nem on_apply
        ("talent_pool", "on_enter_stage"),
        ("talent_pool", "on_exit_stage"),
        ("talent_pool", "on_stuck_in_stage"),
        ("talent_pool", "on_stage_change"),
        ("talent_pool", "on_apply"),
        # job não aceita stage modes
        ("job", "on_enter_stage"),
        ("job", "on_exit_stage"),
        ("job", "on_stuck_in_stage"),
        ("job", "on_stage_change"),
        # pipeline_stage não aceita manual/schedule/on_apply (só stage modes)
        ("pipeline_stage", "manual"),
        ("pipeline_stage", "on_schedule"),
        ("pipeline_stage", "on_create"),
        ("pipeline_stage", "on_apply"),
        # candidate_list não aceita stage modes nem on_apply nem on_create
        ("candidate_list", "on_create"),
        ("candidate_list", "on_apply"),
        ("candidate_list", "on_enter_stage"),
        ("candidate_list", "on_exit_stage"),
        ("candidate_list", "on_stuck_in_stage"),
        ("candidate_list", "on_stage_change"),
    ],
)
def test_invalid_combos_raise_422(target_type, trigger_mode):
    """Combos absurdos → HTTPException(422) com mensagem PT-BR."""
    with pytest.raises(HTTPException) as exc:
        validate_trigger_mode(target_type, trigger_mode)
    assert exc.value.status_code == 422
    detail = str(exc.value.detail)
    assert trigger_mode in detail
    assert "inválido" in detail


def test_unknown_target_type_raises_422():
    """target_type fora do enum canonical → 422."""
    with pytest.raises(HTTPException) as exc:
        validate_trigger_mode("foo_unknown", "manual")
    assert exc.value.status_code == 422
    assert "target_type" in str(exc.value.detail)


# ─────────────────────────────────────────────────────────────────────────────
# Backward compat — legados aceitos em qualquer target
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "target_type",
    ["job", "talent_pool", "pipeline_stage", "candidate_list"],
)
@pytest.mark.parametrize("legacy_mode", sorted(LEGACY_TRIGGER_MODES))
def test_legacy_modes_accepted_in_all_targets(target_type, legacy_mode):
    """on_new_candidate e scheduled (legados) aceitos em qualquer target."""
    # Should not raise
    validate_trigger_mode(target_type, legacy_mode)


# ─────────────────────────────────────────────────────────────────────────────
# Sanity: matriz canonical não regrediu
# ─────────────────────────────────────────────────────────────────────────────


def test_matrix_targets_are_canonical_enum():
    """Targets na matriz batem com DeploymentTargetType canonical."""
    from lia_models.agent_deployment import DeploymentTargetType

    enum_values = {v.value for v in DeploymentTargetType}
    matrix_keys = set(VALID_TRIGGER_MODES_BY_TARGET.keys())
    assert matrix_keys == enum_values, (
        f"matrix keys {matrix_keys} divergiram do enum canonical {enum_values}"
    )


def test_matrix_per_target_modes_minimum_baseline():
    """Pin: cada target tem pelo menos manual ou schedule (defesa contra regressão)."""
    for target, modes in VALID_TRIGGER_MODES_BY_TARGET.items():
        if target == "pipeline_stage":
            # pipeline_stage é trigger-driven; sem manual/schedule por design
            continue
        assert "manual" in modes or "on_schedule" in modes, (
            f"{target}: sem manual nem on_schedule"
        )
