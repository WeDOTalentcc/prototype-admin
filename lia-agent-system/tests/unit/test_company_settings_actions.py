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
