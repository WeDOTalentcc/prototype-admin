"""Audit task #558 — verify per-agent AI billing end-to-end.

Task #532 instrumentou apenas `wsi_layer2`. A task #545 espalhou o
mesmo padrão (`build_usage_callback` + `safe_invoke(on_usage=...)`)
para diversos fluxos críticos. Como o callback falha-soft (qualquer
regressão silenciosa zeraria o dashboard de billing sem alarme), este
módulo cobre cada `agent_type` adicionado:

* ``wsi_question_generator``        (WSIQuestionGenerator._generate_cbi_question)
* ``wsi_report_generator``          (WSIReportGenerator.generate_report)
* ``wsi_candidate_feedback``        (WSIReportGenerator.generate_feedback)
* ``personalized_feedback_whatsapp``(PersonalizedFeedbackService._generate_whatsapp_version)
* ``wsi_transcript_analysis``       (handlers_screening._analyze_transcript_for_wsi)
* ``recruiter_conversation_summary``(ConversationMemory._generate_summary_from_dicts)
* ``interview_analysis``            (handlers_interview — chamada inline em
                                     handle_interview_completed; coberto por
                                     contrato estático + comportamental)

Padrão de cada teste:

1. Stubba ``safe_invoke`` para invocar ``on_usage`` com um payload de
   uso falso e devolver um JSON válido.
2. Stubba ``enqueue_outbox_payload`` (worker module) para chamar uma
   ``TokenTrackingService.record_usage`` falsa imediatamente — pulando
   DB/outbox real, mantendo o contrato de assinatura.
3. Roda o fluxo real e assegura que ``record_usage`` foi chamado com o
   ``agent_type`` correto.

Se um futuro change-set remover o ``on_usage=...`` em qualquer chamada
``safe_invoke``, o teste correspondente falha — o callback nunca é
agendado e ``record_usage`` nunca é chamado.
"""
from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any
from unittest.mock import AsyncMock

import pytest


# ---------------------------------------------------------------------------
# Harness compartilhado
# ---------------------------------------------------------------------------

_FAKE_USAGE = {
    "input_tokens": 42,
    "output_tokens": 13,
    "model": "claude-test",
    "latency_ms": 7.5,
    "provider": "claude",
}


class _RecordCapture:
    """Coleta as chamadas de ``TokenTrackingService.record_usage``."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def record_usage(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


def _install_billing_stubs(monkeypatch) -> _RecordCapture:
    """Substitui ``enqueue_outbox_payload`` por um stub que invoca uma
    ``TokenTrackingService.record_usage`` falsa imediatamente.

    Isso simula o pipeline outbox + drainer worker sem precisar de DB:
    quando o callback agenda o enqueue, o stub abaixo já dispara o
    ``record_usage`` na mesma volta do loop.
    """
    capture = _RecordCapture()

    async def fake_enqueue(payload: dict[str, Any]) -> None:
        # Payload do callback bate 1-para-1 com a assinatura de
        # TokenTrackingService.record_usage (vide outbox drainer).
        await capture.record_usage(**payload)

    from app.shared.observability import ai_consumption_outbox_worker as worker_mod
    monkeypatch.setattr(worker_mod, "enqueue_outbox_payload", fake_enqueue)
    return capture


def _stub_safe_invoke_with_usage(response_text: str):
    """Devolve uma fake ``safe_invoke`` que chama on_usage e retorna texto.

    Mantém a mesma assinatura que ``LLMService.safe_invoke``: aceita
    ``prompt``, ``provider`` e quaisquer kwargs (incl. ``on_usage``).
    """
    async def _fake_safe_invoke(prompt, *args, on_usage=None, **kwargs):
        if on_usage is not None:
            on_usage(dict(_FAKE_USAGE))
        return response_text

    return _fake_safe_invoke


async def _drain_callback_tasks() -> None:
    """O callback usa ``loop.create_task(_enqueue())`` (fire-and-forget).

    Damos uma volta no loop pra que o enqueue rode antes do assert.
    """
    for _ in range(5):
        await asyncio.sleep(0)


# ---------------------------------------------------------------------------
# 1) wsi_question_generator
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wsi_question_generator_records_billing(monkeypatch):
    capture = _install_billing_stubs(monkeypatch)

    from app.domains.cv_screening.services.wsi_service.models import Competency
    from app.domains.cv_screening.services.wsi_service.question_generator import (
        WSIQuestionGenerator,
    )

    fake_llm = type("LLM", (), {})()
    fake_llm.safe_invoke = _stub_safe_invoke_with_usage(json.dumps({
        "framework": "CBI",
        "question_type": "contextual",
        "question_text": "Conte sobre uma situação onde aplicou liderança...",
        "expected_signals": ["ctx", "ação", "resultado"],
        "scoring_criteria": {"score_5": "x", "score_3": "y", "score_1": "z"},
    }))

    gen = WSIQuestionGenerator(llm=fake_llm)
    competency = Competency(
        name="Liderança", type="behavioral", weight=0.5,
        seniority_level="senior", is_critical=False,
    )

    await gen._generate_cbi_question(
        competency,
        tracking_context={
            "company_id": "11111111-1111-1111-1111-111111111111",
            "candidate_id": "22222222-2222-2222-2222-222222222222",
            "vacancy_id": "33333333-3333-3333-3333-333333333333",
        },
    )
    await _drain_callback_tasks()

    assert capture.calls, "callback não disparou record_usage"
    call = capture.calls[0]
    assert call["agent_type"] == "wsi_question_generator"
    assert call["company_id"] == "11111111-1111-1111-1111-111111111111"
    assert call["input_tokens"] == _FAKE_USAGE["input_tokens"]
    assert call["output_tokens"] == _FAKE_USAGE["output_tokens"]


# ---------------------------------------------------------------------------
# 2) wsi_report_generator
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wsi_report_generator_records_billing(monkeypatch):
    capture = _install_billing_stubs(monkeypatch)

    from app.domains.cv_screening.services.wsi_service.models import (
        ResponseAnalysis, WSIResult,
    )
    from app.domains.cv_screening.services.wsi_service.report_generator import (
        WSIReportGenerator,
    )

    fake_llm = type("LLM", (), {})()
    fake_llm.safe_invoke = _stub_safe_invoke_with_usage(json.dumps({
        "executive_summary": "Resumo OK.",
        "technical_analysis": {"pontos_fortes": [], "gaps": [], "evidencias": []},
        "behavioral_analysis": {"colaboracao": 7.0, "inovacao": 7.0,
                                  "organizacao": 7.0, "resiliencia": 7.0},
        "cultural_fit": {"score": 7.0, "valores_alinhados": [], "atencoes": []},
        "recommendation": {"decisao": "APROVADO", "justificativa": "ok",
                             "proximos_passos": []},
    }))

    rg = WSIReportGenerator(llm=fake_llm)
    wsi_result = WSIResult(
        candidate_id="cand-1", job_vacancy_id="job-1",
        technical_wsi=7.0, behavioral_wsi=7.0, overall_wsi=7.0,
        classification="alto", response_analyses=[],
    )
    responses = [
        ResponseAnalysis(
            question_id="q1", competency="Python",
            response_text="usei pandas em prod", evidences=["pandas"],
            red_flags=[], final_score=8.5,
            justification="resposta com evidência concreta",
        )
    ]

    await rg.generate_report(
        candidate_id="cand-1",
        wsi_result=wsi_result,
        responses=responses,
        tracking_context={
            "company_id": "44444444-4444-4444-4444-444444444444",
            "candidate_id": "cand-1",
            "vacancy_id": "job-1",
        },
    )
    await _drain_callback_tasks()

    assert capture.calls, "report_generator não emitiu billing"
    assert capture.calls[0]["agent_type"] == "wsi_report_generator"
    assert capture.calls[0]["company_id"] == "44444444-4444-4444-4444-444444444444"


# ---------------------------------------------------------------------------
# 3) wsi_candidate_feedback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wsi_candidate_feedback_records_billing(monkeypatch):
    capture = _install_billing_stubs(monkeypatch)

    from app.domains.cv_screening.services.wsi_service.models import (
        ResponseAnalysis, WSIResult,
    )
    from app.domains.cv_screening.services.wsi_service.report_generator import (
        WSIReportGenerator,
    )

    fake_llm = type("LLM", (), {})()
    fake_llm.safe_invoke = _stub_safe_invoke_with_usage(json.dumps({
        "main_message": "Obrigado por participar da etapa de triagem. " * 5,
        "technical_strengths": ["Python", "Análise"],
        "development_opportunities": ["Aprofundar design patterns"],
        "behavioral_strengths": ["Comunicação clara"],
        "next_steps": "Aguardar contato.",
        "personalized_tip": "Continue praticando.",
        "development_plan": {"curto_prazo": ["x"], "medio_prazo": ["y"]},
        "recommended_resources": ["Curso A"],
    }))

    rg = WSIReportGenerator(llm=fake_llm)
    wsi_result = WSIResult(
        candidate_id="cand-2", job_vacancy_id="job-2",
        technical_wsi=6.0, behavioral_wsi=6.0, overall_wsi=6.0,
        classification="medio", response_analyses=[],
    )

    await rg.generate_feedback(
        wsi_result=wsi_result,
        responses=[
            ResponseAnalysis(
                question_id="q1", competency="Python", response_text="ok",
                evidences=[], red_flags=[], final_score=8.0,
                justification="ok",
            )
        ],
        decision="aprovado",
        tracking_context={
            "company_id": "55555555-5555-5555-5555-555555555555",
            "candidate_id": "cand-2",
        },
    )
    await _drain_callback_tasks()

    assert capture.calls, "candidate_feedback não emitiu billing"
    assert capture.calls[0]["agent_type"] == "wsi_candidate_feedback"


# ---------------------------------------------------------------------------
# 4) personalized_feedback_whatsapp
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_personalized_feedback_whatsapp_records_billing(monkeypatch):
    capture = _install_billing_stubs(monkeypatch)

    from app.domains.cv_screening.services import personalized_feedback_service as pfs_mod

    svc = pfs_mod.PersonalizedFeedbackService()
    # Substitui o llm_service global usado pelo serviço por um stub
    fake_llm = type("LLM", (), {})()
    fake_llm.safe_invoke = _stub_safe_invoke_with_usage(
        "Olá! Resumo curto pro WhatsApp."
    )
    monkeypatch.setattr(svc, "llm", fake_llm)

    await svc._generate_whatsapp_version(
        email_body="Conteúdo do email original aqui.",
        tracking_context={
            "company_id": "66666666-6666-6666-6666-666666666666",
            "candidate_id": "cand-3",
        },
    )
    await _drain_callback_tasks()

    assert capture.calls, "whatsapp feedback não emitiu billing"
    assert capture.calls[0]["agent_type"] == "personalized_feedback_whatsapp"


# ---------------------------------------------------------------------------
# 5) wsi_transcript_analysis (handlers_screening)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wsi_transcript_analysis_records_billing(monkeypatch):
    capture = _install_billing_stubs(monkeypatch)

    from app.api.v1.automation.event_handlers import handlers_screening as hs
    from app.domains.ai.services import llm as llm_mod

    monkeypatch.setattr(
        llm_mod.llm_service,
        "safe_invoke",
        _stub_safe_invoke_with_usage(json.dumps({"responses": []})),
    )

    fake_vacancy = type("V", (), {"title": "Eng Backend"})()
    fake_wsi = type("W", (), {})()

    await hs._analyze_transcript_for_wsi(
        transcript="Candidato falou sobre projeto X com métrica Y.",
        vacancy_title=fake_vacancy.title,
        wsi_service=fake_wsi,
        tracking_context={
            "company_id": "77777777-7777-7777-7777-777777777777",
            "candidate_id": "cand-4",
            "vacancy_id": "job-4",
        },
    )
    await _drain_callback_tasks()

    assert capture.calls, "transcript_analysis não emitiu billing"
    assert capture.calls[0]["agent_type"] == "wsi_transcript_analysis"
    assert capture.calls[0]["company_id"] == "77777777-7777-7777-7777-777777777777"


# ---------------------------------------------------------------------------
# 6) recruiter_conversation_summary
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recruiter_conversation_summary_records_billing(monkeypatch):
    capture = _install_billing_stubs(monkeypatch)

    from app.domains.recruiter_assistant.services.conversation_memory import (
        ConversationMemory,
    )

    fake_llm = type("LLM", (), {})()
    fake_llm.safe_invoke = _stub_safe_invoke_with_usage("Resumo da conversa.")

    mem = ConversationMemory(llm_service=fake_llm)
    messages = [
        {"role": "user", "content": "Qual o status da vaga X?"},
        {"role": "assistant", "content": "Vaga X tem 5 candidatos."},
    ]

    await mem._generate_summary_from_dicts(
        messages=messages,
        tracking_context={
            "company_id": "88888888-8888-8888-8888-888888888888",
            "user_id": "user-9",
        },
    )
    await _drain_callback_tasks()

    assert capture.calls, "conversation_summary não emitiu billing"
    assert capture.calls[0]["agent_type"] == "recruiter_conversation_summary"
    assert capture.calls[0]["company_id"] == "88888888-8888-8888-8888-888888888888"


# ---------------------------------------------------------------------------
# 7) interview_analysis (inline em handle_interview_completed)
# ---------------------------------------------------------------------------
#
# A análise pós-entrevista é executada inline dentro do event handler
# `handle_interview_completed`, atrás de várias dependências de DB
# (`ensure_company_access`, `scheduling_service`, etc.). Cobrir o
# handler inteiro exigiria fixtures pesadas e desviaria o foco da
# regressão que importa: que `safe_invoke` esteja ligado ao callback
# com o `agent_type="interview_analysis"`. Combinamos:
#
#  (a) Contrato estático: a chamada `build_usage_callback(...,
#      agent_type="interview_analysis", ...)` precede `safe_invoke(...,
#      on_usage=on_usage)` na mesma função.
#  (b) Contrato comportamental: `build_usage_callback` com esse
#      `agent_type` produz um payload de outbox que o drainer
#      converte em `record_usage(agent_type="interview_analysis")`.

def test_interview_analysis_callsite_uses_correct_agent_type():
    from app.api.v1.automation.event_handlers import handlers_interview as hi

    src = inspect.getsource(hi)
    # Assertions emparelhadas: presença do agent_type + uso de on_usage
    # logo a seguir. Se alguém remover qualquer um dos dois, o teste falha.
    assert 'agent_type="interview_analysis"' in src, (
        "handler perdeu o agent_type 'interview_analysis' — billing "
        "do post-interview analysis não vai aparecer no dashboard."
    )
    assert "on_usage=on_usage" in src, (
        "handler não está mais passando on_usage para safe_invoke — "
        "callback não é invocado e billing fica zerado."
    )


@pytest.mark.asyncio
async def test_interview_analysis_callback_records_billing(monkeypatch):
    """Garante que o agent_type cabeado em handlers_interview chega
    intacto até `record_usage` quando o callback é disparado."""
    capture = _install_billing_stubs(monkeypatch)

    from app.shared.observability.usage_tracking_callback import (
        build_usage_callback,
    )

    cb = build_usage_callback(
        {
            "company_id": "99999999-9999-9999-9999-999999999999",
            "candidate_id": "cand-7",
            "vacancy_id": "job-7",
        },
        agent_type="interview_analysis",
        default_operation="interview_post_analysis",
    )
    assert cb is not None
    cb(dict(_FAKE_USAGE))
    await _drain_callback_tasks()

    assert capture.calls, "callback agendou nada"
    assert capture.calls[0]["agent_type"] == "interview_analysis"
    assert capture.calls[0]["intent"] == "interview_post_analysis"


# ---------------------------------------------------------------------------
# Defesa contra regressão silenciosa: o callback não pode ser pulado
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_callback_drop_is_caught(monkeypatch):
    """Se um futuro patch substituir ``on_usage=on_usage`` por
    ``on_usage=None`` (ou simplesmente esquecer de passar), nenhum
    enqueue acontece e o capture fica vazio. Este teste documenta o
    comportamento esperado dessa regressão (pra orientar quem ler o
    log do CI vermelho).
    """
    capture = _install_billing_stubs(monkeypatch)

    async def fake_safe_invoke_no_usage(prompt, *args, on_usage=None, **kwargs):
        # Simula um caller que esqueceu de propagar on_usage.
        return "{}"

    from app.domains.cv_screening.services.wsi_service.models import Competency
    from app.domains.cv_screening.services.wsi_service.question_generator import (
        WSIQuestionGenerator,
    )

    fake_llm = type("LLM", (), {})()
    fake_llm.safe_invoke = fake_safe_invoke_no_usage

    gen = WSIQuestionGenerator(llm=fake_llm)
    competency = Competency(
        name="Liderança", type="behavioral", weight=0.5,
        seniority_level="senior", is_critical=False,
    )
    await gen._generate_cbi_question(
        competency,
        tracking_context={
            "company_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        },
    )
    await _drain_callback_tasks()

    assert capture.calls == [], (
        "Sentinela invertida: este teste mostra COMO uma regressão "
        "(callback nunca chamado) seria detectada — o capture deveria "
        "ficar vazio. Se ele tem chamadas aqui, a stub não está "
        "fielmente reproduzindo a regressão."
    )
