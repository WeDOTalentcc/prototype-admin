"""Agent Studio Fase 2.5 — Onda C1.3.

Sensores TDD dos publishers de eventos de plataforma:
  - candidate_applied  (apply nativo: applications.apply_to_vacancy)
  - candidate_applied  (apply web:   job_vacancies.public.apply_to_public_vacancy)
  - stage_changed      (kanban move: candidates_crud.update_candidate_stage)
  - stage_changed      (triagem:     candidates_metadata.screening_decision)

Invariantes verificadas:
  1. Apply nativo emite candidate_applied com company_id correto (do contexto
     do tenant, NUNCA do request) + candidate_id + vacancy_id.
  2. Stage change emite stage_changed com from_stage/to_stage.
  3. Falha de publish (RabbitMQ down) NAO quebra a operacao do usuario +
     logger.error chamado (REGRA 4: fail-soft mas LOUD).
  4. Multi-tenancy: company_id no payload vem do contexto, nao inventado/forjado.

Os publishers usam import LOCAL de `publish_platform_event`, entao o patch e
aplicado no modulo-fonte `app.shared.messaging.platform_events`.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PLATFORM_EVENTS_MOD = "app.shared.messaging.platform_events"
COMPANY_ID = "11111111-1111-1111-1111-111111111111"
OTHER_COMPANY = "99999999-9999-9999-9999-999999999999"
CANDIDATE_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
VACANCY_ID = "vvvvvvvv-vvvv-vvvv-vvvv-vvvvvvvvvvvv"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _emitted(mock_emit, event_type: str) -> list:
    return [
        c for c in mock_emit.await_args_list
        if c.args and getattr(c.args[0], "event_type", "") == event_type
    ]


# ─────────────────────────────────────────────────────────────────────────────
# C1.3.2 — stage_changed (kanban move via update_candidate_stage)
# ─────────────────────────────────────────────────────────────────────────────

def _make_stage_request(stage="entrevista", job_vacancy_id=VACANCY_ID, user_id="recruiter-1"):
    from app.schemas.candidate import CandidateStageUpdate
    return CandidateStageUpdate(
        stage=stage, sub_status=None, job_vacancy_id=job_vacancy_id, user_id=user_id
    )


def _make_stage_deps(vc_company_id=COMPANY_ID, previous_stage="triagem", new_stage="entrevista"):
    candidate = SimpleNamespace(id=CANDIDATE_ID, name="Maria", status="triagem")
    candidate_repo = MagicMock()
    candidate_repo.db = MagicMock()
    candidate_repo.get_by_id_str = AsyncMock(return_value=candidate)
    candidate_repo.update = AsyncMock(return_value=candidate)

    vacancy_candidate = SimpleNamespace(
        stage=previous_stage,
        status="screening",
        vacancy_id=VACANCY_ID,
        company_id=vc_company_id,
        lia_score=70.0,
        updated_at=None,
        rejected_by_human=False,
        human_reviewer_id=None,
    )
    vc_repo = MagicMock()
    vc_repo.get_for_candidate_and_job = AsyncMock(return_value=vacancy_candidate)

    async def _update(vc):
        # simula o que o endpoint ja fez (vc.stage = new_stage) — o publisher
        # le vacancy_candidate.stage depois do update
        return vc

    vc_repo.update = AsyncMock(side_effect=_update)
    return candidate, candidate_repo, vacancy_candidate, vc_repo


async def _call_update_candidate_stage(candidate_repo, vc_repo, request):
    from app.api.v1.candidates import candidates_crud as mod

    audit_svc = MagicMock()
    activity_svc = MagicMock()
    current_user = SimpleNamespace(id="recruiter-1", role="admin")
    bg = MagicMock()
    bg.add_task = MagicMock()

    # Neutraliza dependencias fora do escopo (calibracao/fairness/mutation gate).
    with patch.object(mod, "assert_mutation_allowed", new=AsyncMock()), \
         patch.object(mod, "CalibrationService") as _cal_cls, \
         patch.object(mod, "check_rejection_reason") as _frg:
        _cal_inst = MagicMock()
        _cal_inst.record_implicit_feedback = AsyncMock()
        _cal_cls.return_value = _cal_inst
        _frg.return_value = SimpleNamespace(is_blocked=False, blocked_result=None)
        return await mod.update_candidate_stage(
            candidate_id=CANDIDATE_ID,
            stage_data=request,
            background_tasks=bg,
            candidate_repo=candidate_repo,
            vc_repo=vc_repo,
            audit_svc=audit_svc,
            activity_svc=activity_svc,
            current_user=current_user,
            company_id=COMPANY_ID,
        )


@pytest.mark.asyncio
async def test_update_candidate_stage_emits_stage_changed():
    """Mover candidato de stage emite stage_changed com from/to + company_id da row."""
    candidate, candidate_repo, vacancy_candidate, vc_repo = _make_stage_deps(
        vc_company_id=COMPANY_ID, previous_stage="triagem"
    )
    request = _make_stage_request(stage="entrevista")

    # O endpoint faz `vacancy_candidate.stage = stage_data.stage` antes do publish;
    # simulamos isso patchando update para refletir o novo stage.
    async def _apply_new_stage(vc):
        return vc
    vc_repo.update = AsyncMock(side_effect=_apply_new_stage)

    with patch(f"{PLATFORM_EVENTS_MOD}.publish_platform_event",
               new=AsyncMock(return_value=True)) as mock_emit:
        await _call_update_candidate_stage(candidate_repo, vc_repo, request)

    found = _emitted(mock_emit, "stage_changed")
    assert len(found) == 1, f"esperava 1 stage_changed, achei {len(found)}"
    evt = found[0].args[0]
    assert evt.company_id == COMPANY_ID
    assert evt.payload["candidate_id"] == CANDIDATE_ID
    assert evt.payload["vacancy_id"] == VACANCY_ID
    assert evt.payload["from_stage"] == "triagem"
    assert evt.payload["to_stage"] == "entrevista"


@pytest.mark.asyncio
async def test_stage_changed_multi_tenancy_uses_row_company_id():
    """company_id do evento vem da row vacancy_candidate, nao do request/contexto forjado."""
    candidate, candidate_repo, vacancy_candidate, vc_repo = _make_stage_deps(
        vc_company_id=OTHER_COMPANY, previous_stage="triagem"
    )
    request = _make_stage_request(stage="entrevista")

    with patch(f"{PLATFORM_EVENTS_MOD}.publish_platform_event",
               new=AsyncMock(return_value=True)) as mock_emit:
        await _call_update_candidate_stage(candidate_repo, vc_repo, request)

    found = _emitted(mock_emit, "stage_changed")
    assert len(found) == 1
    # company_id do evento = company_id da ROW (defesa em profundidade),
    # nao o COMPANY_ID passado como contexto da chamada.
    assert found[0].args[0].company_id == OTHER_COMPANY


@pytest.mark.asyncio
async def test_stage_changed_publish_failure_does_not_break_operation():
    """RabbitMQ down: stage update prossegue + logger.error chamado (REGRA 4 LOUD)."""
    from app.api.v1.candidates import candidates_crud as mod

    candidate, candidate_repo, vacancy_candidate, vc_repo = _make_stage_deps(
        vc_company_id=COMPANY_ID, previous_stage="triagem"
    )
    request = _make_stage_request(stage="entrevista")

    with patch(f"{PLATFORM_EVENTS_MOD}.publish_platform_event",
               new=AsyncMock(side_effect=RuntimeError("RabbitMQ down"))), \
         patch.object(mod.logger, "error") as mock_log_error:
        result = await _call_update_candidate_stage(candidate_repo, vc_repo, request)

    # Operacao prossegue (retorna resultado de sucesso, sem propagar a exception).
    assert result is not None
    assert result.get("stage") == "entrevista"
    # logger.error chamado com exc_info=True (LOUD, nao silencioso).
    assert mock_log_error.called, "esperava logger.error no fail-soft (REGRA 4)"
    loud = any(
        ("stage_changed" in str(c.args)) and (c.kwargs.get("exc_info") is True)
        for c in mock_log_error.call_args_list
    )
    assert loud, "fail-soft deve ser LOUD: logger.error(..., exc_info=True)"


@pytest.mark.asyncio
async def test_stage_changed_not_emitted_when_stage_unchanged():
    """Sem mudanca de stage (from == to) nao emite stage_changed (evita ruido)."""
    candidate, candidate_repo, vacancy_candidate, vc_repo = _make_stage_deps(
        vc_company_id=COMPANY_ID, previous_stage="entrevista"
    )
    request = _make_stage_request(stage="entrevista")  # mesmo stage

    with patch(f"{PLATFORM_EVENTS_MOD}.publish_platform_event",
               new=AsyncMock(return_value=True)) as mock_emit:
        await _call_update_candidate_stage(candidate_repo, vc_repo, request)

    assert len(_emitted(mock_emit, "stage_changed")) == 0


# ─────────────────────────────────────────────────────────────────────────────
# C1.3.3 — schema canonical
# ─────────────────────────────────────────────────────────────────────────────

def test_candidate_applied_event_schema_canonical():
    from app.shared.messaging.platform_events import CandidateAppliedEvent
    evt = CandidateAppliedEvent(
        company_id=COMPANY_ID,
        payload={"candidate_id": CANDIDATE_ID, "vacancy_id": VACANCY_ID},
    )
    assert evt.event_type == "candidate_applied"
    assert evt.source_api == "lia-agent-system"
    assert evt.company_id == COMPANY_ID
    assert evt.payload["candidate_id"] == CANDIDATE_ID
    assert evt.payload["vacancy_id"] == VACANCY_ID
    # serializa pra publish (routing key = event_type flat).
    dumped = evt.model_dump(mode="json")
    assert dumped["event_type"] == "candidate_applied"


def test_stage_changed_event_schema_canonical():
    from app.shared.messaging.platform_events import StageChangedEvent
    evt = StageChangedEvent(
        company_id=COMPANY_ID,
        payload={
            "candidate_id": CANDIDATE_ID,
            "vacancy_id": VACANCY_ID,
            "from_stage": "triagem",
            "to_stage": "entrevista",
        },
    )
    assert evt.event_type == "stage_changed"
    assert evt.source_api == "lia-agent-system"
    assert evt.payload["from_stage"] == "triagem"
    assert evt.payload["to_stage"] == "entrevista"


# ─────────────────────────────────────────────────────────────────────────────
# C1.3.1 — candidate_applied (apply nativo via applications.apply_to_vacancy)
# ─────────────────────────────────────────────────────────────────────────────

def _make_apply_deps(vacancy_company_id=COMPANY_ID, existing_vc=None, adherence=80.0):
    """Monta repo/services mockados para apply_to_vacancy."""
    vacancy = SimpleNamespace(
        id=VACANCY_ID,
        title="QA Engineer",
        status="open",
        company_id=vacancy_company_id,
        company_name="ACME",
        required_skills=["python"],
        min_experience_years=2,
        seniority_level="pleno",
        location_city="SP",
        governance_rules={},
    )
    candidate = SimpleNamespace(
        id=CANDIDATE_ID,
        name="Joao",
        lia_score=None,
        skills_match_percentage=None,
        lia_insights=None,
    )

    repo = MagicMock()
    repo.db = MagicMock()
    repo.get_vacancy_by_id = AsyncMock(return_value=vacancy)
    repo.get_candidate_by_email = AsyncMock(return_value=None)
    repo.create_candidate = AsyncMock(return_value=candidate)
    repo.flush = AsyncMock()
    repo.get_vacancy_candidate = AsyncMock(return_value=existing_vc)
    repo.get_company_threshold = AsyncMock(return_value=20)
    repo.count_organic_candidates = AsyncMock(return_value=0)
    repo.create_vacancy_candidate = AsyncMock()
    repo.get_job_requirements = AsyncMock(return_value=[])
    repo.rollback = AsyncMock()
    return vacancy, candidate, repo


async def _call_apply_to_vacancy(repo):
    from app.api.v1 import applications as mod

    request = mod.CandidateApplicationRequest(
        name="Joao", email="joao@example.com", phone="11999998888",
    )
    cv_parser_svc = MagicMock()
    rubric_svc = MagicMock()
    rubric_svc.evaluate_and_create_activity = AsyncMock()

    score = SimpleNamespace(
        score=80.0,
        matched_skills=["python"],
        missing_skills=[],
        breakdown=SimpleNamespace(skills_match=80.0),
        to_dict=lambda: {"score": 80.0},
    )

    with patch.object(mod.lia_score_service, "calculate_score", return_value=score), \
         patch.object(mod.notification_service, "create_notification", new=AsyncMock()), \
         patch.object(mod.candidate_feedback_service, "ADHERENCE_THRESHOLD", 50.0), \
         patch("app.shared.services.automated_decision_logger.log_automated_decision",
               new=AsyncMock()):
        return await mod.apply_to_vacancy(
            vacancy_id=VACANCY_ID,
            application=request,
            cv_file=None,
            repo=repo,
            cv_parser_svc=cv_parser_svc,
            rubric_svc=rubric_svc,
            company_id=COMPANY_ID,
        )


@pytest.mark.asyncio
async def test_apply_to_vacancy_emits_candidate_applied():
    """Apply nativo emite candidate_applied com company_id da vaga (contexto tenant)."""
    vacancy, candidate, repo = _make_apply_deps(vacancy_company_id=COMPANY_ID)

    with patch(f"{PLATFORM_EVENTS_MOD}.publish_platform_event",
               new=AsyncMock(return_value=True)) as mock_emit:
        await _call_apply_to_vacancy(repo)

    found = _emitted(mock_emit, "candidate_applied")
    assert len(found) == 1, f"esperava 1 candidate_applied, achei {len(found)}"
    evt = found[0].args[0]
    assert evt.company_id == COMPANY_ID
    assert evt.payload["candidate_id"] == CANDIDATE_ID
    assert evt.payload["vacancy_id"] == VACANCY_ID


@pytest.mark.asyncio
async def test_apply_candidate_applied_multi_tenancy_uses_vacancy_company_id():
    """company_id do evento vem de vacancy.company_id (tenant da vaga), nao do request."""
    vacancy, candidate, repo = _make_apply_deps(vacancy_company_id=OTHER_COMPANY)

    with patch(f"{PLATFORM_EVENTS_MOD}.publish_platform_event",
               new=AsyncMock(return_value=True)) as mock_emit:
        await _call_apply_to_vacancy(repo)

    found = _emitted(mock_emit, "candidate_applied")
    assert len(found) == 1
    assert found[0].args[0].company_id == OTHER_COMPANY


@pytest.mark.asyncio
async def test_apply_publish_failure_does_not_break_application():
    """RabbitMQ down no apply: candidatura prossegue + logger.error LOUD."""
    from app.api.v1 import applications as mod

    vacancy, candidate, repo = _make_apply_deps(vacancy_company_id=COMPANY_ID)

    with patch(f"{PLATFORM_EVENTS_MOD}.publish_platform_event",
               new=AsyncMock(side_effect=RuntimeError("RabbitMQ down"))), \
         patch.object(mod.logger, "error") as mock_log_error:
        result = await _call_apply_to_vacancy(repo)

    assert result is not None
    assert getattr(result, "status", None) == "accepted"
    assert mock_log_error.called
    loud = any(
        ("candidate_applied" in str(c.args)) and (c.kwargs.get("exc_info") is True)
        for c in mock_log_error.call_args_list
    )
    assert loud, "fail-soft deve ser LOUD: logger.error(..., exc_info=True)"
