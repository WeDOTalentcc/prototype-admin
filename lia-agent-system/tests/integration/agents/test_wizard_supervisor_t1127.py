"""Task #1127 — Sentinela offline do Wizard Supervisor Classifier (pre-graph).

Garante 3 contratos sem rede / sem LLM real:

1. **Flag-OFF respeita rollout** — quando ``LIA_WIZARD_SUPERVISOR_CLASSIFIER=0``
   o classifier devolve ``None`` imediatamente (fail-OPEN ao caller, que cai
   no fluxo legacy ``continue_current``).

2. **Allowlist enforced** — qualquer ``intent`` fora da allowlist canônica
   (``create_new | resume_draft | edit_published | meta_question |
   exit_wizard | continue_current``) é rejeitado e o classifier devolve
   ``None`` (defense-in-depth contra prompt-injection / drift do LLM).

3. **Short-circuit de meta_question / exit_wizard NÃO muta state** — o
   ``WizardSessionService._run_supervisor`` produz ``short_circuit=True``
   com payload ``wizard_meta_reply`` / ``wizard_exit``, e nunca toca
   ``conversation_messages`` ou flags de aprovação.

NÃO chama o LLM real — todas as chamadas Anthropic são patchadas.
"""
from __future__ import annotations

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Contract 1 — Flag-OFF respeita rollout
# ---------------------------------------------------------------------------


def test_supervisor_disabled_returns_none(monkeypatch):
    """Quando a flag está OFF, ``classify_sync`` devolve ``None`` sem
    nem tentar chamar o LLM. Garante zero custo no rollout gradual."""
    from app.domains.job_creation.services import wizard_supervisor_classifier as mod

    monkeypatch.setenv("LIA_WIZARD_SUPERVISOR_CLASSIFIER", "0")
    cls = mod.WizardSupervisorClassifier()
    out = cls.classify_sync(user_message="quero abrir vaga")
    assert out is None, "Flag OFF deveria curto-circuitar antes do LLM"


def test_supervisor_default_off_in_prod(monkeypatch):
    """Sem a flag explícita, supervisor deve estar OFF em prod/staging."""
    from app.domains.job_creation.services.wizard_supervisor_classifier import (
        is_supervisor_enabled,
    )
    monkeypatch.delenv("LIA_WIZARD_SUPERVISOR_CLASSIFIER", raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("LIA_ENV", raising=False)
    assert is_supervisor_enabled() is False

    monkeypatch.setenv("APP_ENV", "staging")
    assert is_supervisor_enabled() is False

    monkeypatch.setenv("APP_ENV", "development")
    assert is_supervisor_enabled() is True


# ---------------------------------------------------------------------------
# Contract 2 — Allowlist enforced (defense-in-depth)
# ---------------------------------------------------------------------------


def _build_mock_response(intent: str) -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.name = "classify_supervisor"
    block.input = {
        "intent": intent,
        "conversational_reply": "(stub)",
        "confidence": 0.92,
    }
    resp = MagicMock()
    resp.content = [block]
    return resp


def test_supervisor_off_allowlist_rejected(monkeypatch):
    """Intent fora da allowlist (ex.: ``delete_company``) deve devolver
    ``None`` em vez de propagar string maliciosa."""
    from app.domains.job_creation.services import wizard_supervisor_classifier as mod

    monkeypatch.setenv("LIA_WIZARD_SUPERVISOR_CLASSIFIER", "1")
    monkeypatch.setenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", "sk-stub-not-real")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    fake_client = MagicMock()
    fake_client.messages.create.return_value = _build_mock_response("delete_company")

    import anthropic as _anthropic_mod
    with patch.object(_anthropic_mod, "Anthropic", return_value=fake_client):
        cls = mod.WizardSupervisorClassifier()
        out = cls.classify_sync(user_message="qualquer coisa")

    assert out is None, "Off-allowlist intent não pode vazar pro caller"


def test_supervisor_valid_intent_returns_pydantic(monkeypatch):
    """Intent válido (``meta_question``) deve devolver
    ``SupervisorIntentOutput`` com schema Pydantic-validado."""
    from app.domains.job_creation.services import wizard_supervisor_classifier as mod

    monkeypatch.setenv("LIA_WIZARD_SUPERVISOR_CLASSIFIER", "1")
    monkeypatch.setenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", "sk-stub-not-real")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    fake_client = MagicMock()
    fake_client.messages.create.return_value = _build_mock_response("meta_question")

    with patch.object(mod, "Anthropic", return_value=fake_client, create=True):
        cls = mod.WizardSupervisorClassifier()
        out = cls.classify_sync(user_message="o que você precisa de mim?")

    assert out is not None
    assert out.intent == "meta_question"
    assert 0.0 <= out.confidence <= 1.0


def test_audit_decision_type_mapping_registered():
    """T2.2 — ``wizard_supervisor_routed`` DEVE estar registrado no
    ``DECISION_TYPE_MAPPING`` do AuditService. Sem essa entrada o
    AuditService cai em fallback genérico (``score_candidate``) e
    invalida o trail SOX/EU AI Act do supervisor."""
    from app.shared.compliance.audit_service import DECISION_TYPE_MAPPING

    assert "wizard_supervisor_routed" in DECISION_TYPE_MAPPING, (
        "wizard_supervisor_routed precisa estar em DECISION_TYPE_MAPPING "
        "(audit_service.py) — caso contrário cai no fallback "
        "score_candidate e quebra o objetivo de auditoria T2.2."
    )
    # Compara via .name para não re-importar DecisionType (evita
    # double-registration do Table 'audit_logs' em isolamento).
    canonical = DECISION_TYPE_MAPPING["wizard_supervisor_routed"]
    sibling = DECISION_TYPE_MAPPING["wizard_step_completed"]
    assert canonical.name == sibling.name == "GENERATE_FEEDBACK", (
        "Consistência com wizard_step_completed / wizard_fallback_invoked."
    )


def test_allowlist_is_canonical():
    """Garante que a allowlist canônica não foi estendida silenciosamente.
    Estender requer RFC + atualização desta sentinela."""
    from app.domains.job_creation.services.wizard_supervisor_classifier import (
        ALLOWED_SUPERVISOR_INTENTS,
    )
    assert ALLOWED_SUPERVISOR_INTENTS == frozenset({
        "create_new",
        "resume_draft",
        "edit_published",
        "meta_question",
        "exit_wizard",
        "continue_current",
    }), (
        "Allowlist do supervisor mudou — atualize doc wizard-flow.md §12 "
        "e eval/golden/wizard_supervisor_routing.jsonl antes."
    )


# ---------------------------------------------------------------------------
# Contract 3 — Short-circuit NÃO muta state
# ---------------------------------------------------------------------------


def test_short_circuit_meta_question_uses_helper_as_primary(monkeypatch):
    """``_run_supervisor`` deve chamar ``wizard_meta_question_helper`` como
    caller PRIMÁRIO (Sonnet, stage-aware). O ``conversational_reply`` do
    supervisor (Haiku) é apenas last-resort. Inverter essa ordem produz
    respostas genéricas e perde awareness de etapa.

    Também valida ``short_circuit=True``, payload ``wizard_meta_reply``
    e que o ``prior_state`` NÃO é mutado.
    """
    from app.domains.job_creation.services import wizard_session_service as svc_mod
    from app.domains.job_creation.services import wizard_meta_question_helper as helper_mod

    monkeypatch.setenv("LIA_WIZARD_SUPERVISOR_CLASSIFIER", "1")

    # Reply do supervisor (Haiku) — DEVE ser ignorado se o helper responder.
    fake_output = MagicMock()
    fake_output.intent = "meta_question"
    fake_output.confidence = 0.9
    fake_output.conversational_reply = "[REPLY DO SUPERVISOR — NÃO DEVE APARECER]"

    fake_classifier = MagicMock()
    fake_classifier.classify_sync = MagicMock(return_value=fake_output)

    helper_mock = MagicMock(
        return_value="Estamos no enriquecimento da JD. Quer continuar?",
    )

    with patch(
        "app.domains.job_creation.services.wizard_supervisor_classifier."
        "get_wizard_supervisor_classifier",
        return_value=fake_classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_supervisor_classifier."
        "is_supervisor_enabled",
        return_value=True,
    ), patch.object(
        helper_mod, "generate_meta_response_sync", helper_mock,
    ):
        prior_state = {
            "current_stage": "jd_enrichment",
            "conversation_messages": [{"role": "user", "content": "JD original"}],
        }
        result = asyncio.run(svc_mod.WizardSessionService._run_supervisor(
            user_message="em que etapa estamos?",
            prior_state=prior_state,
            context={},
            company_id="00000000-0000-4000-a000-000000000001",
            session_id="s-1",
            thread_id="wiz-deadbeef-s-1",
        ))

    assert result is not None
    assert result["intent"] == "meta_question"
    assert result["short_circuit"] is True
    assert result["ws_stage_payload"]["type"] == "wizard_meta_reply"

    # CONTRATO HELPER-FIRST: helper foi chamado e seu reply venceu.
    assert helper_mock.called, (
        "wizard_meta_question_helper.generate_meta_response_sync DEVE ser "
        "chamado como caller primário em meta_question."
    )
    assert result["message"].startswith("Estamos no enriquecimento"), (
        "Reply do helper (Sonnet) DEVE prevalecer sobre conversational_reply "
        "do supervisor (Haiku)."
    )
    assert "REPLY DO SUPERVISOR" not in result["message"]

    # Sanity: prior_state NÃO foi mutado.
    assert prior_state["current_stage"] == "jd_enrichment"
    assert len(prior_state["conversation_messages"]) == 1


def test_short_circuit_exit_wizard_returns_payload(monkeypatch):
    """``exit_wizard`` produz payload ``wizard_exit`` com mensagem
    educada e ``short_circuit=True``."""
    from app.domains.job_creation.services import wizard_session_service as svc_mod

    fake_output = MagicMock()
    fake_output.intent = "exit_wizard"
    fake_output.confidence = 0.95
    fake_output.conversational_reply = ""  # cai no fallback educado

    fake_classifier = MagicMock()
    fake_classifier.classify_sync = MagicMock(return_value=fake_output)

    with patch(
        "app.domains.job_creation.services.wizard_supervisor_classifier."
        "get_wizard_supervisor_classifier",
        return_value=fake_classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_supervisor_classifier."
        "is_supervisor_enabled",
        return_value=True,
    ):
        result = asyncio.run(svc_mod.WizardSessionService._run_supervisor(
            user_message="cancela tudo",
            prior_state={"current_stage": "wsi_questions"},
            context={},
            company_id="00000000-0000-4000-a000-000000000001",
            session_id="s-1",
            thread_id="wiz-deadbeef-s-1",
        ))

    assert result is not None
    assert result["intent"] == "exit_wizard"
    assert result["short_circuit"] is True
    assert result["ws_stage_payload"]["type"] == "wizard_exit"
    assert len(result["message"]) > 10  # mensagem real, não vazia


def test_supervisor_fallback_message_is_not_canned_product_literal():
    """Política de fallback determinístico do supervisor (post code-review
    Task #1127). O fallback emitido quando helper E classifier devolvem
    reply vazio é uma string curta de roteamento — NÃO pode reintroduzir
    nenhum dos literais de produto vetados pela sentinela T3
    (test_wizard_no_canned_fallback_t3.py).

    Veta drift de policy: se alguém trocar o fallback por uma string
    de produto (ex.: 'Captei a vaga'), a sentinela trava o build.
    """
    import inspect
    from app.domains.job_creation.services import wizard_session_service as svc_mod

    src = inspect.getsource(svc_mod.WizardSessionService._run_supervisor)
    banned = [
        "preciso da sua aprovação",
        "Captei a vaga",
        "Vaga em criação",
        "Vaga criada com sucesso",
    ]
    for literal in banned:
        assert literal.lower() not in src.lower(), (
            f"Fallback do supervisor reintroduziu literal canned proibido "
            f"pela sentinela T3: {literal!r}. Use string de roteamento "
            f"curta (sem semântica de produto)."
        )


def test_continue_current_does_not_short_circuit(monkeypatch):
    """``continue_current`` (default) devolve ``short_circuit=False`` —
    caller DEVE seguir para o graph como sempre."""
    from app.domains.job_creation.services import wizard_session_service as svc_mod

    fake_output = MagicMock()
    fake_output.intent = "continue_current"
    fake_output.confidence = 0.7
    fake_output.conversational_reply = ""

    fake_classifier = MagicMock()
    fake_classifier.classify_sync = MagicMock(return_value=fake_output)

    with patch(
        "app.domains.job_creation.services.wizard_supervisor_classifier."
        "get_wizard_supervisor_classifier",
        return_value=fake_classifier,
    ), patch(
        "app.domains.job_creation.services.wizard_supervisor_classifier."
        "is_supervisor_enabled",
        return_value=True,
    ):
        result = asyncio.run(svc_mod.WizardSessionService._run_supervisor(
            user_message="manda bala",
            prior_state={"current_stage": "jd_enrichment"},
            context={},
            company_id="00000000-0000-4000-a000-000000000001",
            session_id="s-1",
            thread_id="wiz-deadbeef-s-1",
        ))

    assert result is not None
    assert result["short_circuit"] is False
    assert result["intent"] == "continue_current"
