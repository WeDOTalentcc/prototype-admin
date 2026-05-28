"""
Canonical trigger_mode × target_type validation matrix (Onda 3.B4 — Fase 2 Agent Studio).

Registered 2026-05-27.

Princípio canonical: trigger_mode tem que ser coerente com target_type.
Não faz sentido `on_stage_change` em target_type=talent_pool porque pool
não tem stages. Garantir que UI e backend rejeitam combos absurdos
antes de chegarem ao banco.

Modos canonical por target_type (matriz exaustiva):

  talent_pool      → on_create, on_schedule, manual
  job              → on_create, on_schedule, manual, on_apply
  pipeline_stage   → on_enter_stage, on_exit_stage, on_stuck_in_stage, on_stage_change
  candidate_list   → on_schedule, manual

Os legados `on_new_candidate` e `scheduled` (definidos no enum DeploymentTriggerMode
em libs/models/lia_models/agent_deployment.py) permanecem aceitos por compatibilidade
retroativa com deployments existentes — vide LEGACY_TRIGGER_MODES.

Sensores correlatos:
- tests/contract/test_trigger_mode_validation.py — varre matriz completa.
"""
from __future__ import annotations

from fastapi import HTTPException

# Matriz canonical — single source of truth.
VALID_TRIGGER_MODES_BY_TARGET: dict[str, frozenset[str]] = {
    "talent_pool": frozenset({"on_create", "on_schedule", "manual"}),
    "job": frozenset({"on_create", "on_schedule", "manual", "on_apply"}),
    "pipeline_stage": frozenset(
        {"on_enter_stage", "on_exit_stage", "on_stuck_in_stage", "on_stage_change"}
    ),
    "candidate_list": frozenset({"on_schedule", "manual"}),
}

# Backward-compat: trigger_modes pré-Onda 3 que continuam aceitos em qualquer target.
# Documentado em CLAUDE.md sob Onda 3 — agentes recém-criados devem preferir os
# canonical modes acima.
LEGACY_TRIGGER_MODES: frozenset[str] = frozenset(
    {
        "on_new_candidate",  # equivalente a on_apply (job) / on_create (pool)
        "scheduled",  # equivalente a on_schedule
    }
)


def validate_trigger_mode(target_type: str, trigger_mode: str) -> None:
    """Valida combo target_type × trigger_mode.

    Args:
        target_type: valor canonical (job/talent_pool/pipeline_stage/candidate_list).
        trigger_mode: string canonical (on_create/on_schedule/manual/on_apply/
            on_enter_stage/on_exit_stage/on_stuck_in_stage/on_stage_change) ou legado.

    Raises:
        HTTPException(422): combo inválido. Mensagem em PT-BR + listagem dos modos
            válidos para o target_type específico.
    """
    if target_type not in VALID_TRIGGER_MODES_BY_TARGET:
        raise HTTPException(
            status_code=422,
            detail=(
                f"target_type '{target_type}' inválido. "
                f"Valores aceitos: {sorted(VALID_TRIGGER_MODES_BY_TARGET.keys())}"
            ),
        )

    # Aceita legado em qualquer target_type (backward compat).
    if trigger_mode in LEGACY_TRIGGER_MODES:
        return

    valid_modes = VALID_TRIGGER_MODES_BY_TARGET[target_type]
    if trigger_mode not in valid_modes:
        raise HTTPException(
            status_code=422,
            detail=(
                f"trigger_mode '{trigger_mode}' inválido para "
                f"target_type='{target_type}'. "
                f"Modos válidos: {sorted(valid_modes)}"
            ),
        )
