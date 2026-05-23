"""
PR-A — Rail A metadata routing (BE)

Testa o pipeline FE→BE para hints de routing emitidos pelo Rail A:

1. ``ContextAdapter.from_ws`` extrai ``context.metadata`` do payload WS
   para ``UniversalContext.extra["metadata"]``.
2. ``rail_a_hint_override.try_hint_route`` retorna RouteResult quando hint
   válido (source=rail_a + domain registrado), senão None (fallback).
3. Hint inválido (domínio não-registrado) é rejeitado para preservar
   LIA-C01 compliance enforcement.
4. Metadata sem source=rail_a é ignorada (defensivo contra prompt
   injection via context arbitrário).

Skill: lia-testing PARTE 1 (TDD red→green) + harness-engineering
(computational guide canônico).
"""
from app.orchestrator.context.context_adapter import ContextAdapter
from app.orchestrator.services.rail_a_hint_override import (
    OVERRIDE_SOURCE,
    TRUSTED_SOURCE,
    get_hint_domain,
    try_hint_route,
)


# ─── ContextAdapter.from_ws — extração de metadata ──────────────────────


def test_from_ws_extrai_metadata_para_extra():
    """Payload WS com ``context.metadata`` deve popular ``extra["metadata"]``."""
    frame = {
        "type": "message",
        "content": "Criar uma nova vaga",
        "context": {
            "metadata": {
                "source": "rail_a",
                "card_id": "create-job",
                "stage": "definir-vaga",
                "domain_hint": "job_management",
                "intent_hint": "create_job",
            },
        },
        "domain": "general",
    }
    jwt = {"sub": "user-1", "company_id": "co-1"}
    ctx = ContextAdapter.from_ws(session_id="sess-1", message_frame=frame, jwt_payload=jwt)
    assert ctx.extra.get("metadata") == frame["context"]["metadata"]
    assert ctx.extra["metadata"]["domain_hint"] == "job_management"
    assert ctx.extra["metadata"]["intent_hint"] == "create_job"


def test_from_ws_sem_metadata_funciona_normalmente():
    """Payload sem ``metadata`` não deve quebrar nem inserir chave fantasma."""
    frame = {"type": "message", "content": "Olá", "context": {}, "domain": "general"}
    jwt = {"sub": "user-1", "company_id": "co-1"}
    ctx = ContextAdapter.from_ws(session_id="sess-1", message_frame=frame, jwt_payload=jwt)
    assert ctx.extra.get("metadata") is None


def test_from_ws_descarta_metadata_invalida_via_pydantic():
    """Metadata sem campos obrigatórios é descartada com warning (fail-safe)."""
    frame = {
        "type": "message",
        "content": "Olá",
        "context": {
            "metadata": {
                # falta 'source' (literal "rail_a"), 'card_id' e 'stage'
                "domain_hint": "job_management",
            },
        },
        "domain": "general",
    }
    jwt = {"sub": "user-1", "company_id": "co-1"}
    ctx = ContextAdapter.from_ws(session_id="sess-1", message_frame=frame, jwt_payload=jwt)
    # Metadata inválida deve ser descartada — chave 'metadata' não aparece em extra
    assert "metadata" not in ctx.extra


def test_from_ws_descarta_metadata_com_source_diferente():
    """Metadata com source != 'rail_a' é descartada (anti prompt injection)."""
    frame = {
        "type": "message",
        "content": "Olá",
        "context": {
            "metadata": {
                "source": "untrusted_origin",
                "card_id": "create-job",
                "stage": "definir-vaga",
                "domain_hint": "job_management",
                "intent_hint": "create_job",
            },
        },
        "domain": "general",
    }
    jwt = {"sub": "user-1", "company_id": "co-1"}
    ctx = ContextAdapter.from_ws(session_id="sess-1", message_frame=frame, jwt_payload=jwt)
    assert "metadata" not in ctx.extra


def test_from_ws_drop_extra_fields_da_metadata():
    """Campos extras na metadata são silenciosamente descartados (model_config)."""
    frame = {
        "type": "message",
        "content": "Criar uma nova vaga",
        "context": {
            "metadata": {
                "source": "rail_a",
                "card_id": "create-job",
                "stage": "definir-vaga",
                "domain_hint": "job_management",
                "intent_hint": "create_job",
                "evil_field": "<script>alert(1)</script>",  # campo extra malicioso
            },
        },
        "domain": "general",
    }
    jwt = {"sub": "user-1", "company_id": "co-1"}
    ctx = ContextAdapter.from_ws(session_id="sess-1", message_frame=frame, jwt_payload=jwt)
    md = ctx.extra.get("metadata")
    assert md is not None
    assert "evil_field" not in md
    assert md["card_id"] == "create-job"


# ─── rail_a_hint_override.get_hint_domain ───────────────────────────────


def test_get_hint_domain_retorna_tupla_quando_hint_valido(monkeypatch):
    """Hint para domínio registrado deve retornar (domain_id, intent_id)."""
    # Monkeypatch DomainRegistry para evitar dependência de domains carregados.
    from app.domains.registry import DomainRegistry
    monkeypatch.setattr(
        DomainRegistry,
        "list_domains",
        lambda self: ["job_management", "sourcing", "communication"],
    )

    metadata = {
        "source": TRUSTED_SOURCE,
        "domain_hint": "job_management",
        "intent_hint": "create_job",
    }
    resolved = get_hint_domain(metadata)
    assert resolved == ("job_management", "create_job")


def test_get_hint_domain_aceita_so_domain_hint(monkeypatch):
    """Card pré-PR-B (5.1 send-offer) só especifica domain_hint."""
    from app.domains.registry import DomainRegistry
    monkeypatch.setattr(
        DomainRegistry, "list_domains", lambda self: ["communication"]
    )
    metadata = {"source": TRUSTED_SOURCE, "domain_hint": "communication"}
    resolved = get_hint_domain(metadata)
    assert resolved == ("communication", None)


def test_get_hint_domain_none_sem_metadata():
    assert get_hint_domain(None) is None
    assert get_hint_domain({}) is None
    assert get_hint_domain({"other": "x"}) is None


def test_get_hint_domain_none_sem_source_rail_a():
    """Defensivo: metadata sem source=rail_a é ignorada (anti prompt injection)."""
    metadata = {"domain_hint": "job_management", "intent_hint": "create_job"}
    assert get_hint_domain(metadata) is None
    metadata_outra = {
        "source": "untrusted",
        "domain_hint": "job_management",
    }
    assert get_hint_domain(metadata_outra) is None


def test_get_hint_domain_none_para_dominio_invalido(monkeypatch):
    """Hint para domínio NÃO registrado é rejeitado (preserva LIA-C01)."""
    from app.domains.registry import DomainRegistry
    monkeypatch.setattr(
        DomainRegistry, "list_domains", lambda self: ["job_management"]
    )
    metadata = {
        "source": TRUSTED_SOURCE,
        "domain_hint": "nonexistent_domain_xyz",
        "intent_hint": "fake",
    }
    assert get_hint_domain(metadata) is None


# ─── rail_a_hint_override.try_hint_route ────────────────────────────────


def test_try_hint_route_retorna_route_result_para_hint_valido(monkeypatch):
    """try_hint_route compõe RouteResult com confidence=0.99 e source override."""
    from app.domains.registry import DomainRegistry
    monkeypatch.setattr(
        DomainRegistry, "list_domains", lambda self: ["analytics"]
    )
    context = {
        "metadata": {
            "source": TRUSTED_SOURCE,
            "card_id": "job-report",
            "domain_hint": "analytics",
            "intent_hint": "generate_job_report",
        },
    }
    route = try_hint_route(context)
    assert route is not None
    assert route.domain_id == "analytics"
    assert route.confidence == 0.99
    assert route.source == OVERRIDE_SOURCE
    assert (route.intent_details or {}).get("raw_intent") == "generate_job_report"


def test_try_hint_route_none_quando_context_vazio():
    assert try_hint_route(None) is None
    assert try_hint_route({}) is None


def test_try_hint_route_none_quando_metadata_invalida():
    """Metadata presente mas inválida (sem source rail_a) → None."""
    context = {"metadata": {"domain_hint": "job_management"}}
    assert try_hint_route(context) is None


# ─── CascadedRouter Tier 0.0 (cobertura SSE/REST que bypassa orchestrator) ─


def test_cascaded_router_tier_0_0_curto_circuita_com_hint_valido(monkeypatch):
    """Tier 0.0 do CascadedRouter retorna RouteResult sem percorrer tiers 0-4.

    Garante que os transports que chamam ``CascadedRouter.route()`` direto
    (ex.: ``agent_chat_sse``, ``agent_chat_ws`` quando bypassam o
    MainOrchestrator) também respeitem os hints do Rail A.
    """
    import asyncio
    from app.domains.registry import DomainRegistry
    monkeypatch.setattr(
        DomainRegistry, "list_domains", lambda self: ["job_management"]
    )
    from app.orchestrator.routing.cascaded_router import CascadedRouter

    router = CascadedRouter()
    context = {
        "metadata": {
            "source": TRUSTED_SOURCE,
            "card_id": "create-job",
            "domain_hint": "job_management",
            "intent_hint": "create_job",
        },
    }
    # Mensagem absurda (sem keyword) — sem hint, fastrouter cairia em fallback.
    route = asyncio.run(router.route("xyzzy plugh nonsense", context=context))
    assert route.domain_id == "job_management"
    assert route.source == OVERRIDE_SOURCE
    assert route.confidence == 0.99


def test_cascaded_router_sem_hint_segue_tiers_normalmente(monkeypatch):
    """Sem hint válido, CascadedRouter cai nos tiers 0-4 normalmente."""
    import asyncio
    from app.orchestrator.routing.cascaded_router import CascadedRouter

    router = CascadedRouter()
    # Keyword forte → fastrouter resolve para job_management
    route = asyncio.run(router.route("criar nova vaga de desenvolvedor"))
    # Não exigimos um domain específico — só que NÃO seja override do Rail A
    assert route.source != OVERRIDE_SOURCE
