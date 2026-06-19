"""
SEV1-C3-01 — execute_transition deve aplicar gate de fairness ANTES da escrita.

Auditoria C3 (Execução de Transição de Candidato) encontrou que o endpoint
POST /transition/execute (Path A — modal UI) não chama check_rejection_reason
antes do UPDATE no banco, permitindo que rejeições discriminatórias persistam
sem validação de fairness.

Princípio: P-GUARD — gate de política ANTES do efeito irreversível.
Compliance: Lei 9.029/95 (Art. 1°), CLT Art. 373-A.
Raiz: SEV1-C3-01 — fairness bypass on rejection via UI modal.

TDD RED: test_rejection_with_discriminatory_sub_status_is_blocked FALHA antes
do fix porque stages_transition.py::execute_transition não importa nem chama
check_rejection_reason — mock_check.called será False.

TDD GREEN: após fix, a função chama check_rejection_reason antes do stmt =
sa_update(...), o mock retorna is_blocked=True e HTTPException(422) é levantada.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── Fixtures helpers ─────────────────────────────────────────────────────────

def _make_request(**kwargs):
    from app.api.v1.recruitment_stages._shared import TransitionExecuteRequest
    defaults = dict(
        vacancy_candidate_id="cand-aaa-001",
        to_stage="reprovado",
        sub_status="estado civil",
        action="just_move",
    )
    defaults.update(kwargs)
    return TransitionExecuteRequest(**defaults)


def _make_user():
    u = MagicMock()
    u.id = "user-bbb-002"
    return u


def _make_stage_repo(rowcount: int = 1):
    repo = MagicMock()
    db = AsyncMock()
    exec_result = MagicMock()
    exec_result.rowcount = rowcount
    db.execute = AsyncMock(return_value=exec_result)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    repo.db = db
    return repo


def _blocked_fairness_output():
    from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
    out = FairnessCheckOutput()
    out.is_blocked = True
    out.blocked_field = "rejection_reason"
    result = MagicMock()
    result.category = "estado_civil"
    result.educational_message = (
        "Rejeição por estado civil é discriminatória (Lei 9.029/95, Art. 1°)."
    )
    out.blocked_result = result
    return out


def _clean_fairness_output():
    from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
    return FairnessCheckOutput()  # is_blocked=False por padrão


# ─── RED test — prova o defeito SEV1-C3-01 ───────────────────────────────────

@pytest.mark.asyncio
async def test_rejection_with_discriminatory_sub_status_is_blocked():
    """
    RED: stages_transition.py não chama check_rejection_reason →
         mock_check.called=False e HTTPException(422) não é levantada → FALHA.

    GREEN (após fix): check_rejection_reason é chamado ANTES de sa_update →
                      mock retorna is_blocked=True → HTTPException(422) →
                      PASSA.
    """
    from app.api.v1.recruitment_stages.stages_transition import execute_transition
    from fastapi import HTTPException

    with patch(
        "app.api.v1.recruitment_stages.stages_transition.check_rejection_reason",
        create=True,  # cria o atributo mesmo antes da importação existir (RED state)
        return_value=_blocked_fairness_output(),
    ) as mock_check, patch(
        "app.api.v1.recruitment_stages.stages_transition.settings"
    ) as mock_settings:
        mock_settings.ENABLE_LLM_SUBSTATUS_PREDICTION = False
        mock_settings.ENABLE_LLM_DISPATCH_PERSONALIZATION = False

        raised_fairness_block = False
        try:
            await execute_transition(
                request=_make_request(to_stage="reprovado", sub_status="estado civil"),
                current_user=_make_user(),
                stage_repo=_make_stage_repo(rowcount=1),
                company_id="co-ccc-003",
            )
        except HTTPException as exc:
            if exc.status_code == 422 and isinstance(exc.detail, dict):
                if exc.detail.get("error") == "fairness_blocked":
                    raised_fairness_block = True
        except Exception:
            pass  # outros erros não comprovam o gate

    # ── Assertions (ambas FALHAM no estado RED) ──
    assert mock_check.called, (
        "[RED] check_rejection_reason não foi chamado.\n"
        "execute_transition deve verificar fairness ANTES de escrever no banco "
        "(P-GUARD, SEV1-C3-01). Importar check_rejection_reason e chamá-la "
        "quando to_stage ∈ REJECTION_STAGES e sub_status não é vazio."
    )
    assert raised_fairness_block, (
        "[RED] HTTPException(422, error=fairness_blocked) não foi levantada.\n"
        "Compliance: Lei 9.029/95, CLT Art. 373-A. "
        "Ver candidatos_crud.py:789 para o padrão canônico."
    )


# ─── Boundary tests (GREEN) ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rejection_without_sub_status_skips_fairness_check():
    """
    Rejeição SEM sub_status → check_rejection_reason NÃO deve ser chamado.
    Não há motivo para checar texto discriminatório se não há texto.
    """
    from app.api.v1.recruitment_stages.stages_transition import execute_transition

    with patch(
        "app.api.v1.recruitment_stages.stages_transition.check_rejection_reason",
        create=True,
        return_value=_blocked_fairness_output(),  # retornaria blocked SE chamado
    ) as mock_check, patch(
        "app.api.v1.recruitment_stages.stages_transition.settings"
    ) as mock_settings:
        mock_settings.ENABLE_LLM_SUBSTATUS_PREDICTION = False
        mock_settings.ENABLE_LLM_DISPATCH_PERSONALIZATION = False

        try:
            await execute_transition(
                request=_make_request(to_stage="reprovado", sub_status=None),
                current_user=_make_user(),
                stage_repo=_make_stage_repo(rowcount=1),
                company_id="co-ccc-003",
            )
        except Exception:
            pass  # outros erros são irrelevantes para este boundary test

    mock_check.assert_not_called()


@pytest.mark.asyncio
async def test_non_rejection_stage_skips_fairness_check():
    """
    Transição para estágio NÃO-rejeição → check_rejection_reason NÃO deve
    ser chamado mesmo com sub_status discriminatório.
    """
    from app.api.v1.recruitment_stages.stages_transition import execute_transition

    with patch(
        "app.api.v1.recruitment_stages.stages_transition.check_rejection_reason",
        create=True,
        return_value=_blocked_fairness_output(),  # retornaria blocked SE chamado
    ) as mock_check, patch(
        "app.api.v1.recruitment_stages.stages_transition.settings"
    ) as mock_settings:
        mock_settings.ENABLE_LLM_SUBSTATUS_PREDICTION = False
        mock_settings.ENABLE_LLM_DISPATCH_PERSONALIZATION = False

        try:
            await execute_transition(
                # "entrevista" não está em REJECTION_STAGES → fairness skip
                request=_make_request(to_stage="entrevista", sub_status="estado civil"),
                current_user=_make_user(),
                stage_repo=_make_stage_repo(rowcount=1),
                company_id="co-ccc-003",
            )
        except Exception:
            pass

    mock_check.assert_not_called()


@pytest.mark.asyncio
async def test_rejection_with_valid_sub_status_passes():
    """
    Rejeição com sub_status técnico válido → check é chamado, não bloqueia.
    """
    from app.api.v1.recruitment_stages.stages_transition import execute_transition
    from fastapi import HTTPException

    with patch(
        "app.api.v1.recruitment_stages.stages_transition.check_rejection_reason",
        create=True,
        return_value=_clean_fairness_output(),  # is_blocked=False
    ) as mock_check, patch(
        "app.api.v1.recruitment_stages.stages_transition.settings"
    ) as mock_settings:
        mock_settings.ENABLE_LLM_SUBSTATUS_PREDICTION = False
        mock_settings.ENABLE_LLM_DISPATCH_PERSONALIZATION = False

        raised_fairness_block = False
        try:
            await execute_transition(
                request=_make_request(
                    to_stage="reprovado",
                    sub_status="perfil técnico incompatível com os requisitos da vaga",
                ),
                current_user=_make_user(),
                stage_repo=_make_stage_repo(rowcount=1),
                company_id="co-ccc-003",
            )
        except HTTPException as exc:
            if exc.status_code == 422 and isinstance(exc.detail, dict):
                if exc.detail.get("error") == "fairness_blocked":
                    raised_fairness_block = True
        except Exception:
            pass

    # Check foi chamado mas NÃO bloqueou (sub_status é técnico, não discriminatório)
    mock_check.assert_called_once()
    assert not raised_fairness_block, (
        "sub_status técnico não deve ser bloqueado pelo fairness gate."
    )
