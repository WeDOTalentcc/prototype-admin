"""Task #712 — sanity tests for the 7 company_settings actions.

Garante que os handlers de domain delegam para as tools canônicas em
``company_tool_registry`` (sem duplicar lógica de escrita) e que respondem
corretamente nos três caminhos: success, clarification, error.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock

from app.domains.company_settings.domain import CompanySettingsDomain
from app.domains.base import DomainContext


def _ctx(tenant: str = "co_demo", user: str = "u_demo") -> DomainContext:
    return DomainContext(
        domain_id="company_settings",
        user_id=user,
        session_id="sess_test",
        tenant_id=tenant,
    )


@pytest.fixture
def domain() -> CompanySettingsDomain:
    return CompanySettingsDomain()


# ---------------------------------------------------------------------------
# clarification — sem campos preenchidos
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "action_id",
    [
        "configure_profile",
        "configure_culture",
        "configure_tech_stack",
        "configure_benefits",
    ],
)
@pytest.mark.asyncio
async def test_section_handlers_return_clarification_when_no_data(
    domain: CompanySettingsDomain, action_id: str
) -> None:
    handler = getattr(domain, f"_handle_{action_id}")
    resp = await handler({"company_id": "co_demo"}, _ctx())
    assert resp.needs_clarification, f"{action_id} deveria pedir clarification"
    assert resp.clarification_question


@pytest.mark.asyncio
async def test_manage_departments_is_routing_only(
    domain: CompanySettingsDomain,
) -> None:
    """Task #767 — `manage_departments` must route to canonical hub, not write."""
    resp = await domain._handle_manage_departments({}, _ctx())
    assert resp.success is True
    assert not resp.needs_clarification
    assert "Usuários & Departamentos" in (resp.message or "")
    hint = (resp.data or {}).get("navigation_hint") or {}
    assert hint.get("section") == "usuarios-departamentos"
    assert hint.get("tab") == "departments"


@pytest.mark.asyncio
async def test_workforce_clarification(domain: CompanySettingsDomain) -> None:
    resp = await domain._handle_configure_workforce({"company_id": "co_demo"}, _ctx())
    assert resp.needs_clarification
    assert "planejamento" in (resp.clarification_question or "").lower()


@pytest.mark.asyncio
async def test_process_document_clarification(domain: CompanySettingsDomain) -> None:
    resp = await domain._handle_process_document({"company_id": "co_demo"}, _ctx())
    assert resp.needs_clarification


# ---------------------------------------------------------------------------
# error — sem company_id
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "action_id",
    [
        "configure_profile",
        "configure_culture",
        "configure_tech_stack",
        "configure_benefits",
        "configure_workforce",
        "process_document",
    ],
)
@pytest.mark.asyncio
async def test_handlers_error_without_company_id(
    domain: CompanySettingsDomain, action_id: str
) -> None:
    handler_name = f"_handle_{action_id}"
    handler = getattr(domain, handler_name)
    # context tenant vazio + params sem company_id
    resp = await handler({}, DomainContext(
        domain_id="company_settings", user_id="u_demo", session_id="s", tenant_id=""))
    assert resp.success is False
    assert "company_id" in ((resp.error or "") + (resp.message or "")).lower()


# ---------------------------------------------------------------------------
# success — delega para tool canônica
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_configure_profile_delegates_to_save_section(
    domain: CompanySettingsDomain,
) -> None:
    target = (
        "app.domains.company_settings.agents.company_tool_registry"
        "._wrap_save_company_section"
    )
    fake = AsyncMock(
        return_value={
            "success": True,
            "message": "Perfil atualizado.",
            "data": {"updated_fields": ["website"]},
        }
    )
    with patch(target, fake):
        resp = await domain._handle_configure_profile(
            {"company_id": "co_demo", "data": {"website": "https://wedotalent.cc"}},
            _ctx(),
        )
    assert resp.success, f"esperado success, veio error={resp.error}"
    fake.assert_awaited_once()
    call_kwargs = fake.await_args.kwargs
    assert call_kwargs["company_id"] == "co_demo"
    assert call_kwargs["section"] == "profile"
    assert call_kwargs["data"] == {"website": "https://wedotalent.cc"}


@pytest.mark.asyncio
async def test_configure_workforce_delegates_to_import_plan(
    domain: CompanySettingsDomain,
) -> None:
    target = (
        "app.domains.company_settings.agents.company_tool_registry"
        "._wrap_import_workforce_plan"
    )
    fake = AsyncMock(
        return_value={
            "success": True,
            "message": "Plano importado.",
            "data": {"hires_count": 1},
        }
    )
    plan = [{"department": "Eng", "role": "SWE", "quantity": 2, "deadline": "Q3"}]
    with patch(target, fake):
        resp = await domain._handle_configure_workforce(
            {"company_id": "co_demo", "plan_data": plan}, _ctx()
        )
    assert resp.success
    fake.assert_awaited_once()
    assert fake.await_args.kwargs["plan_data"] == plan


@pytest.mark.asyncio
async def test_process_document_delegates_to_process_uploaded(
    domain: CompanySettingsDomain,
) -> None:
    target = (
        "app.domains.company_settings.agents.company_tool_registry"
        "._wrap_process_uploaded_document"
    )
    fake = AsyncMock(
        return_value={
            "success": True,
            "message": "Documento processado.",
            "data": {"expected_fields": ["mission", "values"]},
        }
    )
    with patch(target, fake):
        resp = await domain._handle_process_document(
            {
                "company_id": "co_demo",
                "document_text": "Nossa missao e empoderar pessoas.",
                "document_type": "handbook",
            },
            _ctx(),
        )
    assert resp.success
    assert resp.data.get("requires_human_approval") is True
    fake.assert_awaited_once()


# ---------------------------------------------------------------------------
# success — culture / tech_stack delegam para a mesma tool canônica
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "action_id, payload, expected_section",
    [
        ("configure_culture", {"mission": "empoderar pessoas"}, "culture"),
        ("configure_tech_stack", {"tech_stack": ["Python", "TS"]}, "culture"),
    ],
)
@pytest.mark.asyncio
async def test_culture_and_techstack_delegate_to_save_section(
    domain: CompanySettingsDomain,
    action_id: str,
    payload: dict,
    expected_section: str,
) -> None:
    target = (
        "app.domains.company_settings.agents.company_tool_registry"
        "._wrap_save_company_section"
    )
    fake = AsyncMock(
        return_value={"success": True, "message": "ok", "data": {"updated_fields": list(payload)}},
    )
    handler = getattr(domain, f"_handle_{action_id}")
    with patch(target, fake):
        resp = await handler({"company_id": "co_demo", "data": payload}, _ctx())
    assert resp.success
    fake.assert_awaited_once()
    kwargs = fake.await_args.kwargs
    assert kwargs["section"] == expected_section
    assert kwargs["data"] == payload


# ---------------------------------------------------------------------------
# configure_benefits — clarification quando vazio + delega para tool
# dedicada (write real em company_benefits) quando lista presente
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_configure_benefits_clarification_when_empty(
    domain: CompanySettingsDomain,
) -> None:
    resp = await domain._handle_configure_benefits({"company_id": "co_demo"}, _ctx())
    assert resp.needs_clarification
    assert resp.data.get("navigation_hint", {}).get("subsection") == "beneficios"


@pytest.mark.asyncio
async def test_configure_benefits_delegates_to_save_benefits_tool(
    domain: CompanySettingsDomain,
) -> None:
    target = (
        "app.domains.company_settings.agents.company_tool_registry"
        "._wrap_save_company_benefits"
    )
    fake = AsyncMock(
        return_value={
            "success": True,
            "message": "Beneficios salvos: 2 inserido(s).",
            "data": {"inserted": 2, "deactivated": 0, "mode": "append"},
        },
    )
    with patch(target, fake):
        resp = await domain._handle_configure_benefits(
            {
                "company_id": "co_demo",
                "benefits": ["Vale Refeicao", {"name": "Plano de Saude", "category": "health"}],
            },
            _ctx(),
        )
    assert resp.success, f"esperado success, veio error={resp.error}"
    fake.assert_awaited_once()
    kwargs = fake.await_args.kwargs
    assert kwargs["company_id"] == "co_demo"
    assert kwargs["mode"] == "append"
    assert len(kwargs["benefits"]) == 2
    assert kwargs["benefits"][0] == {"name": "Vale Refeicao"}
    assert resp.data.get("navigation_hint", {}).get("subsection") == "beneficios"


# ---------------------------------------------------------------------------
# analyze_website — clarification, error de SSRF, success com scraper mockado
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analyze_website_clarification_when_no_url(
    domain: CompanySettingsDomain,
) -> None:
    resp = await domain._handle_analyze_website({}, _ctx())
    assert resp.needs_clarification
    assert "site" in (resp.clarification_question or "").lower()


@pytest.mark.asyncio
async def test_analyze_website_rejects_unsafe_url(
    domain: CompanySettingsDomain,
) -> None:
    resp = await domain._handle_analyze_website({"website": "http://localhost/admin"}, _ctx())
    assert resp.success is False
    assert "seguranca" in (resp.error or "").lower()


@pytest.mark.asyncio
async def test_analyze_website_success_uses_scraper(
    domain: CompanySettingsDomain,
) -> None:
    target = (
        "app.domains.company.services.company_scraper_service.CompanyScraperService"
    )
    fake_instance = AsyncMock()
    fake_instance.scrape_website = AsyncMock(
        return_value={
            "success": True,
            "pages_scraped": 3,
            "pages": [],
            "content": "Somos a WeDOTalent",
            "source": "live",
        }
    )
    with patch(target, return_value=fake_instance):
        resp = await domain._handle_analyze_website(
            {"website": "https://wedotalent.cc"}, _ctx()
        )
    assert resp.success
    assert resp.data["pages_scraped"] == 3
    assert resp.data["url"] == "https://wedotalent.cc"


# ---------------------------------------------------------------------------
# Tenant isolation — context.tenant_id is the source of truth.
# params.company_id pointing to a different tenant MUST be refused for ALL
# write actions (security regression guard — Task #712 finding).
# ---------------------------------------------------------------------------
WRITE_ACTIONS_FOR_TENANT_TEST = [
    "configure_profile",
    "configure_culture",
    "configure_tech_stack",
    "configure_benefits",
    "configure_workforce",
    "process_document",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("action_id", WRITE_ACTIONS_FOR_TENANT_TEST)
async def test_write_actions_refuse_tenant_mismatch(
    domain: CompanySettingsDomain,
    action_id: str,
) -> None:
    """If params.company_id differs from context.tenant_id, the handler must
    refuse with a tenant_mismatch error and NOT call any write tool."""
    handler = {
        "configure_profile": domain._handle_configure_profile,
        "configure_culture": domain._handle_configure_culture,
        "configure_tech_stack": domain._handle_configure_tech_stack,
        "configure_benefits": domain._handle_configure_benefits,
        "configure_workforce": domain._handle_configure_workforce,
        "process_document": domain._handle_process_document,
    }[action_id]
    # Payload that would otherwise be valid for each action — we only care
    # that the security check fires BEFORE any tool is invoked.
    params = {
        "company_id": "co_attacker",   # untrusted input
        "name": "x",
        "description": "x",
        "benefits": ["Vale"],
        "plan_data": [{"role": "dev", "quantity": 1}],
        "document_text": "Texto institucional curto.",
    }
    ctx = _ctx(tenant="co_victim")

    # Patch every possible downstream tool — none should be reached.
    targets = [
        "app.domains.company_settings.agents.company_tool_registry._wrap_save_company_section",
        "app.domains.company_settings.agents.company_tool_registry._wrap_save_company_benefits",
        "app.domains.company_settings.agents.company_tool_registry._wrap_import_workforce_plan",
        "app.domains.company_settings.agents.company_tool_registry._wrap_process_uploaded_document",
    ]
    with patch(targets[0]) as m1, patch(targets[1]) as m2, \
         patch(targets[2]) as m3, patch(targets[3]) as m4:
        resp = await handler(params, ctx)

    assert resp.success is False, f"{action_id} should refuse tenant mismatch"
    assert (resp.data or {}).get("forbidden") is True
    assert (resp.data or {}).get("reason") == "tenant_mismatch"
    for m in (m1, m2, m3, m4):
        m.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("action_id", WRITE_ACTIONS_FOR_TENANT_TEST)
async def test_write_actions_accept_matching_company_id(
    domain: CompanySettingsDomain,
    action_id: str,
) -> None:
    """When params.company_id matches context.tenant_id, the action proceeds
    normally (no false-positive blocks)."""
    handler = {
        "configure_profile": domain._handle_configure_profile,
        "configure_culture": domain._handle_configure_culture,
        "configure_tech_stack": domain._handle_configure_tech_stack,
        "configure_benefits": domain._handle_configure_benefits,
        "configure_workforce": domain._handle_configure_workforce,
        "process_document": domain._handle_process_document,
    }[action_id]
    params = {"company_id": "co_demo"}  # matches _ctx default
    # Ensure the action gets PAST the tenant check — clarification or
    # success both prove the security guard didn't fire.
    resp = await handler(params, _ctx(tenant="co_demo"))
    assert (resp.data or {}).get("reason") != "tenant_mismatch"


# ---------------------------------------------------------------------------
# process_document — PHASE 2: confirm + confirmed_fields persists via
# _wrap_save_company_section and emits persist_document_extraction audit.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_process_document_phase2_persists_confirmed_fields(
    domain: CompanySettingsDomain,
) -> None:
    section_target = (
        "app.domains.company_settings.agents.company_tool_registry."
        "_wrap_save_company_section"
    )
    audit_target = (
        "app.domains.company_settings.agents.company_tool_registry._audit_log"
    )
    fake_save = AsyncMock(return_value={
        "success": True,
        "data": {"section": "profile", "fields_saved": ["name", "mission"]},
        "message": "ok",
    })
    fake_audit = AsyncMock(return_value=None)
    params = {
        "company_id": "co_demo",
        "confirm": True,
        "confirmed_fields": {
            "name": "WeDOTalent",
            "mission": "Conectar talento e proposito",
            "values": ["Etica", "Transparencia"],
        },
    }
    with patch(section_target, fake_save), patch(audit_target, fake_audit):
        resp = await domain._handle_process_document(params, _ctx())
    assert resp.success
    assert "profile" in resp.data["persisted_sections"]
    # save_company_section called at least once for profile/culture buckets
    assert fake_save.await_count >= 1
    # Extra audit emitted with persist_document_extraction action
    assert fake_audit.await_count >= 1
    audit_call = fake_audit.await_args_list[-1]
    # signature: _audit_log(company_id, action_type, ...)
    assert audit_call.args[1] == "persist_document_extraction"


@pytest.mark.asyncio
async def test_process_document_phase2_clarifies_when_no_fields(
    domain: CompanySettingsDomain,
) -> None:
    resp = await domain._handle_process_document(
        {"company_id": "co_demo", "confirm": True, "confirmed_fields": {}},
        _ctx(),
    )
    assert resp.needs_clarification
    assert "confirmed_fields" in (resp.clarification_question or "")


@pytest.mark.asyncio
async def test_process_document_phase2_refuses_tenant_mismatch(
    domain: CompanySettingsDomain,
) -> None:
    section_target = (
        "app.domains.company_settings.agents.company_tool_registry."
        "_wrap_save_company_section"
    )
    fake_save = AsyncMock()
    with patch(section_target, fake_save):
        resp = await domain._handle_process_document(
            {
                "company_id": "co_attacker",
                "confirm": True,
                "confirmed_fields": {"name": "x"},
            },
            _ctx(tenant="co_victim"),
        )
    assert resp.success is False
    assert (resp.data or {}).get("reason") == "tenant_mismatch"
    fake_save.assert_not_called()


# ---------------------------------------------------------------------------
# FairnessGuard — when the underlying tool blocks (e.g., discriminatory text),
# the handler must surface that error and not pretend success.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_configure_culture_propagates_fairness_block(
    domain: CompanySettingsDomain,
) -> None:
    section_target = (
        "app.domains.company_settings.agents.company_tool_registry."
        "_wrap_save_company_section"
    )
    blocked = {
        "success": False,
        "data": {"blocked_field": "values", "category": "discriminatory"},
        "message": "Campo 'values' bloqueado por compliance: linguagem discriminatoria detectada",
    }
    with patch(section_target, AsyncMock(return_value=blocked)):
        resp = await domain._handle_configure_culture(
            {"company_id": "co_demo", "values": ["Apenas homens jovens"]},
            _ctx(),
        )
    assert resp.success is False
    assert "compliance" in (resp.error or "").lower()
    assert (resp.data or {}).get("blocked_field") == "values"


@pytest.mark.asyncio
async def test_configure_benefits_propagates_fairness_block(
    domain: CompanySettingsDomain,
) -> None:
    benefits_target = (
        "app.domains.company_settings.agents.company_tool_registry."
        "_wrap_save_company_benefits"
    )
    blocked = {
        "success": False,
        "data": {"blocked_field": "description", "category": "discriminatory"},
        "message": "Beneficio 'X' bloqueado por compliance: linguagem inadequada",
    }
    with patch(benefits_target, AsyncMock(return_value=blocked)):
        resp = await domain._handle_configure_benefits(
            {"company_id": "co_demo",
             "benefits": [{"name": "Beneficio X",
                           "description": "Apenas para pessoas brancas"}]},
            _ctx(),
        )
    assert resp.success is False
    assert (resp.data or {}).get("blocked_field") == "description"


# ---------------------------------------------------------------------------
# Task #716 — analyze_website now returns `pending_writes` (phase 1) and
# accepts `confirm=True` + `confirmed_fields` (phase 2) to persist via the
# canonical save tools, mirroring the process_document flow.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analyze_website_success_includes_pending_writes(
    domain: CompanySettingsDomain,
) -> None:
    """Phase 1: scrape success surfaces `pending_writes` extracted from text
    and from the LinkedIn payload (without writing anything)."""
    target = (
        "app.domains.company.services.company_scraper_service.CompanyScraperService"
    )
    fake_instance = AsyncMock()
    fake_instance.scrape_website = AsyncMock(
        return_value={
            "success": True,
            "pages_scraped": 4,
            "pages": [],
            "content": (
                "## Missao\nConectar talento e proposito.\n\n"
                "## Valores\n- Etica\n- Transparencia\n- Foco em resultado\n"
            ),
            "linkedin_data": {
                "name": "WeDOTalent",
                "industry": "HR Tech",
                "employee_count": 42,
                "company_size": "Startup",
                "founded_year": 2021,
            },
            "source": "live",
        }
    )
    save_targets = [
        "app.domains.company_settings.agents.company_tool_registry._wrap_save_company_section",
        "app.domains.company_settings.agents.company_tool_registry._wrap_save_company_benefits",
    ]
    with patch(target, return_value=fake_instance), \
         patch(save_targets[0]) as m_section, \
         patch(save_targets[1]) as m_benefits:
        resp = await domain._handle_analyze_website(
            {"website": "https://wedotalent.cc"}, _ctx()
        )
    assert resp.success
    pw = (resp.data or {}).get("pending_writes") or {}
    # Text extraction picks up mission + values; LinkedIn payload promotes
    # name/industry/employee_count/company_size/founded_year.
    assert "mission" in pw
    assert "values" in pw and "Etica" in pw["values"]
    assert pw.get("name") == "WeDOTalent"
    assert pw.get("industry") == "HR Tech"
    assert pw.get("employee_count") == 42
    assert resp.data["requires_human_approval"] is True
    # Phase 1 must NEVER call the save tools.
    m_section.assert_not_called()
    m_benefits.assert_not_called()


@pytest.mark.asyncio
async def test_analyze_website_phase2_persists_confirmed_fields(
    domain: CompanySettingsDomain,
) -> None:
    """Phase 2: confirm=True + confirmed_fields persists via the canonical
    save tools and emits a `persist_website_extraction` audit entry."""
    section_target = (
        "app.domains.company_settings.agents.company_tool_registry."
        "_wrap_save_company_section"
    )
    benefits_target = (
        "app.domains.company_settings.agents.company_tool_registry."
        "_wrap_save_company_benefits"
    )
    audit_target = (
        "app.domains.company_settings.agents.company_tool_registry._audit_log"
    )
    fake_save = AsyncMock(return_value={
        "success": True,
        "data": {"section": "profile", "fields_saved": ["name", "mission"]},
        "message": "ok",
    })
    fake_benefits = AsyncMock(return_value={
        "success": True,
        "data": {"benefits_saved": ["Vale Refeicao"]},
        "message": "ok",
    })
    fake_audit = AsyncMock(return_value=None)
    params = {
        "company_id": "co_demo",
        "website": "https://wedotalent.cc",
        "confirm": True,
        "confirmed_fields": {
            "name": "WeDOTalent",
            "mission": "Conectar talento e proposito",
            "values": ["Etica", "Transparencia"],
            "benefits": ["Vale Refeicao"],
        },
    }
    with patch(section_target, fake_save), \
         patch(benefits_target, fake_benefits), \
         patch(audit_target, fake_audit):
        resp = await domain._handle_analyze_website(params, _ctx())
    assert resp.success
    persisted = resp.data["persisted_sections"]
    # Profile + culture + benefits all wrote successfully.
    assert "profile" in persisted
    assert "culture" in persisted
    assert "benefits" in persisted
    assert fake_save.await_count >= 1
    assert fake_benefits.await_count == 1
    # Audit explicitly tags the source as website extraction.
    assert fake_audit.await_count >= 1
    audit_call = fake_audit.await_args_list[-1]
    assert audit_call.args[1] == "persist_website_extraction"
    md = audit_call.kwargs.get("metadata") or {}
    assert md.get("source_url") == "https://wedotalent.cc"


@pytest.mark.asyncio
async def test_analyze_website_phase2_clarifies_when_no_fields(
    domain: CompanySettingsDomain,
) -> None:
    resp = await domain._handle_analyze_website(
        {"company_id": "co_demo", "confirm": True, "confirmed_fields": {}},
        _ctx(),
    )
    assert resp.needs_clarification
    assert "confirmed_fields" in (resp.clarification_question or "")


@pytest.mark.asyncio
async def test_analyze_website_phase2_clarifies_when_fields_unrecognized(
    domain: CompanySettingsDomain,
) -> None:
    """confirm=True with `confirmed_fields` that map to no savable section
    must clarify instead of returning success with empty persisted_sections."""
    section_target = (
        "app.domains.company_settings.agents.company_tool_registry."
        "_wrap_save_company_section"
    )
    benefits_target = (
        "app.domains.company_settings.agents.company_tool_registry."
        "_wrap_save_company_benefits"
    )
    fake_section = AsyncMock()
    fake_benefits = AsyncMock()
    with patch(section_target, fake_section), patch(benefits_target, fake_benefits):
        resp = await domain._handle_analyze_website(
            {
                "company_id": "co_demo",
                "confirm": True,
                "confirmed_fields": {"unknown_field": "x", "another": 42},
            },
            _ctx(),
        )
    assert resp.needs_clarification
    assert "secao gravavel" in (resp.clarification_question or "")
    fake_section.assert_not_called()
    fake_benefits.assert_not_called()


@pytest.mark.asyncio
async def test_analyze_website_phase2_refuses_tenant_mismatch(
    domain: CompanySettingsDomain,
) -> None:
    """The same tenant guard that protects every other write action must
    also fire BEFORE the confirm path on analyze_website."""
    section_target = (
        "app.domains.company_settings.agents.company_tool_registry."
        "_wrap_save_company_section"
    )
    fake_save = AsyncMock()
    with patch(section_target, fake_save):
        resp = await domain._handle_analyze_website(
            {
                "company_id": "co_attacker",
                "confirm": True,
                "confirmed_fields": {"mission": "x"},
            },
            _ctx(tenant="co_victim"),
        )
    assert resp.success is False
    assert (resp.data or {}).get("reason") == "tenant_mismatch"
    fake_save.assert_not_called()


# ---------------------------------------------------------------------------
# Task #766 — Beneficios via chat com schema canonico completo.
# Cobre: clarification quando faltam pares obrigatorios, success com
# input completo (chat), success por planilha (import_benefits_from_data),
# success por site apos approval humano, e guardrail anti-regressao do
# schema (CANONICAL_BENEFIT_FIELDS deve cobrir todas as colunas do
# modelo CompanyBenefit).
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_configure_benefits_clarification_when_value_without_value_type(
    domain: CompanySettingsDomain,
) -> None:
    """value sem value_type deve disparar clarification antes de gravar."""
    resp = await domain._handle_configure_benefits(
        {
            "company_id": "co_demo",
            "benefits": [{"name": "Vale Refeicao", "value": 800}],
        },
        _ctx(),
    )
    assert resp.needs_clarification, (
        f"esperado clarification, veio success={resp.success} error={resp.error}"
    )
    q = (resp.clarification_question or "").lower()
    assert "value_type" in q or "tipo" in q
    assert (resp.data or {}).get("expected_fields"), (
        "expected_fields deve listar campos canonicos para o usuario completar"
    )


@pytest.mark.asyncio
async def test_configure_benefits_clarification_when_monetary_without_value(
    domain: CompanySettingsDomain,
) -> None:
    """value_type=monetary sem value e sem value_details deve clarificar."""
    resp = await domain._handle_configure_benefits(
        {
            "company_id": "co_demo",
            "benefits": [
                {"name": "Plano de Saude", "value_type": "monetary"},
            ],
        },
        _ctx(),
    )
    assert resp.needs_clarification
    assert "monetary" in (resp.clarification_question or "").lower()


@pytest.mark.asyncio
async def test_configure_benefits_success_with_full_canonical_schema(
    domain: CompanySettingsDomain,
) -> None:
    """Quando o input ja vem completo, o handler delega passando o schema
    inteiro (provider, value, value_type, percentage_value, etc.) para
    a tool canonica — paridade com o formulario do Hub."""
    target = (
        "app.domains.company_settings.agents.company_tool_registry"
        "._wrap_save_company_benefits"
    )
    fake = AsyncMock(return_value={
        "success": True,
        "data": {"inserted": 1, "deactivated": 0, "mode": "append",
                 "source": "chat", "names": ["Plano de Saude Premium"]},
        "message": "Beneficios salvos: 1 inserido(s).",
    })
    rich_benefit = {
        "name": "Plano de Saude Premium",
        "category": "health",
        "description": "Cobertura nacional, sem coparticipacao.",
        "icon": "hospital",
        "provider": "Bradesco Saude",
        "value": 850.0,
        "value_type": "monetary",
        "value_details": "Subsidio integral pela empresa",
        "seniority_levels": ["junior", "pleno", "senior"],
        "waiting_period_days": 30,
        "is_highlighted": True,
        "is_mandatory": False,
        "is_discount": False,
        "order": 4,
    }
    with patch(target, fake):
        resp = await domain._handle_configure_benefits(
            {"company_id": "co_demo", "benefits": [rich_benefit]},
            _ctx(),
        )
    assert resp.success, f"esperado success, veio error={resp.error}"
    fake.assert_awaited_once()
    sent = fake.await_args.kwargs["benefits"]
    assert len(sent) == 1
    for k in (
        "provider", "value", "value_type", "value_details",
        "seniority_levels", "waiting_period_days",
        "is_mandatory", "is_discount",
    ):
        assert sent[0].get(k) == rich_benefit[k], f"campo {k} perdido a caminho da tool"
    assert fake.await_args.kwargs.get("source") == "chat"


@pytest.mark.asyncio
async def test_import_benefits_from_data_delegates_to_canonical_wrapper() -> None:
    """A tool de import (planilha/JSON) deve delegar a tool canonica
    com source='spreadsheet' — sem schema reduzido, sem bug `is_highlight`."""
    from app.domains.company_settings.tools.import_tools import (
        import_benefits_from_data,
    )

    class _FakeContext:
        company_id = "co_demo"
        user_id = "u_demo"

    target = (
        "app.domains.company_settings.agents.company_tool_registry"
        "._wrap_save_company_benefits"
    )
    fake = AsyncMock(return_value={
        "success": True,
        "data": {"inserted": 2, "deactivated": 0, "mode": "append",
                 "source": "spreadsheet", "names": ["A", "B"]},
        "message": "Beneficios salvos: 2 inserido(s).",
    })
    rows = [
        {"name": "Auxilio Creche", "category": "family",
         "value": 400, "value_type": "monetary", "provider": "RH"},
        {"nome": "Vale Cultura", "category": "wellness",
         "is_highlight": True},
    ]
    with patch(target, fake):
        resp = await import_benefits_from_data(
            benefits=rows,
            replace_existing=False,
            _context=_FakeContext(),
            source="spreadsheet",
        )
    assert resp["success"] is True
    assert resp["inserted_count"] == 2
    fake.assert_awaited_once()
    kwargs = fake.await_args.kwargs
    assert kwargs["source"] == "spreadsheet"
    assert kwargs["mode"] == "append"
    sent = kwargs["benefits"]
    names = {b.get("name") for b in sent}
    assert names == {"Auxilio Creche", "Vale Cultura"}
    second = next(b for b in sent if b["name"] == "Vale Cultura")
    assert second.get("is_highlighted") is True
    assert "is_highlight" not in second
    first = next(b for b in sent if b["name"] == "Auxilio Creche")
    assert first.get("value") == 400
    assert first.get("value_type") == "monetary"
    assert first.get("provider") == "RH"


@pytest.mark.asyncio
async def test_import_benefits_from_data_propagates_clarification() -> None:
    """Se a tool canonica detecta campo faltante, o importer NAO grava e
    devolve needs_clarification=True (sem fallback silencioso)."""
    from app.domains.company_settings.tools.import_tools import (
        import_benefits_from_data,
    )

    class _FakeContext:
        company_id = "co_demo"
        user_id = "u_demo"

    target = (
        "app.domains.company_settings.agents.company_tool_registry"
        "._wrap_save_company_benefits"
    )
    fake = AsyncMock(return_value={
        "success": False,
        "needs_clarification": True,
        "data": {
            "missing_fields": ["'X': value_type=monetary exige 'value'."],
            "expected_fields": ["name", "value", "value_type"],
        },
        "message": "Antes de gravar...",
    })
    with patch(target, fake):
        resp = await import_benefits_from_data(
            benefits=[{"name": "X", "value_type": "monetary"}],
            _context=_FakeContext(),
        )
    assert resp["success"] is False
    assert resp.get("needs_clarification") is True
    assert resp["inserted_count"] == 0
    assert resp.get("expected_fields") == ["name", "value", "value_type"]


@pytest.mark.asyncio
async def test_analyze_website_phase1_proposes_structured_benefits(
    domain: CompanySettingsDomain,
) -> None:
    """Phase 1 do analyze_website deve promover beneficios extraidos para
    dicts {name} e listar `expected_fields` que o humano deve completar
    antes de confirmar (Task #766)."""
    target = (
        "app.domains.company.services.company_scraper_service.CompanyScraperService"
    )
    fake_instance = AsyncMock()
    fake_instance.scrape_website = AsyncMock(
        return_value={
            "success": True,
            "pages_scraped": 2,
            "pages": [],
            "content": (
                "## Beneficios\n- Vale Refeicao\n- Plano de Saude\n- Gympass\n"
            ),
            "source": "live",
        }
    )
    with patch(target, return_value=fake_instance):
        resp = await domain._handle_analyze_website(
            {"website": "https://wedotalent.cc"}, _ctx()
        )
    assert resp.success
    pw = (resp.data or {}).get("pending_writes") or {}
    benefits_pw = pw.get("benefits")
    assert isinstance(benefits_pw, list) and benefits_pw
    assert all(isinstance(b, dict) and b.get("name") for b in benefits_pw)
    assert {b["name"] for b in benefits_pw} >= {"Vale Refeicao", "Plano de Saude"}
    assert resp.data.get("requires_human_approval") is True
    assert "complete antes de confirmar" in (resp.message or "").lower()


def test_canonical_benefit_fields_cover_company_benefit_columns() -> None:
    """Anti-regressao (harness-engineering / Task #766): qualquer coluna nova
    no modelo CompanyBenefit precisa ser refletida em CANONICAL_BENEFIT_FIELDS
    para evitar que o chat / planilha / site voltem a aceitar schema reduzido.
    """
    from app.domains.company_settings.agents.company_tool_registry import (
        CANONICAL_BENEFIT_FIELDS,
    )
    from lia_models.company_benefit import CompanyBenefit

    db_columns = {c.name for c in CompanyBenefit.__table__.columns}
    system_only = {"id", "company_id", "created_at", "updated_at"}
    contract_columns = db_columns - system_only
    missing = contract_columns - CANONICAL_BENEFIT_FIELDS
    assert not missing, (
        f"CANONICAL_BENEFIT_FIELDS desatualizado — colunas novas no modelo "
        f"CompanyBenefit nao mapeadas: {sorted(missing)}. "
        "Atualize CANONICAL_BENEFIT_FIELDS e o INSERT em "
        "_wrap_save_company_benefits."
    )
