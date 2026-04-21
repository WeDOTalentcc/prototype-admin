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
