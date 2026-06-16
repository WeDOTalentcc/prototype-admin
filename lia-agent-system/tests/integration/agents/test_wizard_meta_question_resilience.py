"""Task #1123 — Sentinela: gates HITL respondem a meta-questions sem travar.

Os 4 gates HITL do wizard (jd_gate, competency_gate, wsi_questions_gate,
review_gate) devem responder a perguntas meta / off-topic /
ask_clarification SEM mutar state de aprovação E populando
``gate_clarify_message``. O Sonnet helper é OPCIONAL — se falhar
(ImportError, sem chave, exceção), o gate cai no
``output.conversational_reply`` do classifier. Em qualquer caminho,
o state permanece consistente.

≥8 cenários cobrindo as 4 stages × 2 paths (com helper / sem helper).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _classifier_output(intent: str, reply: str = "(classifier reply)", conf: float = 0.9, extracted: dict | None = None):
    """Stub para GateClassifierOutput sem importar Pydantic real."""
    out = MagicMock()
    out.intent = intent
    out.confidence = conf
    out.conversational_reply = reply
    out.extracted_data = extracted or {}
    return out


def _patch_classifier(intent: str, reply: str = "(classifier reply)", conf: float = 0.9, extracted: dict | None = None):
    """Patches get_wizard_gate_classifier + _make_fallback to control output."""
    output = _classifier_output(intent, reply, conf, extracted)
    classifier = MagicMock()

    async def _classify_async(**kwargs):
        return output

    classifier.classify = _classify_async
    return classifier


@pytest.fixture
def base_state():
    return {
        "user_id": "u-1",
        "workspace_id": "00000000-0000-4000-a000-000000000001",
        "session_id": "s-1",
        "tenant_context_snippet": "Demo Company (Tecnologia, enterprise).",
        "hiring_policy_summary": "",
        "conversation_messages": [
            {"role": "assistant", "content": "Aqui está a JD enriquecida. Aprova?"},
        ],
        "gate_resume_message": "tem mais alguma coisa que você precisa pra começar?",
        "jd_enriched": {"title": "Engenheiro Backend"},
        "jd_approved": None,
        "raw_input": "Engenheiro Backend Pleno",
        "user_query": "tem mais alguma coisa que você precisa pra começar?",
        "current_stage": "jd_enrichment",
    }


# ────────────────── jd_gate (ask_question + off_topic) ──────────────────

def test_jd_gate_ask_question_with_sonnet_helper(base_state):
    """jd_gate + ask_question + Sonnet OK → reply do Sonnet em gate_clarify_message."""
    from app.domains.job_creation import graph as g

    classifier = _patch_classifier("ask_question", "fallback reply", 0.9)
    with patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_meta_question_helper."
        "generate_meta_response_sync",
        return_value="Posso enriquecer a JD com o setor da Demo Company. Quer aprovar agora?",
    ):
        result = g.jd_gate_node(base_state)

    assert "Demo Company" in (result.get("gate_clarify_message") or "")
    assert result.get("jd_approved") is None  # state inalterado
    assert result.get("gate_last_intent") == "ask_question"


def test_jd_gate_ask_question_sonnet_fails_fallback_to_classifier(base_state):
    """jd_gate + ask_question + Sonnet FAIL → cai no classifier reply."""
    from app.domains.job_creation import graph as g

    classifier = _patch_classifier("ask_question", "Posso explicar o que enriqueci.", 0.9)
    with patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_meta_question_helper."
        "generate_meta_response_sync",
        side_effect=Exception("simulated LLM failure"),
    ):
        result = g.jd_gate_node(base_state)

    assert result.get("gate_clarify_message") == "Posso explicar o que enriqueci."
    assert result.get("jd_approved") is None


def test_jd_gate_off_topic_with_sonnet(base_state):
    """jd_gate + off_topic + Sonnet → state inalterado + reply do Sonnet."""
    from app.domains.job_creation import graph as g

    base_state["gate_resume_message"] = "como tá o tempo aí?"
    base_state["user_query"] = "como tá o tempo aí?"
    classifier = _patch_classifier("off_topic", "small talk reply", 0.85)
    with patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_meta_question_helper."
        "generate_meta_response_sync",
        return_value="Vamos focar na JD da Demo Company. Aprova ou ajusta?",
    ):
        result = g.jd_gate_node(base_state)

    assert "Demo Company" in (result.get("gate_clarify_message") or "")
    assert result.get("jd_approved") is None


# ────────────────── competency_gate (ask_question) ──────────────────

def test_competency_gate_ask_question_with_sonnet(base_state):
    """competency_gate + ask_question + Sonnet → reply do Sonnet."""
    from app.domains.job_creation import graph as g

    state = {
        **base_state,
        "current_stage": "competency",
        "seniority_resolved": "pleno",
        "screening_mode": None,
        "gate_resume_message": "qual a diferença mesmo?",
        "user_query": "qual a diferença mesmo?",
    }
    classifier = _patch_classifier("ask_question", "Compacto tem 7 perguntas.", 0.9)
    with patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_meta_question_helper."
        "generate_meta_response_sync",
        return_value="Pra Pleno o Compacto (7q) cobre 5 técnicas + 2 comportamentais. Vamos com Compacto?",
    ):
        result = g.competency_gate_node(state)

    msg = result.get("gate_clarify_message") or ""
    assert "Compacto" in msg
    assert result.get("screening_mode") is None  # state inalterado
    assert result.get("gate_last_intent") == "ask_question"


def test_competency_gate_ask_question_sonnet_fails(base_state):
    """competency_gate + ask_question + Sonnet FAIL → cai no classifier reply."""
    from app.domains.job_creation import graph as g

    state = {
        **base_state,
        "current_stage": "competency",
        "seniority_resolved": "pleno",
        "screening_mode": None,
        "gate_resume_message": "qual a diferença mesmo?",
        "user_query": "qual a diferença mesmo?",
    }
    classifier_reply = "Compacto (7) é mais ágil; Completo (12) tem mais evidência."
    classifier = _patch_classifier("ask_question", classifier_reply, 0.9)
    with patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_meta_question_helper."
        "generate_meta_response_sync",
        side_effect=Exception("simulated"),
    ):
        result = g.competency_gate_node(state)

    assert classifier_reply in (result.get("gate_clarify_message") or "")
    assert result.get("screening_mode") is None


# ────────────────── wsi_questions_gate (ask_question) ──────────────────

def test_wsi_gate_ask_question_with_sonnet(base_state):
    """wsi_questions_gate + ask_question + Sonnet → reply contextual."""
    from app.domains.job_creation import graph as g

    state = {
        **base_state,
        "current_stage": "wsi_questions",
        "wsi_questions": [{"q": "Q1"}, {"q": "Q2"}, {"q": "Q3"}],
        "questions_approved": None,
        "gate_resume_message": "por que essas 3?",
        "user_query": "por que essas 3?",
    }
    classifier = _patch_classifier("ask_question", "Pacote gerado a partir do WSI.", 0.9)
    with patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_meta_question_helper."
        "generate_meta_response_sync",
        return_value="As 3 cobrem stack + comportamental. Quer aprovar ou editar alguma?",
    ):
        result = g.wsi_questions_gate_node(state)

    assert "Quer aprovar" in (result.get("gate_clarify_message") or "")
    assert result.get("questions_approved") is None


def test_wsi_gate_ask_question_sonnet_fails(base_state):
    """wsi_questions_gate + ask_question + Sonnet FAIL → cai no classifier."""
    from app.domains.job_creation import graph as g

    state = {
        **base_state,
        "current_stage": "wsi_questions",
        "wsi_questions": [{"q": "Q1"}, {"q": "Q2"}],
        "questions_approved": None,
        "gate_resume_message": "qual a metodologia?",
        "user_query": "qual a metodologia?",
    }
    classifier_reply = "WSI é a metodologia da WeDoTalent. Quer ver o detalhe?"
    classifier = _patch_classifier("ask_question", classifier_reply, 0.9)
    with patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_meta_question_helper."
        "generate_meta_response_sync",
        side_effect=Exception("simulated"),
    ):
        result = g.wsi_questions_gate_node(state)

    assert classifier_reply in (result.get("gate_clarify_message") or "")
    assert result.get("questions_approved") is None


# ────────────────── review_gate (ask_clarification) ──────────────────

def test_review_gate_ask_clarification_with_sonnet(base_state):
    """review_gate + ask_clarification + Sonnet → reply do Sonnet em
    gate_clarify_message; state de publicação inalterado.

    Task #1123 — fechamento da cobertura dos 4 HITL gates.
    """
    from app.domains.job_creation import graph as g

    state = {
        **base_state,
        "current_stage": "review",
        "published": None,
        "publish_destinations": ["gupy", "linkedin"],
        "gate_resume_message": "esse pipeline é o padrão da empresa?",
        "user_query": "esse pipeline é o padrão da empresa?",
        "ws_stage_payload": {"data": {"pipeline_template": "default"}},
    }
    classifier_reply = "Esse pipeline veio do default. Quer ajustar?"
    classifier = _patch_classifier("ask_clarification", classifier_reply, 0.9)
    with patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_meta_question_helper."
        "generate_meta_response_sync",
        return_value="O pipeline é o default da Demo Company configurado em Settings. Quer ajustar alguma etapa antes de publicar?",
    ):
        result = g.review_gate_node(state)

    msg = result.get("gate_clarify_message") or ""
    assert "Demo Company" in msg, (
        f"Sonnet reply (tenant-aware) deveria estar em gate_clarify_message, got: {msg}"
    )
    assert result.get("published") in (None, False)


def test_review_gate_ask_clarification_sonnet_fails(base_state):
    """review_gate + ask_clarification + Sonnet FAIL → cai no classifier reply.

    Garante fail-OPEN: helper exception não trava o gate.
    """
    from app.domains.job_creation import graph as g

    state = {
        **base_state,
        "current_stage": "review",
        "published": None,
        "publish_destinations": ["gupy"],
        "gate_resume_message": "o que é esse score WSI no resumo?",
        "user_query": "o que é esse score WSI no resumo?",
        "ws_stage_payload": {"data": {"pipeline_template": "default"}},
    }
    classifier_reply = "O score WSI é a metodologia WeDoTalent. Quer ver mais?"
    classifier = _patch_classifier("ask_clarification", classifier_reply, 0.9)
    with patch(
        "app.domains.job_creation.services.wizard_gate_classifier.get_wizard_gate_classifier",
        return_value=classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_meta_question_helper."
        "generate_meta_response_sync",
        side_effect=Exception("simulated LLM failure"),
    ):
        result = g.review_gate_node(state)

    msg = result.get("gate_clarify_message") or ""
    assert classifier_reply in msg, (
        f"Fail-OPEN deveria cair no classifier reply, got: {msg}"
    )
    assert result.get("published") in (None, False)


# ────────────────── helper module presence ──────────────────

def test_meta_helper_module_importable():
    """O módulo Sonnet helper DEVE estar importável (sentinela
    arquitetural — se renomearem o módulo, esta sentinela falha)."""
    from app.domains.job_creation.services import wizard_meta_question_helper
    assert hasattr(wizard_meta_question_helper, "generate_meta_response_sync")


def test_meta_helper_returns_none_without_api_key(monkeypatch):
    """Helper devolve None (NUNCA levanta) quando não há API key."""
    monkeypatch.delenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from app.domains.job_creation.services.wizard_meta_question_helper import (
        generate_meta_response_sync,
    )
    result = generate_meta_response_sync(
        stage="jd_enrichment",
        user_message="o que você precisa?",
        tenant_context_snippet="Demo Company.",
        last_turns=[],
        stage_description="HITL #1",
    )
    assert result is None
