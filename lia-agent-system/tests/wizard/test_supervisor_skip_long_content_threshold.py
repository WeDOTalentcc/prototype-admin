"""Sprint F.2-v2 (2026-05-26) — Sensor: supervisor SKIP must NOT swallow
long substantial content (JD pastes, briefings) during an active wizard
stage. Only short prompt-answers ("sim", "ok", "modo compacto") may be
skipped — long content MUST re-classify so the graph can ingest it.

Bug history (transcript Paulo 2026-05-26):
  Turn 1: user "vamos abrir uma vaga" (~20 chars) → classifier=intent_only
          → input-thin guard fires → template "preciso de mais contexto"
          → state.current_stage = "jd_enrichment", HITL gate active.
  Turn 2: user pastes 1500-char JD with responsibilities, requirements,
          frameworks, soft skills.
  ❌ Sprint F.2 skip BINARIO (prior_stage in ACTIVE_WIZARD_STAGES) skipa
     supervisor → JD chega como "answer to HITL prompt" → graph não
     re-classifica → template "preciso de mais contexto" repete → loop.

Sprint F.2-v2 fix: skip APENAS quando msg_len < 100 chars. Threshold
empírico: JD real começa em ~120 chars (graph.py:842 documenta esse
mesmo número), prompt-answers ficam < 30 chars. Margem de 100 dá folga
pra ambos sem ambiguidade.

Esse sensor parametriza:
  (a) 8 active stages × 3 long-content cases → supervisor DEVE rodar
  (b) 8 active stages × 5 short HITL replies   → supervisor SKIP (mantém
      Sprint F.2 sensor adjacente — defesa em profundidade)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


ACTIVE_STAGES = (
    "jd_enrichment", "bigfive", "salary", "competency",
    "wsi_questions", "eligibility", "review", "publish",
)

# Long content: JD pastes, briefings, structured replies that must re-classify.
LONG_CONTENT_CASES = (
    # JD completa estilo transcript Paulo
    (
        "Desenvolvedor Python Sênior com sólida experiência (5+ anos) em "
        "backend. Responsabilidades: arquitetura de aplicações escaláveis, "
        "code reviews, mentoria de devs plenos/juniores. Requisitos: FastAPI "
        "ou Django, PostgreSQL, Docker, AWS/GCP/Azure, Git. Soft skills: "
        "comunicação, autonomia, senso crítico."
    ),
    # Briefing de cargo com critérios
    (
        "Quero abrir vaga de cientista de dados sênior em São Paulo, modelo "
        "remoto, salário entre 15-20k. Stack obrigatória: Python, SQL, ML. "
        "Diferencial: deep learning, MLOps. Inicia em 2 semanas."
    ),
    # Resposta longa mas com intent de continuação (e.g. user esclarece JD)
    (
        "Esse cargo de Tech Lead substitui a posição do Carlos que saiu mês "
        "passado. Foco: liderança técnica de 8 devs, arquitetura cloud-native, "
        "integração com nosso ERP legado em Java. Senioridade obrigatória."
    ),
)

# Short HITL prompt-answers: TUDO < 100 chars, devem manter Sprint F.2 skip.
SHORT_HITL_REPLIES = (
    "sim",
    "ok",
    "aprovado",
    "modo compacto",
    "modo compacto, 7 perguntas",  # ~30 chars — borda safe
)


def _enable_supervisor_env(monkeypatch):
    monkeypatch.setenv("LIA_WIZARD_SUPERVISOR_CLASSIFIER", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    monkeypatch.delenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", raising=False)


async def _drive(monkeypatch, *, prior_stage, user_message):
    """Drive WizardSessionService.process_message with mocks. Returns
    ``(supervisor_called_count, graph_resume_count)``.

    Mirror of `_drive` em test_supervisor_classifier_skips_active_session.py
    — duplicated (não importado) para isolar pytest discovery scope.
    """
    _enable_supervisor_env(monkeypatch)

    from app.domains.job_creation.services import (
        wizard_session_service as wss_mod,
    )
    WSS = wss_mod.WizardSessionService

    prior_state = (
        {"current_stage": prior_stage, "conversation_messages": []}
        if prior_stage is not None
        else {}
    )

    supervisor_spy = AsyncMock(
        return_value={"intent": "continue_current", "short_circuit": False},
    )
    aresume_spy = AsyncMock(
        return_value={"messages": [], "current_stage": prior_stage or "intake"},
    )
    is_interrupted_spy = MagicMock(return_value=True)
    post_process_spy = AsyncMock(return_value=("reply", {}, 0))
    fake_graph = MagicMock()
    fake_graph.is_interrupted = is_interrupted_spy
    fake_graph.aresume_with_message = aresume_spy

    monkeypatch.setattr(
        WSS, "_get_prior_state",
        AsyncMock(return_value=prior_state),
    )
    monkeypatch.setattr(WSS, "_run_supervisor", supervisor_spy)
    monkeypatch.setattr(WSS, "_post_process_result", post_process_spy)

    monkeypatch.setattr(
        "app.domains.job_creation.graph.get_job_creation_graph",
        lambda: fake_graph,
    )

    await WSS.process_message(
        thread_id="thr-test-long",
        user_message=user_message,
        user_id="user-test",
        company_id="company-test",
        session_id="sess-test",
        context={},
    )
    return supervisor_spy.await_count, aresume_spy.await_count


# ─────────────────────────────────────────────────────────────────────
# CORE SENSOR — Sprint F.2-v2: supervisor MUST RUN for long content
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ACTIVE_STAGES)
@pytest.mark.parametrize("long_msg", LONG_CONTENT_CASES)
async def test_supervisor_RUNS_when_active_stage_BUT_long_content(
    monkeypatch, stage, long_msg,
):
    """Sprint F.2-v2 (2026-05-26) — JD/briefing substancial colado durante
    stage ativa do wizard NÃO pode ser engolido pelo Sprint F.2 skip.
    Supervisor DEVE rodar e classificar a intenção real (continue_current
    se é continuação legítima, create_new se mudou contexto).

    Causa raiz histórica: transcript Paulo 2026-05-26 mostrou JD 1500 chars
    sendo ignorada porque skip era binário (prior_stage in ACTIVE_STAGES)
    sem considerar substância do user_message.
    """
    assert len(long_msg) >= 100, (
        f"Test fixture inválida — long_msg precisa ter >= 100 chars, "
        f"got {len(long_msg)}: {long_msg!r}"
    )
    sup_calls, resume_calls = await _drive(
        monkeypatch, prior_stage=stage, user_message=long_msg,
    )
    assert sup_calls == 1, (
        f"supervisor was SKIPPED for stage={stage!r} + long_msg "
        f"(len={len(long_msg)}) — Sprint F.2-v2 fix missing or "
        f"regressed. Long content during HITL gate MUST re-classify "
        f"(continue_current vs create_new vs meta_question) — engolir "
        f"JD substancial regrida o wizard em loop de 'preciso de mais "
        f"contexto' (transcript Paulo 2026-05-26)."
    )
    assert resume_calls == 1, (
        f"After supervisor runs and returns short_circuit=False, "
        f"graph aresume_with_message must still be invoked exactly "
        f"once (got {resume_calls})."
    )


# ─────────────────────────────────────────────────────────────────────
# REGRESSION GUARD — Sprint F.2 skip preserved for short HITL replies
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ACTIVE_STAGES)
@pytest.mark.parametrize("short_msg", SHORT_HITL_REPLIES)
async def test_supervisor_SKIPPED_when_active_stage_AND_short_reply(
    monkeypatch, stage, short_msg,
):
    """Sprint F.2 (2026-05-20) — proteção original mantida: respostas
    curtas durante HITL gate (< 100 chars) continuam skipando o
    supervisor pra não serem misrotuladas como create_new/meta_question.
    Esse teste duplica a intent do sensor adjacente
    ``test_supervisor_classifier_skips_active_session.py`` mas valida
    explicitamente o caminho do threshold (msg_len < 100).
    """
    assert len(short_msg.strip()) < 100, (
        f"Test fixture inválida — short_msg precisa ter < 100 chars, "
        f"got {len(short_msg)}: {short_msg!r}"
    )
    sup_calls, resume_calls = await _drive(
        monkeypatch, prior_stage=stage, user_message=short_msg,
    )
    assert sup_calls == 0, (
        f"supervisor was called {sup_calls}x for stage={stage!r} + "
        f"short_msg={short_msg!r} — Sprint F.2-v2 must preserve the "
        f"F.2 short-answer protection (sim/ok/modo compacto skipa)."
    )
    assert resume_calls == 1, (
        f"graph aresume_with_message must be invoked exactly once "
        f"for stage={stage!r}, got {resume_calls}."
    )


# ─────────────────────────────────────────────────────────────────────
# UNIT TEST — pure helper (independente de mocks pesados)
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("user_msg,prior_stage,expected_skip", [
    # Short prompt-answers DEVEM skipar (Sprint F.2 preserved)
    ("sim",                                "jd_enrichment", True),
    ("ok",                                 "bigfive",       True),
    ("aprovado",                           "review",        True),
    ("modo compacto",                      "competency",    True),
    ("modo compacto, 7 perguntas",         "wsi_questions", True),
    # Long content NÃO deve skipar (Sprint F.2-v2)
    ("a" * 100,                            "jd_enrichment", False),  # threshold exato
    ("a" * 150,                            "bigfive",       False),
    ("Desenvolvedor Python Senior com solida experiencia 5+ anos. Responsabilidades: arquitetura, code review e mentoria. Requisitos: FastAPI, PostgreSQL, Docker, AWS.",
                                           "jd_enrichment", False),
    # Sem prior_stage ativa → supervisor SEMPRE roda
    ("sim",                                None,            False),
    ("modo compacto",                      "intake",        False),
    ("ok",                                 "done",          False),
    ("ok",                                 "calibration",   False),
    ("ok",                                 "handoff",       False),
])
def test_compute_supervisor_skip_helper(user_msg, prior_stage, expected_skip):
    """Helper module-level extractable, testável sem mocks.

    Contract:
      skip ⇔ (prior_stage in ACTIVE_WIZARD_STAGES) AND (msg_len < 100)
    """
    from app.domains.job_creation.services.wizard_session_service import (
        _compute_supervisor_skip,
    )
    assert _compute_supervisor_skip(user_msg, prior_stage) == expected_skip, (
        f"_compute_supervisor_skip({user_msg!r}, {prior_stage!r}) "
        f"esperado={expected_skip}, got {not expected_skip}"
    )
