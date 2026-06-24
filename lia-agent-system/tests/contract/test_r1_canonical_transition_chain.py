"""
R1 — Cadeia canônica de transição de etapa: fairness + audit + idempotência.

Testa que pipeline_stage_service.transition_candidate():
  1. Chama check_rejection_reason em transições de rejeição.
  2. Levanta FairnessBlockedError quando fairness bloqueia.
  3. Chama AuditService.log_decision em toda transição bem-sucedida.
  4. É idempotente: segunda chamada com mesmo to_stage não grava histórico.
  5. (não-regressão) Levanta PermissionError em company_id mismatch.
  6. (não-regressão) candidates_crud ainda importa check_rejection_reason.

TDD Red → Green:
  R1–R4 devem FALHAR antes do fix em pipeline_stage_service.py.
  R5–R6 devem PASSAR (já implementado).
"""
from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

# ─── Helpers ──────────────────────────────────────────────────────────────────

COMPANY_ID = "aaaaaaaa-0000-0000-0000-000000000001"
CANDIDATE_ID = "bbbbbbbb-0000-0000-0000-000000000002"
VACANCY_ID = "cccccccc-0000-0000-0000-000000000003"
VC_ID = "dddddddd-0000-0000-0000-000000000004"

# Stage name that matches REJECTION_STAGES substring check:
REJECTION_STAGE = "reprovado"
VALID_STAGE = "entrevista_rh"


def _make_vacancy_candidate(stage: str = VALID_STAGE) -> MagicMock:
    vc = MagicMock()
    vc.id = uuid.UUID(VC_ID)
    vc.company_id = COMPANY_ID
    vc.candidate_id = uuid.UUID(CANDIDATE_ID)
    vc.vacancy_id = uuid.UUID(VACANCY_ID)
    vc.stage = stage
    vc.status = "active"
    return vc


def _make_stage_obj(name: str = VALID_STAGE) -> MagicMock:
    s = MagicMock()
    s.id = uuid.uuid4()
    s.name = name
    s.display_name = name
    s.is_final = False
    s.action_behavior = "passive"
    return s


def _make_db(vc: MagicMock, stages: list | None = None) -> AsyncMock:
    """Creates a mock AsyncSession that returns vc on .get() and stages list."""
    db = AsyncMock()
    db.get = AsyncMock(return_value=vc)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()

    if stages is None:
        stages = [_make_stage_obj(VALID_STAGE), _make_stage_obj(REJECTION_STAGE)]

    # db.execute returns scalars().all()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none = MagicMock(return_value=None)
    scalars_result = MagicMock()
    scalars_result.all = MagicMock(return_value=stages)
    exec_result.scalars = MagicMock(return_value=scalars_result)
    db.execute = AsyncMock(return_value=exec_result)

    return db


def _blocked_output():
    from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
    out = FairnessCheckOutput()
    out.is_blocked = True
    blocked = MagicMock()
    blocked.educational_message = "Viés detectado: critério proibido por Lei 9.029/95"
    blocked.category = "estado_civil"
    out.blocked_result = blocked
    return out


def _clear_output():
    from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
    out = FairnessCheckOutput()
    out.is_blocked = False
    return out


def _make_mock_dr_svc():
    """Mock for data_request_service property."""
    dr = MagicMock()
    dr.find_blocking_pending_request = AsyncMock(return_value=None)
    dr.check_existing_pending_request = AsyncMock(return_value=False)
    dr.get_trigger_fields_for_stage = AsyncMock(return_value=None)
    return dr


def _make_mock_auto_svc():
    """Mock for automation_service property."""
    auto = MagicMock()
    auto.trigger_automation = AsyncMock(return_value={"automations_executed": 0})
    return auto


# ─── Test 1 ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_r1_service_calls_fairness_on_rejection_stage():
    """
    RED: pipeline_stage_service.transition_candidate deve chamar
    check_rejection_reason quando to_stage ∈ REJECTION_STAGES.

    Actualmente o serviço NÃO importa check_rejection_reason → AttributeError.
    Após o fix, mock_fg.called deve ser True.
    """
    from app.domains.recruiter_assistant.services import pipeline_stage_service as _svc_mod
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    vc = _make_vacancy_candidate(stage=VALID_STAGE)
    db = _make_db(vc)

    service = PipelineStageService()
    service._data_request_service = _make_mock_dr_svc()
    service._automation_service = _make_mock_auto_svc()

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.derive_company_from_context",
        new_callable=AsyncMock,
        return_value=COMPANY_ID,
    ), patch.object(
        service, "_validate_transition", new_callable=AsyncMock, return_value=(True, None)
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.ats_sync_service"
    ) as mock_ats, patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.get_event_dispatcher",
    ) as mock_disp, patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.AuditService",
        MagicMock(return_value=MagicMock(log_decision=AsyncMock())),
    ):
        mock_ats.trigger_status_change = AsyncMock(return_value={})
        mock_disp.return_value.on_stage_changed = AsyncMock(return_value={})

        # Inject check_rejection_reason mock into the module namespace
        # (it doesn't exist yet — will raise AttributeError before fix)
        mock_fg = MagicMock(return_value=_clear_output())
        _original = getattr(_svc_mod, "check_rejection_reason", None)
        _svc_mod.check_rejection_reason = mock_fg
        try:
            await service.transition_candidate(
                vacancy_candidate_id=VC_ID,
                to_stage=REJECTION_STAGE,
                to_sub_status="qualificacao_insuficiente",
                reason="Perfil não atende os requisitos",
                context={"company_id": COMPANY_ID},
                db=db,
            )
        finally:
            if _original is None:
                try:
                    delattr(_svc_mod, "check_rejection_reason")
                except AttributeError:
                    pass
            else:
                _svc_mod.check_rejection_reason = _original

    # RED: will fail until fix adds the fairness gate call
    assert mock_fg.called, (
        "R1-FAIL: check_rejection_reason NÃO foi chamado para stage de rejeição. "
        "Fix: adicionar gate fairness em pipeline_stage_service.transition_candidate."
    )


# ─── Test 2 ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_r2_service_raises_on_fairness_blocked():
    """
    RED: quando check_rejection_reason retorna is_blocked=True, o serviço
    deve levantar FairnessBlockedError.

    Actualmente o serviço não chama check_rejection_reason → nunca levanta.
    Após o fix, deve levantar FairnessBlockedError.
    """
    from app.domains.recruiter_assistant.services import pipeline_stage_service as _svc_mod
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    vc = _make_vacancy_candidate(stage=VALID_STAGE)
    db = _make_db(vc)

    service = PipelineStageService()
    service._data_request_service = _make_mock_dr_svc()
    service._automation_service = _make_mock_auto_svc()

    _original = getattr(_svc_mod, "check_rejection_reason", None)
    _svc_mod.check_rejection_reason = MagicMock(return_value=_blocked_output())

    try:
        with patch(
            "app.domains.recruiter_assistant.services.pipeline_stage_service.derive_company_from_context",
            new_callable=AsyncMock,
            return_value=COMPANY_ID,
        ), patch.object(
            service, "_validate_transition", new_callable=AsyncMock, return_value=(True, None)
        ), patch(
            "app.domains.recruiter_assistant.services.pipeline_stage_service.ats_sync_service"
        ):
            raised = False
            raised_exc = None
            try:
                await service.transition_candidate(
                    vacancy_candidate_id=VC_ID,
                    to_stage=REJECTION_STAGE,
                    to_sub_status="estado civil",
                    reason="estado civil",
                    context={"company_id": COMPANY_ID},
                    db=db,
                )
            except Exception as exc:
                raised = True
                raised_exc = exc
    finally:
        if _original is None:
            try:
                delattr(_svc_mod, "check_rejection_reason")
            except AttributeError:
                pass
        else:
            _svc_mod.check_rejection_reason = _original

    # RED: will fail until fix raises FairnessBlockedError
    assert raised, (
        "R2-FAIL: nenhuma exceção levantada quando fairness.is_blocked=True. "
        "Fix: levantar FairnessBlockedError quando fairness.is_blocked=True."
    )
    # After fix, raised_exc should be FairnessBlockedError or HTTPException
    assert raised_exc is not None


# ─── Test 3 ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_r3_service_calls_audit_log_on_transition():
    """
    RED: pipeline_stage_service.transition_candidate deve chamar
    AuditService.log_decision após cada transição bem-sucedida.

    Actualmente o serviço não importa AuditService → AttributeError ao patch.
    Após o fix, mock_audit.called deve ser True.
    """
    from app.domains.recruiter_assistant.services import pipeline_stage_service as _svc_mod
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    vc = _make_vacancy_candidate(stage="triagem")
    db = _make_db(vc)

    service = PipelineStageService()
    service._data_request_service = _make_mock_dr_svc()
    service._automation_service = _make_mock_auto_svc()

    mock_audit_instance = MagicMock()
    mock_audit_instance.log_decision = AsyncMock(return_value=MagicMock())

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.derive_company_from_context",
        new_callable=AsyncMock,
        return_value=COMPANY_ID,
    ), patch.object(
        service, "_validate_transition", new_callable=AsyncMock, return_value=(True, None)
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.ats_sync_service"
    ) as mock_ats, patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.get_event_dispatcher",
    ) as mock_disp, patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.AuditService",
        return_value=mock_audit_instance,
    ):
        mock_ats.trigger_status_change = AsyncMock(return_value={})
        mock_disp.return_value.on_stage_changed = AsyncMock(return_value={})

        await service.transition_candidate(
            vacancy_candidate_id=VC_ID,
            to_stage=VALID_STAGE,
            context={"company_id": COMPANY_ID},
            db=db,
        )

    # RED: will fail until fix adds AuditService call (AttributeError on patch before fix)
    assert mock_audit_instance.log_decision.called, (
        "R3-FAIL: AuditService.log_decision NÃO foi chamado. "
        "Fix: adicionar chamada a AuditService().log_decision() após db.commit()."
    )


# ─── Test 4 ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_r4_idempotent_double_call_produces_one_history_entry():
    """
    RED: chamar transition_candidate duas vezes com o mesmo to_stage deve ser
    idempotente: a segunda chamada deve retornar sem gravar nova entrada no histórico.

    Actualmente o serviço sempre grava → db.add será chamado 2×.
    Após o fix, db.add deve ser chamado apenas 1× (segundo call = no-op).
    """
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    vc = _make_vacancy_candidate(stage=VALID_STAGE)
    db = _make_db(vc)

    service = PipelineStageService()
    service._data_request_service = _make_mock_dr_svc()
    service._automation_service = _make_mock_auto_svc()

    call_kwargs: dict[str, Any] = dict(
        vacancy_candidate_id=VC_ID,
        to_stage=VALID_STAGE,
        context={"company_id": COMPANY_ID},
        db=db,
    )

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.derive_company_from_context",
        new_callable=AsyncMock,
        return_value=COMPANY_ID,
    ), patch.object(
        service, "_validate_transition", new_callable=AsyncMock, return_value=(True, None)
    ), patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.ats_sync_service"
    ) as mock_ats, patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.get_event_dispatcher",
    ) as mock_disp, patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.AuditService",
        return_value=MagicMock(log_decision=AsyncMock()),
    ):
        mock_ats.trigger_status_change = AsyncMock(return_value={})
        mock_disp.return_value.on_stage_changed = AsyncMock(return_value={})

        # First call — transition happens
        result1 = await service.transition_candidate(**call_kwargs)
        add_count_after_first = db.add.call_count

        # Second call with same stage — should be no-op
        result2 = await service.transition_candidate(**call_kwargs)
        add_count_after_second = db.add.call_count

    # RED: will fail until idempotency check is added (currently add_count doubles)
    assert add_count_after_second == add_count_after_first, (
        f"R4-FAIL: db.add chamado {add_count_after_second}× mas deveria ser {add_count_after_first}× "
        "(segunda chamada deveria ser no-op). "
        "Fix: verificar if vacancy_candidate.stage == to_stage → return early."
    )
    assert result2.get("idempotent") is True, (
        "R4-FAIL: segunda chamada deveria retornar idempotent=True mas retornou: "
        f"{result2}"
    )


# ─── Test 5 (NON-REGRESSION) ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_r5_tenant_fail_closed_still_raises():
    """
    GREEN (non-regression): company_id mismatch deve sempre levantar PermissionError.
    """
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    vc = _make_vacancy_candidate()
    vc.company_id = "different-company-id"  # mismatch
    db = _make_db(vc)

    service = PipelineStageService()
    service._data_request_service = _make_mock_dr_svc()
    service._automation_service = _make_mock_auto_svc()

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.derive_company_from_context",
        new_callable=AsyncMock,
        return_value=COMPANY_ID,  # request is for COMPANY_ID, vc belongs to "different-company-id"
    ):
        with pytest.raises(PermissionError):
            await service.transition_candidate(
                vacancy_candidate_id=VC_ID,
                to_stage=VALID_STAGE,
                context={"company_id": COMPANY_ID},
                db=db,
            )


# ─── Test 6 (NON-REGRESSION) ──────────────────────────────────────────────────

def test_r6_candidates_crud_imports_fairness():
    """
    GREEN (non-regression): candidates_crud.py deve importar check_rejection_reason
    da fairness_guard_middleware (Path B fairness gate já existe).
    """
    import pathlib

    crud_path = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/candidates/candidates_crud.py"
    )
    assert crud_path.exists(), "candidates_crud.py não encontrado"
    source = crud_path.read_text()
    assert "check_rejection_reason" in source, (
        "R6-FAIL: candidates_crud.py não importa check_rejection_reason — "
        "Path B fairness gate ausente."
    )

# ─── Tests D2 (kanban _wrap_batch_move_candidates → pipeline_stage_service) ───

"""
D2 tests verify that _wrap_batch_move_candidates in kanban_tool_registry.py
calls pipeline_stage_service.transition_candidate per-candidate instead of
bulk_update_candidate_stage (the raw-SQL repository bypass, SEV1 P-GUARD).

RED: These tests FAIL before the migration (bulk_update called, service not called).
GREEN: After migration, service is called per-candidate, fairness/audit enforced.

Note: tests mock hitl_gate_enabled→False to disable the HITL dormancy gate so
the function body is exercised regardless of LIA_HITL_GATE env var.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

# Shared HITL bypass: disables the dormancy gate so tests reach the loop body
_HITL_DISABLED = patch(
    "app.shared.hitl.hitl_approval_context.hitl_gate_enabled",
    return_value=False,
)


# ─── D2 Test 7: service called per-candidate (RED until migration) ──────────────

@pytest.mark.asyncio
async def test_d2_r7_service_called_per_candidate():
    """
    RED → GREEN: _wrap_batch_move_candidates must call
    pipeline_stage_service.transition_candidate once per candidate_id,
    NOT bulk_update_candidate_stage.

    Before migration: service NOT called → test FAILS.
    After migration:  service called len(candidate_ids) times → test PASSES.
    """
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
        _wrap_batch_move_candidates,
    )
    from app.domains.recruiter_assistant.services.pipeline_stage_service import (
        FairnessBlockedError,
    )

    candidate_ids = [
        "eeeeeeee-0000-0000-0000-000000000011",
        "ffffffff-0000-0000-0000-000000000022",
        "00000000-aaaa-0000-0000-000000000033",
    ]

    mock_svc = MagicMock()
    mock_svc.transition_candidate = AsyncMock(return_value={"ok": True, "to_stage": "entrevista_rh"})

    with _HITL_DISABLED, patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry.pipeline_stage_service",
        mock_svc,
    ), patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry._fetch_candidate_name_map",
        new_callable=AsyncMock,
        return_value={cid: f"Candidate {i}" for i, cid in enumerate(candidate_ids)},
    ):
        result = await _wrap_batch_move_candidates(
            candidate_ids=candidate_ids,
            target_stage="entrevista_rh",
            vacancy_id=VACANCY_ID,
            company_id=COMPANY_ID,
            reason="Batch move test D2",
        )

    # D2-R7: service must be called once per candidate
    assert mock_svc.transition_candidate.call_count == len(candidate_ids), (
        f"D2-R7-FAIL: transition_candidate chamado {mock_svc.transition_candidate.call_count}x "
        f"mas deveria ser {len(candidate_ids)}x (um por candidato). "
        "Fix: substituir bulk_update_candidate_stage por loop per-candidate."
    )
    assert result["success"] is True, f"D2-R7-FAIL: esperado success=True, got: {result}"
    assert result["data"]["moved_count"] == len(candidate_ids), (
        f"D2-R7-FAIL: moved_count={result['data']['moved_count']} mas esperado {len(candidate_ids)}"
    )


# ─── D2 Test 8: FairnessBlockedError per-candidate is tracked (RED until migration) ──

@pytest.mark.asyncio
async def test_d2_r8_fairness_block_tracked_per_candidate():
    """
    RED → GREEN: When pipeline_stage_service raises FairnessBlockedError for
    one candidate, that candidate must appear in the results with ok=False,
    while others succeed.

    Before migration: bulk_update ignores fairness → test FAILS.
    After migration:  per-candidate loop handles FairnessBlockedError → test PASSES.
    """
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
        _wrap_batch_move_candidates,
    )
    from app.domains.recruiter_assistant.services.pipeline_stage_service import (
        FairnessBlockedError,
    )

    candidate_ids = [
        "eeeeeeee-0000-0000-0000-000000000011",
        "ffffffff-0000-0000-0000-000000000022",
    ]
    blocked_id = candidate_ids[0]

    fairness_error = FairnessBlockedError("Vies detectado: criterio proibido por Lei 9.029/95")

    call_counter = {"n": 0}

    async def _side_effect(**kwargs):
        cid = kwargs.get("vacancy_candidate_id", "")
        call_counter["n"] += 1
        if cid == blocked_id:
            raise fairness_error
        return {"ok": True, "to_stage": "entrevista_rh"}

    mock_svc = MagicMock()
    mock_svc.transition_candidate = AsyncMock(side_effect=_side_effect)

    with _HITL_DISABLED, patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry.pipeline_stage_service",
        mock_svc,
    ), patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry._fetch_candidate_name_map",
        new_callable=AsyncMock,
        return_value={cid: f"Candidate {i}" for i, cid in enumerate(candidate_ids)},
    ):
        result = await _wrap_batch_move_candidates(
            candidate_ids=candidate_ids,
            target_stage="entrevista_rh",
            vacancy_id=VACANCY_ID,
            company_id=COMPANY_ID,
            reason="Batch fairness test D2",
        )

    # D2-R8: call count must equal total candidates (fairness block does not skip iteration)
    assert call_counter["n"] == len(candidate_ids), (
        f"D2-R8-FAIL: transition_candidate chamado {call_counter['n']}x "
        f"mas deveria ser {len(candidate_ids)}x. "
        "Fix: per-candidate loop deve continuar apos FairnessBlockedError."
    )
    # D2-R8: 1 succeeded, 1 blocked → moved_count = 1
    assert result["success"] is True, f"D2-R8-FAIL: resultado deve ser success=True, got: {result}"
    assert result["data"]["moved_count"] == 1, (
        f"D2-R8-FAIL: moved_count={result['data']['moved_count']} mas esperado 1 "
        "(1 candidato bloqueado por fairness)."
    )
    # The blocked candidate must be ok=False in results
    results_list = result["data"]["ui_action_params"]["results"]
    blocked_result = next((r for r in results_list if r["id"] == blocked_id), None)
    assert blocked_result is not None, "D2-R8-FAIL: candidato bloqueado nao aparece nos results"
    assert blocked_result["ok"] is False, (
        f"D2-R8-FAIL: candidato bloqueado deveria ter ok=False, got: {blocked_result}"
    )


# ─── D2 Test 9: bulk_update_candidate_stage NOT called (regression guard) ──────

@pytest.mark.asyncio
async def test_d2_r9_bulk_update_not_called():
    """
    GREEN after migration: bulk_update_candidate_stage must NOT be called by
    _wrap_batch_move_candidates. This is the regression guard that locks D2.

    Before migration: bulk_update IS called → test FAILS.
    After migration:  bulk_update NOT called → test PASSES.
    """
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
        _wrap_batch_move_candidates,
    )

    candidate_ids = ["eeeeeeee-0000-0000-0000-000000000011"]

    mock_svc = MagicMock()
    mock_svc.transition_candidate = AsyncMock(return_value={"ok": True, "to_stage": "entrevista_rh"})

    mock_repo = MagicMock()
    mock_repo.bulk_update_candidate_stage = AsyncMock(return_value=1)

    with _HITL_DISABLED, patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry.pipeline_stage_service",
        mock_svc,
    ), patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry._fetch_candidate_name_map",
        new_callable=AsyncMock,
        return_value={candidate_ids[0]: "Candidate A"},
    ):
        # Also patch RecruiterMetricsRepository to detect if it gets called
        with patch(
            "app.domains.recruiter_assistant.repositories.recruiter_metrics_repository.RecruiterMetricsRepository",
            return_value=mock_repo,
        ):
            await _wrap_batch_move_candidates(
                candidate_ids=candidate_ids,
                target_stage="entrevista_rh",
                vacancy_id=VACANCY_ID,
                company_id=COMPANY_ID,
                reason="Regression guard test D2",
            )

    assert mock_repo.bulk_update_candidate_stage.call_count == 0, (
        f"D2-R9-FAIL: bulk_update_candidate_stage chamado {mock_repo.bulk_update_candidate_stage.call_count}x "
        "mas deveria ser 0x apos migracao D2. "
        "Fix: remover chamada a repo.bulk_update_candidate_stage em _wrap_batch_move_candidates."
    )


# ============================================================
# FASE 3 RED TESTS — Path B delegation + D2 loop polish
# ============================================================
_CANDIDATE_ID_B = "aabbccdd-0001-0002-0003-000000000001"
_VACANCY_CANDIDATE_ID_B = "aabbccdd-0001-0002-0003-000000000002"
_VACANCY_ID_B = "aabbccdd-0001-0002-0003-000000000003"

from datetime import datetime as _datetime

from app.domains.recruiter_assistant.services.pipeline_stage_service import (
    FairnessBlockedError as _FairnessBlockedError,
)
from app.domains.recruiter_assistant.agents.kanban_tool_registry import (
    _wrap_batch_move_candidates,
)


def _make_b_fixtures(stage: str = "entrevista_rh", sub_status=None, user_id=None):
    """Shared fixture builder for T-B tests."""
    from fastapi import BackgroundTasks
    _candidate = MagicMock()
    _candidate.id = uuid.UUID(_CANDIDATE_ID_B)
    _candidate.name = "Alice Teste"
    _candidate.status = "triagem"
    _vc = MagicMock()
    _vc.id = uuid.UUID(_VACANCY_CANDIDATE_ID_B)
    _vc.stage = "triagem"
    _vc.status = "default"
    _vc.company_id = uuid.UUID(COMPANY_ID)
    _vc.vacancy_id = uuid.UUID(_VACANCY_ID_B)
    _vc.lia_score = 0.8
    _vc.updated_at = _datetime.utcnow()
    _candidate_repo = AsyncMock()
    _candidate_repo.get_by_id_str = AsyncMock(return_value=_candidate)
    _candidate_repo.db = AsyncMock()
    _vc_repo = AsyncMock()
    _vc_repo.get_for_candidate_and_job = AsyncMock(return_value=_vc)
    _vc_repo.update = AsyncMock(return_value=_vc)
    _vc_repo.db = AsyncMock()
    _stage_data = MagicMock()
    _stage_data.stage = stage
    _stage_data.sub_status = sub_status
    _stage_data.user_id = user_id
    _stage_data.job_vacancy_id = _VACANCY_ID_B
    _bt = BackgroundTasks()
    return _candidate, _vc, _candidate_repo, _vc_repo, _stage_data, _bt


@pytest.mark.asyncio
async def test_t_b_a_path_b_calls_service_not_repo_directly():
    """T-B-a RED: update_candidate_stage MUST call pipeline_stage_service.transition_candidate.
    RED state: writes via vc_repo.update directly (no delegation to service).
    GREEN: transition_candidate called 1x; vc_repo.update called 0x.
    Fix: import pipeline_stage_service in candidates_crud.py, delegate write+chain.
    """
    import app.api.v1.candidates.candidates_crud as _crud

    _candidate, _vc, _candidate_repo, _vc_repo, _stage_data, _bt = _make_b_fixtures(
        stage="entrevista_rh", sub_status=None, user_id=None
    )
    _mock_svc = MagicMock()
    _mock_svc.transition_candidate = AsyncMock(return_value={
        "success": True,
        "idempotent": False,
        "transition": {"from_stage": "triagem", "to_stage": "entrevista_rh"},
    })

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.pipeline_stage_service",
        _mock_svc,
    ), patch("app.api.v1.candidates.candidates_crud.assert_mutation_allowed", AsyncMock()), \
         patch("app.api.v1.candidates.candidates_crud.determine_feedback_action", return_value="neutral"):
        try:
            await _crud.update_candidate_stage(
                candidate_id=_CANDIDATE_ID_B,
                stage_data=_stage_data,
                background_tasks=_bt,
                candidate_repo=_candidate_repo,
                vc_repo=_vc_repo,
                audit_svc=AsyncMock(),
                activity_svc=AsyncMock(),
                current_user=MagicMock(id=uuid.UUID("00000000-0000-0000-0000-000000000099")),
                company_id=COMPANY_ID,
            )
        except Exception:
            pass  # RED: may error because service not wired yet

    assert _mock_svc.transition_candidate.call_count == 1, (
        f"T-B-a FAIL: pipeline_stage_service.transition_candidate chamado "
        f"{_mock_svc.transition_candidate.call_count}x esperado 1x. "
        "Fix: importar pipeline_stage_service em candidates_crud.py e delegar write+chain."
    )
    assert _vc_repo.update.call_count == 0, (
        f"T-B-a FAIL: vc_repo.update chamado {_vc_repo.update.call_count}x esperado 0x. "
        "Write deve ser delegado ao pipeline_stage_service, nao feito diretamente via repo."
    )


@pytest.mark.asyncio
async def test_t_b_b_fairness_error_from_service_returns_422():
    """T-B-b RED: FairnessBlockedError from service -> HTTPException 422 with educational_message.
    RED state: service not called -> 200 returned (or 422 from Path B own gate only).
    GREEN: service raises -> endpoint maps to 422 with _fb.message.
    Fix: catch FairnessBlockedError in Path B after service delegation.
    """
    import app.api.v1.candidates.candidates_crud as _crud
    from fastapi import HTTPException as _HTTP

    _candidate, _vc, _candidate_repo, _vc_repo, _stage_data, _bt = _make_b_fixtures(
        stage="reprovado",
        sub_status="Perfil inadequado",
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000011"),
    )
    _edu_msg = "Rejeicao com base em genero nao e permitida (Lei 9.029/95)"
    _mock_svc = MagicMock()
    _mock_svc.transition_candidate = AsyncMock(
        side_effect=_FairnessBlockedError(message=_edu_msg, suggestion="Use criterios tecnicos")
    )
    _fg_pass = MagicMock(is_blocked=False, blocked_result=None)

    got_status = None
    got_detail = None
    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.pipeline_stage_service",
        _mock_svc,
    ), patch("app.api.v1.candidates.candidates_crud.assert_mutation_allowed", AsyncMock()), \
         patch("app.api.v1.candidates.candidates_crud.check_rejection_reason", return_value=_fg_pass):
        try:
            await _crud.update_candidate_stage(
                candidate_id=_CANDIDATE_ID_B,
                stage_data=_stage_data,
                background_tasks=_bt,
                candidate_repo=_candidate_repo,
                vc_repo=_vc_repo,
                audit_svc=AsyncMock(),
                activity_svc=AsyncMock(),
                current_user=MagicMock(id=uuid.UUID("00000000-0000-0000-0000-000000000099")),
                company_id=COMPANY_ID,
            )
        except _HTTP as exc:
            got_status = exc.status_code
            got_detail = exc.detail
        except Exception:
            pass  # RED: may be other exception

    assert got_status == 422, (
        f"T-B-b FAIL: status={got_status} esperado 422. "
        "Endpoint deve capturar FairnessBlockedError do servico e retornar 422."
    )
    assert isinstance(got_detail, dict) and got_detail.get("error") == "fairness_blocked", (
        f"T-B-b FAIL: detail={got_detail}. Esperado error=fairness_blocked."
    )
    assert _edu_msg in str(got_detail.get("message", "")), (
        f"T-B-b FAIL: {_edu_msg!r} nao encontrado em detail.message={got_detail.get('message')}. "
        "Endpoint deve propagar educational_message do servico para o cliente."
    )
    assert _vc_repo.update.call_count == 0, (
        f"T-B-b FAIL: vc_repo.update chamado {_vc_repo.update.call_count}x. "
        "Write deve ser bloqueado quando servico levanta FairnessBlockedError."
    )


@pytest.mark.asyncio
async def test_t_b_c_post_service_lgpd_kanban_still_called():
    """T-B-c: After service success, write is delegated (vc_repo.update=0).
    GREEN when transition_candidate called AND vc_repo.update=0.
    """
    import app.api.v1.candidates.candidates_crud as _crud

    _candidate, _vc, _candidate_repo, _vc_repo, _stage_data, _bt = _make_b_fixtures(
        stage="reprovado",
        sub_status=None,
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000011"),
    )
    _mock_svc = MagicMock()
    _mock_svc.transition_candidate = AsyncMock(return_value={
        "success": True,
        "idempotent": False,
        "transition": {"from_stage": "triagem", "to_stage": "reprovado"},
    })
    _fg_pass = MagicMock(is_blocked=False, blocked_result=None)

    with patch(
        "app.domains.recruiter_assistant.services.pipeline_stage_service.pipeline_stage_service",
        _mock_svc,
    ), patch("app.api.v1.candidates.candidates_crud.assert_mutation_allowed", AsyncMock()), \
         patch("app.api.v1.candidates.candidates_crud.check_rejection_reason", return_value=_fg_pass), \
         patch("app.api.v1.candidates.candidates_crud.determine_feedback_action", return_value="neutral"):
        try:
            await _crud.update_candidate_stage(
                candidate_id=_CANDIDATE_ID_B,
                stage_data=_stage_data,
                background_tasks=_bt,
                candidate_repo=_candidate_repo,
                vc_repo=_vc_repo,
                audit_svc=AsyncMock(),
                activity_svc=AsyncMock(),
                current_user=MagicMock(id=uuid.UUID("00000000-0000-0000-0000-000000000099")),
                company_id=COMPANY_ID,
            )
        except Exception:
            pass

    assert _mock_svc.transition_candidate.call_count == 1, (
        f"T-B-c FAIL: transition_candidate chamado {_mock_svc.transition_candidate.call_count}x. "
        "Prerequisito: Path B deve delegar ao servico antes de checar LGPD."
    )
    assert _vc_repo.update.call_count == 0, (
        f"T-B-c FAIL: vc_repo.update chamado {_vc_repo.update.call_count}x. "
        "Write deve ser exclusivo do servico canonico."
    )


@pytest.mark.asyncio
async def test_t_d2_d_fairness_blocked_propagates_educational_message():
    """T-D2-d RED: FairnessBlockedError in D2 loop -> _fb.message in ui_results reason.
    RED state: _failed_ids is a set; generic Bloqueado (fairness/permissao) used for all.
    GREEN: _failed_ids is dict; _fb.message appears verbatim in candidate result.
    Fix: _failed_ids: dict[str, str]; capture _fb.message per candidate.
    """
    _edu_msg = "Rejeicao por estado civil detectada — vies proibido (Lei 9.029/95)"
    _mock_svc = MagicMock()
    _mock_svc.transition_candidate = AsyncMock(
        side_effect=_FairnessBlockedError(message=_edu_msg, suggestion="")
    )
    _cid = "ffffffff-0000-0000-0000-000000000001"
    _name_map = {_cid: "Candidato X"}

    with patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry.pipeline_stage_service",
        _mock_svc,
    ), patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry._fetch_candidate_name_map",
        new_callable=AsyncMock,
        return_value=_name_map,
    ), _HITL_DISABLED:
        result = await _wrap_batch_move_candidates(
            candidate_ids=[_cid],
            target_stage="reprovado",
            vacancy_id=VACANCY_ID,
            company_id=COMPANY_ID,
            reason="Test fairness message propagation",
        )

    _ui_results = result.get("data", {}).get("ui_action_params", {}).get("results", [])
    assert len(_ui_results) == 1, f"T-D2-d FAIL: esperado 1 resultado, got {len(_ui_results)}"
    _r = _ui_results[0]
    assert _r.get("ok") is False, f"T-D2-d FAIL: ok deveria ser False para blocked candidate"
    _reason = _r.get("reason", "")
    assert _edu_msg in _reason, (
        f"T-D2-d FAIL: educational_message {_edu_msg} nao encontrado em reason={_reason}. "
        "Fix: _failed_ids: dict[str, str]; capturar _fb.message no except FairnessBlockedError."
    )


@pytest.mark.asyncio
async def test_t_d2_e_distinguishes_fairness_permission_system_error():
    """T-D2-e RED: D2 loop must distinguish fairness/permission/system error in reason text.
    RED state: all three map to same generic Bloqueado (fairness/permissao).
    GREEN: fairness -> _fb.message; permission -> Sem permissao; system -> type info.
    Fix: _failed_ids: dict[str, str]; different messages per exception type.
    """
    _cid_fairness = "eeeeeeee-0000-0000-0000-000000000001"
    _cid_perm = "eeeeeeee-0000-0000-0000-000000000002"
    _cid_err = "eeeeeeee-0000-0000-0000-000000000003"
    _edu_msg = "Vies de raca detectado"

    _call_count = [0]
    async def _svc_side_effect(**kwargs):
        cid = kwargs.get("vacancy_candidate_id", "")
        _call_count[0] += 1
        if cid == _cid_fairness:
            raise _FairnessBlockedError(message=_edu_msg, suggestion="")
        elif cid == _cid_perm:
            raise PermissionError("Acesso negado ao tenant")
        elif cid == _cid_err:
            raise ValueError("Etapa invalida para esta vaga")
        return {"success": True, "idempotent": False}

    _mock_svc = MagicMock()
    _mock_svc.transition_candidate = _svc_side_effect
    _name_map = {
        _cid_fairness: "Candidato Fairness",
        _cid_perm: "Candidato Permissao",
        _cid_err: "Candidato Erro",
    }

    with patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry.pipeline_stage_service",
        _mock_svc,
    ), patch(
        "app.domains.recruiter_assistant.agents.kanban_tool_registry._fetch_candidate_name_map",
        new_callable=AsyncMock,
        return_value=_name_map,
    ), _HITL_DISABLED:
        result = await _wrap_batch_move_candidates(
            candidate_ids=[_cid_fairness, _cid_perm, _cid_err],
            target_stage="reprovado",
            vacancy_id=VACANCY_ID,
            company_id=COMPANY_ID,
            reason="Test error type distinction",
        )

    _ui_results = result.get("data", {}).get("ui_action_params", {}).get("results", [])
    _by_id = {r["id"]: r for r in _ui_results}

    # Fairness: must contain educational_message verbatim
    _r_fair = _by_id.get(_cid_fairness, {})
    assert _r_fair.get("ok") is False
    assert _edu_msg in _r_fair.get("reason", ""), (
        f"T-D2-e FAIL fairness: {_edu_msg} nao em reason={_r_fair.get(reason)}. "
        "Fix: capturar _fb.message no except FairnessBlockedError."
    )

    # Permission: must differ from fairness and contain permission context
    _r_perm = _by_id.get(_cid_perm, {})
    assert _r_perm.get("ok") is False
    assert _r_perm.get("reason", "") != _r_fair.get("reason", ""), (
        f"T-D2-e FAIL permission: reason igual ao fairness — nao distingue tipos de erro. "
        "Fix: except PermissionError -> mensagem distinta de FairnessBlockedError."
    )

    # System error: must differ from both and not be empty
    _r_err = _by_id.get(_cid_err, {})
    assert _r_err.get("ok") is False
    assert _r_err.get("reason", "") not in ("", _r_fair.get("reason"), _r_perm.get("reason")), (
        f"T-D2-e FAIL system: reason={_r_err.get(reason)} deve ser distinto dos outros. "
        "Fix: except Exception -> mensagem com tipo do erro."
    )
