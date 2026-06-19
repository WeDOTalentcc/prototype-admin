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
