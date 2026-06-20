"""
SEV1-C3-01 — transition_candidate deve aplicar gate de fairness ANTES da escrita.

Redireccionado de execute_transition (Path C, deletado) para o serviço canônico
PipelineStageService.transition_candidate que implementa o P-GUARD correto.

Princípio: P-GUARD — gate de política ANTES do efeito irreversível.
Compliance: Lei 9.029/95 (Art. 1°), CLT Art. 373-A.
Raiz: SEV1-C3-01 — fairness bypass on rejection via UI modal.

O serviço canônico aplica o gate em R1-A (linha ~224 de pipeline_stage_service.py):
    if any(rej in _to_stage_lower for rej in REJECTION_STAGES):
        _fairness_reason = reason or to_sub_status or ""
        if _fairness_reason:
            _fg = check_rejection_reason(...)
            if _fg.is_blocked:
                raise FairnessBlockedError(...)
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── Fixtures helpers ─────────────────────────────────────────────────────────

_VC_UUID = "00000000-0000-0000-0000-000000000001"
_COMPANY_ID = "co-ccc-003"


def _make_vacancy_candidate(stage="triagem", company_id=_COMPANY_ID):
    vc = MagicMock()
    vc.id = _VC_UUID
    vc.candidate_id = "cand-aaa-001"
    vc.vacancy_id = "vac-111"
    vc.company_id = company_id
    vc.stage = stage
    vc.status = "in_review"
    vc.previous_status = "in_review"
    return vc


def _make_stage_obj(name, company_id=_COMPANY_ID):
    s = MagicMock()
    s.id = "stage-uuid-001"
    s.name = name
    s.display_name = name
    s.is_active = True
    s.company_id = company_id
    s.stage_order = 1
    return s


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


def _make_db_mock(vc, stage_obj):
    """AsyncSession mock: db.get returns vc; db.execute returns stage scalars."""
    db = AsyncMock()
    db.get = AsyncMock(return_value=vc)

    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=[stage_obj])
    exec_result = MagicMock()
    exec_result.scalars = MagicMock(return_value=scalars_mock)
    db.execute = AsyncMock(return_value=exec_result)

    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.__aenter__ = AsyncMock(return_value=db)
    db.__aexit__ = AsyncMock(return_value=False)
    return db


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rejection_with_discriminatory_sub_status_raises_fairness_blocked():
    """
    transition_candidate para estágio de rejeição com sub_status discriminatório
    deve chamar check_rejection_reason e levantar FairnessBlockedError.

    GREEN: pipeline_stage_service.py implementa R1-A gate.
    Compliance: Lei 9.029/95, CLT Art. 373-A.
    """
    from app.domains.recruiter_assistant.services.pipeline_stage_service import (
        FairnessBlockedError,
        PipelineStageService,
    )

    COMPANY_ID = _COMPANY_ID
    stage_obj = _make_stage_obj("reprovado", COMPANY_ID)
    vc = _make_vacancy_candidate(stage="triagem", company_id=COMPANY_ID)
    db = _make_db_mock(vc, stage_obj)

    service = PipelineStageService()

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.derive_company_from_context",
        new_callable=AsyncMock,
        return_value=COMPANY_ID,
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.check_rejection_reason",
        return_value=_blocked_fairness_output(),
    ) as mock_check:

        with pytest.raises(FairnessBlockedError):
            await service.transition_candidate(
                vacancy_candidate_id=_VC_UUID,
                to_stage="reprovado",
                to_sub_status="estado civil",
                reason="estado civil",
                triggered_by="test",
                force=True,  # skip FSM/data_request_service to isolate fairness gate
                db=db,
            )

    assert mock_check.called, (
        "check_rejection_reason deve ser chamado quando to_stage ∈ REJECTION_STAGES "
        "e há reason/sub_status (P-GUARD, SEV1-C3-01)."
    )


@pytest.mark.asyncio
async def test_rejection_without_sub_status_skips_fairness_check():
    """
    Rejeição SEM reason E SEM sub_status → check_rejection_reason NÃO deve ser chamado.
    Não há texto discriminatório para checar.
    """
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    COMPANY_ID = _COMPANY_ID
    stage_obj = _make_stage_obj("reprovado", COMPANY_ID)
    vc = _make_vacancy_candidate(stage="triagem", company_id=COMPANY_ID)
    db = _make_db_mock(vc, stage_obj)

    service = PipelineStageService()

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.derive_company_from_context",
        new_callable=AsyncMock,
        return_value=COMPANY_ID,
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.check_rejection_reason",
        return_value=_blocked_fairness_output(),  # retornaria blocked SE chamado
    ) as mock_check:

        try:
            await service.transition_candidate(
                vacancy_candidate_id=_VC_UUID,
                to_stage="reprovado",
                to_sub_status=None,
                reason=None,
                triggered_by="test",
                force=True,
                db=db,
            )
        except Exception:
            pass  # outros erros são irrelevantes para este boundary test

    mock_check.assert_not_called()


@pytest.mark.asyncio
async def test_non_rejection_stage_skips_fairness_check():
    """
    Transição para estágio NÃO-rejeição → check_rejection_reason NÃO deve ser
    chamado mesmo com reason discriminatório.
    """
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    COMPANY_ID = _COMPANY_ID
    stage_obj = _make_stage_obj("entrevista", COMPANY_ID)
    vc = _make_vacancy_candidate(stage="triagem", company_id=COMPANY_ID)
    db = _make_db_mock(vc, stage_obj)

    service = PipelineStageService()

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.derive_company_from_context",
        new_callable=AsyncMock,
        return_value=COMPANY_ID,
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.check_rejection_reason",
        return_value=_blocked_fairness_output(),  # retornaria blocked SE chamado
    ) as mock_check:

        try:
            await service.transition_candidate(
                vacancy_candidate_id=_VC_UUID,
                to_stage="entrevista",
                to_sub_status="estado civil",
                reason="estado civil",
                triggered_by="test",
                force=True,
                db=db,
            )
        except Exception:
            pass

    mock_check.assert_not_called()


@pytest.mark.asyncio
async def test_rejection_with_valid_sub_status_passes():
    """
    Rejeição com reason técnico válido → check é chamado, não bloqueia,
    FairnessBlockedError NÃO é levantada.
    """
    from app.domains.recruiter_assistant.services.pipeline_stage_service import (
        FairnessBlockedError,
        PipelineStageService,
    )

    COMPANY_ID = _COMPANY_ID
    stage_obj = _make_stage_obj("reprovado", COMPANY_ID)
    vc = _make_vacancy_candidate(stage="triagem", company_id=COMPANY_ID)
    db = _make_db_mock(vc, stage_obj)

    service = PipelineStageService()

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.derive_company_from_context",
        new_callable=AsyncMock,
        return_value=COMPANY_ID,
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.check_rejection_reason",
        return_value=_clean_fairness_output(),  # is_blocked=False
    ) as mock_check:

        fairness_raised = False
        try:
            await service.transition_candidate(
                vacancy_candidate_id=_VC_UUID,
                to_stage="reprovado",
                to_sub_status="perfil técnico incompatível com os requisitos da vaga",
                reason="perfil técnico incompatível com os requisitos da vaga",
                triggered_by="test",
                force=True,
                db=db,
            )
        except FairnessBlockedError:
            fairness_raised = True
        except Exception:
            pass  # outros erros são irrelevantes para este boundary test

    assert mock_check.called, (
        "check_rejection_reason deve ser chamado mesmo com sub_status técnico."
    )
    assert not fairness_raised, (
        "sub_status técnico não deve ser bloqueado pelo fairness gate."
    )
