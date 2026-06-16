"""TDD — wiring do orquestrador em WizardSessionService (flag-gated).

Testa _process_via_orchestrator e o gate _orchestrator_enabled sem tocar o
graph nem rede. Mocka o orquestrador e a persistência.
"""
from __future__ import annotations

from unittest.mock import patch, AsyncMock

import pytest

from app.domains.job_creation.services.wizard_session_service import (
    WizardSessionService,
)
from app.domains.job_creation.orchestrator.wizard_orchestrator import (
    OrchestratorResult,
)


@pytest.mark.medium
def test_orchestrator_flag_default_off(monkeypatch):
    # Isola o fallback .env (que em dev tem a flag ligada) forçando cache vazio.
    monkeypatch.delenv("LIA_WIZARD_ORCHESTRATOR", raising=False)
    WizardSessionService._dotenv_cache = {}
    try:
        assert WizardSessionService._orchestrator_enabled() is False
    finally:
        WizardSessionService._dotenv_cache = None


@pytest.mark.medium
def test_orchestrator_flag_on(monkeypatch):
    monkeypatch.setenv("LIA_WIZARD_ORCHESTRATOR", "true")
    assert WizardSessionService._orchestrator_enabled() is True


@pytest.mark.medium
@pytest.mark.asyncio
async def test_process_via_orchestrator_merges_and_persists():
    """Roteia via orquestrador, mergeia state_updates, acumula histórico, persiste."""
    fake_result = OrchestratorResult(
        reply="Registrei Designer. Qual a senioridade?",
        state_updates={"parsed_title": "Designer", "current_stage": "intake"},
        tool_calls=["set_job_fields"],
        iterations=2,
    )

    class _FakeOrch:
        def process_turn(self, *, state, user_message, ctx):
            # multi-tenancy: ctx.company_id veio do caller, não do state cru
            assert ctx.company_id == "comp-77"
            return fake_result

    persisted = {}

    async def _fake_persist(thread_id, values):
        persisted["thread_id"] = thread_id
        persisted["values"] = values
        return True

    with patch(
        "app.domains.job_creation.orchestrator.wizard_orchestrator.get_wizard_orchestrator",
        return_value=_FakeOrch(),
    ), patch.object(
        WizardSessionService, "_persist_orchestrator_state", _fake_persist
    ):
        reply, payload, tokens = await WizardSessionService._process_via_orchestrator(
            thread_id="thread-1",
            user_message="quero criar vaga de designer",
            user_id="u1",
            company_id="comp-77",
            prior_state={"workspace_id": 1, "conversation_messages": []},
            context=None,
        )

    assert reply == fake_result.reply
    assert tokens == 0
    # state persistido com o merge + histórico acumulado
    pv = persisted["values"]
    assert pv["parsed_title"] == "Designer"
    assert pv["company_id"] == "comp-77"
    assert pv["conversation_messages"][-2] == {"role": "user", "content": "quero criar vaga de designer"}
    assert pv["conversation_messages"][-1] == {"role": "assistant", "content": fake_result.reply}
    # payload canonical com a chave message obrigatória
    assert payload["data"]["message"] == fake_result.reply
    assert payload["data"]["parsed_title"] == "Designer"


@pytest.mark.medium
@pytest.mark.asyncio
async def test_process_via_orchestrator_carries_context_fields():
    """tenant_context_snippet do context chega ao state passado ao orquestrador."""
    seen = {}

    class _FakeOrch:
        def process_turn(self, *, state, user_message, ctx):
            seen["tenant"] = state.get("tenant_context_snippet")
            return OrchestratorResult(reply="ok")

    async def _noop_persist(thread_id, values):
        return True

    with patch(
        "app.domains.job_creation.orchestrator.wizard_orchestrator.get_wizard_orchestrator",
        return_value=_FakeOrch(),
    ), patch.object(WizardSessionService, "_persist_orchestrator_state", _noop_persist):
        await WizardSessionService._process_via_orchestrator(
            thread_id="t",
            user_message="oi",
            user_id="u",
            company_id="c",
            prior_state={},
            context={"tenant_context_snippet": "Empresa ACME, setor tech"},
        )

    assert seen["tenant"] == "Empresa ACME, setor tech"


@pytest.mark.medium
@pytest.mark.asyncio
async def test_payload_includes_panel_fields_and_jd():
    """P1: payload alinhado ao painel — location/manager/email + JD + stage derivado."""
    fake_result = OrchestratorResult(
        reply="Pronto!",
        state_updates={
            "parsed_title": "Eng Python",
            "parsed_location": "São Paulo",
            "parsed_employment_type": "CLT",
            "parsed_manager_name": "Paulo Moraes",
            "parsed_manager_email": "paulo@x.com",
            "jd_enriched": {"titulo_padronizado": "Eng Python Sr"},
            "jd_quality_score": 88.0,
            "jd_approved": True,
        },
    )

    class _FakeOrch:
        def process_turn(self, *, state, user_message, ctx):
            return fake_result

    async def _noop(thread_id, values):
        return True

    with patch(
        "app.domains.job_creation.orchestrator.wizard_orchestrator.get_wizard_orchestrator",
        return_value=_FakeOrch(),
    ), patch.object(WizardSessionService, "_persist_orchestrator_state", _noop):
        reply, payload, _ = await WizardSessionService._process_via_orchestrator(
            thread_id="t", user_message="x", user_id="u", company_id="c",
            prior_state={}, context=None,
        )

    d = payload["data"]
    # campos do painel (antes ausentes)
    assert d["parsed_location"] == "São Paulo"
    assert d["parsed_employment_type"] == "CLT"
    assert d["parsed_manager_name"] == "Paulo Moraes"
    assert d["parsed_manager_email"] == "paulo@x.com"
    # JD surfacada
    assert d["jd_enriched"]["titulo_padronizado"] == "Eng Python Sr"
    assert d["jd_approved"] is True
    # stage derivado: jd_enriched presente → jd_enrichment
    assert payload["stage"] == "jd_enrichment"


@pytest.mark.medium
@pytest.mark.asyncio
async def test_email_extracted_from_raw_context_bypassing_llm():
    """P0: email do gestor capturado do texto cru (context) e setado no state."""
    seen = {}

    class _FakeOrch:
        def process_turn(self, *, state, user_message, ctx):
            seen["email_in_state"] = state.get("parsed_manager_email")
            return OrchestratorResult(reply="ok")

    async def _noop(thread_id, values):
        seen["persisted_email"] = values.get("parsed_manager_email")
        return True

    with patch(
        "app.domains.job_creation.orchestrator.wizard_orchestrator.get_wizard_orchestrator",
        return_value=_FakeOrch(),
    ), patch.object(WizardSessionService, "_persist_orchestrator_state", _noop):
        await WizardSessionService._process_via_orchestrator(
            thread_id="t",
            user_message="[EMAIL REMOVIDO]",  # mascarado (o que o LLM veria)
            user_id="u", company_id="c", prior_state={},
            context={"_raw_user_message": "gestor é paulo paulo.moraes@wedotalent.cc"},
        )

    # extraído do raw, disponível ao state ANTES do LLM, e persistido
    assert seen["email_in_state"] == "paulo.moraes@wedotalent.cc"
    assert seen["persisted_email"] == "paulo.moraes@wedotalent.cc"


@pytest.mark.medium
@pytest.mark.asyncio
async def test_email_extracted_from_user_message_sse_path():
    """SSE não preenche _raw_user_message nem mascara inbound — email vem no
    próprio user_message. A extração deve cobrir esse caso (fallback)."""
    seen = {}

    class _FakeOrch:
        def process_turn(self, *, state, user_message, ctx):
            seen["email"] = state.get("parsed_manager_email")
            return OrchestratorResult(reply="ok")

    async def _noop(thread_id, values):
        return True

    with patch(
        "app.domains.job_creation.orchestrator.wizard_orchestrator.get_wizard_orchestrator",
        return_value=_FakeOrch(),
    ), patch.object(WizardSessionService, "_persist_orchestrator_state", _noop):
        await WizardSessionService._process_via_orchestrator(
            thread_id="t",
            user_message="gestor pedro silva pedro.silva@democompany.com.br",  # raw (SSE)
            user_id="u", company_id="c", prior_state={},
            context=None,  # SSE não passa _raw_user_message
        )
    assert seen["email"] == "pedro.silva@democompany.com.br"
