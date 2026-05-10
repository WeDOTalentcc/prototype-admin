"""
Task #970 (T-B canônica) — Wizard como piloto da TenantAwareAgentMixin.

Substitui o hotfix `fix-wizard-company-context.md`. Garante que:

1. ``WizardReActAgent`` herda de ``TenantAwareAgentMixin`` (MRO correto).
2. ``WizardReActAgent.tenant_strict_override is True`` — wizard NUNCA pode
   degradar pra "sua empresa"/"geral" mesmo quando ``LIA_AGENT_TENANT_STRICT``
   estiver OFF em dev.
3. ``_get_runtime_domain_instructions`` usa ``self._compose_runtime_prompt``
   (helper canônico do mixin) — assim ``tenant_context_snippet`` injetado
   pelos handlers SSE/WS chega ao prompt em runtime.
4. ``WizardSessionService._build_state`` valida ``company_id`` via
   ``CompanyId.parse`` (UUID v4 ou slug). Para UUID/slug não-numérico,
   ``workspace_id`` permanece 0 e ``company_id`` é normalizado e propagado;
   ``review_node`` faz fallback string em ``workspace_id or company_id``.
5. Em strict-mode, ``company_id`` inválido ("default", vazio, None) levanta
   ``InvalidCompanyIdError``.

Sem deps de DB / LLM — testa apenas a fronteira do agente e do builder.
"""
from __future__ import annotations

import inspect
import os
import pytest

from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
from app.shared.exceptions.tenant_errors import (
    InvalidCompanyIdError,
    MissingTenantContextError,
)

DEMO_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"


# ─── Wizard agent: herança + override + helper canônico ────────────────────

def test_wizard_react_agent_inherits_tenant_aware_mixin():
    from app.domains.job_management.agents.wizard_react_agent import (
        WizardReActAgent,
    )

    mro = [c.__name__ for c in WizardReActAgent.__mro__]
    assert "TenantAwareAgentMixin" in mro, (
        f"WizardReActAgent deve herdar de TenantAwareAgentMixin (MRO atual: {mro})"
    )
    # MRO recomendado: mixin antes da base ReAct para os overrides funcionarem
    assert mro.index("TenantAwareAgentMixin") < mro.index("LangGraphReActBase"), (
        "TenantAwareAgentMixin deve vir ANTES de LangGraphReActBase no MRO"
    )


def test_wizard_react_agent_forces_strict_mode():
    from app.domains.job_management.agents.wizard_react_agent import (
        WizardReActAgent,
    )

    assert WizardReActAgent.tenant_strict_override is True, (
        "Wizard nunca deve degradar pra 'sua empresa' — "
        "tenant_strict_override deve ser True"
    )


def test_wizard_runtime_instructions_use_compose_helper():
    """O override de _get_runtime_domain_instructions deve usar o helper
    canônico do mixin (self._compose_runtime_prompt), não chamar
    PromptComposer.for_domain_runtime direto — caso contrário o snippet
    propagado pelo mixin se perde no runtime prompt."""
    from app.domains.job_management.agents import wizard_react_agent as mod

    src = inspect.getsource(mod.WizardReActAgent._get_runtime_domain_instructions)
    assert "_compose_runtime_prompt" in src, (
        "_get_runtime_domain_instructions deve chamar self._compose_runtime_prompt "
        "(helper do TenantAwareAgentMixin) — caso contrário tenant_context_snippet "
        "não chega ao prompt runtime do wizard."
    )


# ─── WizardSessionService._build_state: CompanyId.parse + UUID handling ────

def _build_state_args(**overrides):
    base = dict(
        thread_id="wiz-test-1",
        user_message="Quero criar uma vaga",
        user_id="user-1",
        company_id="00000000-0000-4000-a000-000000000001",  # Demo Company canônica
        session_id="sess-1",
        context={},
        prior_state={},
    )
    base.update(overrides)
    return base


def test_build_state_uuid_company_id_normalizes_and_keeps_workspace_zero():
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    state = WizardSessionService._build_state(
        **_build_state_args(company_id="00000000-0000-4000-A000-000000000001")
    )
    # UUID não é numérico → workspace_id permanece 0; review_node faz fallback string
    assert state["workspace_id"] == 0
    # company_id é normalizado em lowercase (CompanyId.parse)
    assert state["company_id"] == "00000000-0000-4000-a000-000000000001"


def test_build_state_slug_company_id_keeps_workspace_zero_and_normalizes():
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    state = WizardSessionService._build_state(
        **_build_state_args(company_id="ACME_CORP")
    )
    assert state["workspace_id"] == 0
    assert state["company_id"] == "acme_corp"


def test_build_state_propagates_tenant_context_snippet():
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    snippet = "Empresa: WeDo Talent (Tecnologia)\nPlano: enterprise"
    state = WizardSessionService._build_state(
        **_build_state_args(context={"tenant_context_snippet": snippet})
    )
    assert state.get("tenant_context_snippet") == snippet, (
        "_CONTEXT_CARRY_KEYS deve incluir tenant_context_snippet — "
        "sem isso o agente do wizard perde tenant context entre turnos."
    )


def test_build_state_strict_mode_rejects_default_literal(monkeypatch):
    """Em strict-mode (default em prod/staging), company_id reservado
    como 'default' deve levantar InvalidCompanyIdError — não silenciar
    para workspace_id=0/company_id="default"."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")
    with pytest.raises(InvalidCompanyIdError):
        WizardSessionService._build_state(**_build_state_args(company_id="default"))


def test_build_state_strict_mode_rejects_empty_company_id(monkeypatch):
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")
    with pytest.raises(InvalidCompanyIdError):
        WizardSessionService._build_state(**_build_state_args(company_id=""))


def test_build_state_legacy_mode_falls_open_with_warning(monkeypatch, caplog):
    """Em legacy/dev mode, company_id inválido NÃO levanta — só loga warning
    e degrada pra workspace_id=0/company_id="" (compat dev)."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "false")
    state = WizardSessionService._build_state(
        **_build_state_args(company_id="default")
    )
    assert state["workspace_id"] == 0
    assert state["company_id"] == ""


def test_build_state_strict_mode_rejects_none_with_missing_tenant_context(monkeypatch):
    """Contrato T-B (review #970): ``company_id=None`` em strict-mode
    levanta ``MissingTenantContextError`` (semanticamente "tenant context
    ausente") — NÃO ``InvalidCompanyIdError`` (que é "presente mas malformado").
    Distinção importa para o exception handler global e o error code registry."""
    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")
    with pytest.raises(MissingTenantContextError):
        WizardSessionService._build_state(**_build_state_args(company_id=None))


def test_build_state_emits_structured_log_per_turn(monkeypatch, caplog):
    """Cada turno do wizard deve emitir um log estruturado
    ``wizard_tenant_context_resolved`` com ``company_id``, ``source`` e
    ``snippet_len`` — habilita eval suite + canary detectarem regressão
    silenciosa de tenant context (ex.: snippet vazio / source=fail_open_*)."""
    import logging

    from app.domains.job_creation.services.wizard_session_service import (
        WizardSessionService,
    )

    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "false")
    snippet = "Empresa: WeDo Talent (Tecnologia)"
    with caplog.at_level(logging.INFO, logger="app.domains.job_creation.services.wizard_session_service"):
        WizardSessionService._build_state(
            **_build_state_args(
                company_id=DEMO_COMPANY_UUID,
                context={"tenant_context_snippet": snippet},
            )
        )

    structured = [
        r for r in caplog.records
        if getattr(r, "event", None) == "wizard_tenant_context_resolved"
    ]
    assert structured, (
        "wizard_tenant_context_resolved não emitido — eval/canary não conseguem "
        "detectar regressão silenciosa de tenant context"
    )
    rec = structured[-1]
    assert rec.company_id == DEMO_COMPANY_UUID
    assert rec.source == "valid"
    assert rec.snippet_len == len(snippet)


# ─── E2E SSE/WS repro: process_message com grafo mockado ───────────────────

@pytest.mark.asyncio
async def test_process_message_propagates_tenant_context_to_graph(monkeypatch):
    """Repro do bug original "LIA pergunta company_id no chat do wizard":
    o handler SSE/WS chama ``WizardSessionService.process_message`` com o
    snippet de tenant resolvido + ``company_id`` do JWT. O serviço deve
    propagar ambos para o ``state`` que vai ao grafo (e por extensão ao
    runtime prompt do agente). Esse teste mocka o grafo e captura o
    ``state`` injetado — replica o caminho exato dos handlers de produção
    (``agent_chat_sse.py`` linhas 332-353 / WS equivalente)."""
    from app.domains.job_creation.services import wizard_session_service as wss_mod

    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")

    captured: dict = {}

    class _FakeGraph:
        async def stream_invoke(self, state, thread_id, on_token=None):
            captured["state"] = state
            captured["thread_id"] = thread_id
            return (
                {
                    "current_stage": "draft",
                    "recruiter_message": "Vamos criar a vaga!",
                    "company_id": state.get("company_id"),
                },
                0,
            )

    monkeypatch.setattr(
        wss_mod, "get_job_creation_graph", lambda: _FakeGraph()
    )

    async def _fake_prior_state(_thread_id):
        return {}

    monkeypatch.setattr(
        wss_mod.WizardSessionService, "_get_prior_state", classmethod(lambda cls, _t: _fake_prior_state(_t))
    )

    snippet = (
        "Empresa: Demo Company (Tecnologia)\n"
        "Plano: enterprise\nTimezone: America/Sao_Paulo"
    )
    msg, payload, tokens = await wss_mod.WizardSessionService.process_message(
        thread_id="wiz-e2e-1",
        user_message="Quero criar uma vaga de Engenheiro de Software",
        user_id="recruiter-1",
        company_id=DEMO_COMPANY_UUID,
        session_id="sse-sess-1",
        context={"tenant_context_snippet": snippet, "metadata": {"channel": "sse"}},
    )

    assert "state" in captured, "Grafo do wizard não foi invocado"
    state = captured["state"]
    # 1. company_id do JWT chega normalizado ao grafo (T-B)
    assert state["company_id"] == DEMO_COMPANY_UUID
    # 2. workspace_id=0 para UUID — review_node faz fallback string
    assert state["workspace_id"] == 0
    # 3. tenant_context_snippet propaga via _CONTEXT_CARRY_KEYS — sem isso
    #    o agente perderia o contexto e voltaria a perguntar a empresa
    assert state.get("tenant_context_snippet") == snippet
    # 4. user_message vira raw_input + última conversation_message
    assert state["raw_input"] == "Quero criar uma vaga de Engenheiro de Software"
    assert state["conversation_messages"][-1]["role"] == "user"


@pytest.mark.asyncio
async def test_process_message_strict_mode_rejects_missing_company(monkeypatch):
    """Em strict-mode (default em prod), invocar o wizard sem company_id
    (JWT sem tenant) deve abortar com ``MissingTenantContextError`` ANTES
    de tocar o grafo — fail-closed canônico T-B."""
    from app.domains.job_creation.services import wizard_session_service as wss_mod

    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")

    graph_called = {"flag": False}

    class _FakeGraph:
        async def stream_invoke(self, state, thread_id, on_token=None):
            graph_called["flag"] = True
            return ({}, 0)

    monkeypatch.setattr(wss_mod, "get_job_creation_graph", lambda: _FakeGraph())

    async def _fake_prior_state(_thread_id):
        return {}

    monkeypatch.setattr(
        wss_mod.WizardSessionService, "_get_prior_state",
        classmethod(lambda cls, _t: _fake_prior_state(_t)),
    )

    with pytest.raises(MissingTenantContextError):
        await wss_mod.WizardSessionService.process_message(
            thread_id="wiz-e2e-noauth",
            user_message="oi",
            user_id="recruiter-1",
            company_id=None,
            session_id="sse-sess-2",
            context={},
        )

    assert graph_called["flag"] is False, (
        "Grafo NÃO deveria ter sido invocado quando tenant context está ausente"
    )
