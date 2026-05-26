"""Sprint 3.2 sensor (2026-05-26) — POST /api/v1/lia/proactive-context
endpoint canonical contract.

Validates:
  1. Endpoint registered + route resolves
  2. Schema WeDoBaseModel (extra='forbid' prevents unknown fields)
  3. Multi-tenancy: company_id via JWT Depends (não via payload, REGRA Pydantic R2)
  4. Store integration: ProactiveContextStore.put is called
  5. Fail-open: response.ok always True (cliente não retry)
"""
from unittest.mock import AsyncMock, patch

import pytest


def test_endpoint_router_registered():
    """Router exists + has expected route POST /."""
    from app.api.v1 import proactive_context
    routes = [r.path for r in proactive_context.router.routes]
    assert "/lia/proactive-context" in routes, f"Router routes: {routes}"
    methods = [tuple(sorted(r.methods)) for r in proactive_context.router.routes if r.path == "/lia/proactive-context"]
    assert any("POST" in m for m in methods), f"POST not registered: {methods}"


def test_schema_forbids_company_id_in_payload():
    """Sprint Pydantic R2 canonical: company_id NUNCA no request body
    (vem do JWT via Depends). Schema deve rejeitar extra fields."""
    from app.api.v1.proactive_context import ProactiveContextNoteInput

    # company_id no payload deve falhar (extra='forbid' via WeDoBaseModel)
    with pytest.raises(Exception):  # pydantic ValidationError
        ProactiveContextNoteInput(
            actionId="configure_workforce",
            section="workforce",
            company_id="some-uuid",  # ← extra forbidden
        )


def test_schema_accepts_canonical_payload():
    """Schema canonical: actionId + section required, field+value optional."""
    from app.api.v1.proactive_context import ProactiveContextNoteInput

    p = ProactiveContextNoteInput(
        actionId="configure_hiring_policy",
        section="hiring_policies",
        field="default_duration_minutes",
        value=30,
    )
    assert p.actionId == "configure_hiring_policy"
    assert p.section == "hiring_policies"
    assert p.field == "default_duration_minutes"
    assert p.value == 30


def test_schema_minimal_payload():
    """field e value são opcionais."""
    from app.api.v1.proactive_context import ProactiveContextNoteInput
    p = ProactiveContextNoteInput(actionId="x", section="y")
    assert p.field is None
    assert p.value is None


@pytest.mark.asyncio
async def test_endpoint_calls_store_put_with_jwt_company_id():
    """Sprint 3.2 G9 wire: endpoint chama ProactiveContextStore.put com
    company_id do JWT (Depends), NÃO do payload."""
    from app.api.v1.proactive_context import (
        ProactiveContextNoteInput,
        post_proactive_context,
    )

    class _FakeUser:
        id = "user-fixture"
        company_id = "ignored-from-user-model"

    payload = ProactiveContextNoteInput(
        actionId="configure_workforce",
        section="workforce",
        field="headcount",
        value=42,
    )
    with patch(
        "app.api.v1.proactive_context.ProactiveContextStore.put",
        new=AsyncMock(return_value=True),
    ) as put_spy:
        result = await post_proactive_context(
            payload=payload,
            current_user=_FakeUser(),
            company_id="jwt-company-uuid",  # canonical from Depends
        )
    assert result.ok is True
    assert result.stored is True
    put_spy.assert_called_once()
    call_kwargs = put_spy.call_args.kwargs
    assert call_kwargs["company_id"] == "jwt-company-uuid", (
        "company_id deve vir do JWT (Depends), NÃO de payload nem de User.company_id"
    )
    assert call_kwargs["user_id"] == "user-fixture"
    assert call_kwargs["action_id"] == "configure_workforce"
    assert call_kwargs["section"] == "workforce"
    assert call_kwargs["field"] == "headcount"
    assert call_kwargs["value"] == 42


@pytest.mark.asyncio
async def test_endpoint_fail_open_when_store_returns_false():
    """Redis indisponível → store.put retorna False → response {ok:True,
    stored:False}. Cliente NÃO retry (UX local com debounce já é resiliente)."""
    from app.api.v1.proactive_context import (
        ProactiveContextNoteInput,
        post_proactive_context,
    )

    class _FakeUser:
        id = "user-fixture"
        company_id = "x"

    payload = ProactiveContextNoteInput(actionId="x", section="y")
    with patch(
        "app.api.v1.proactive_context.ProactiveContextStore.put",
        new=AsyncMock(return_value=False),
    ):
        result = await post_proactive_context(
            payload=payload,
            current_user=_FakeUser(),
            company_id="jwt",
        )
    assert result.ok is True, "ok=True always (cliente não retry)"
    assert result.stored is False, "stored reflete real status do Redis"


@pytest.mark.asyncio
async def test_store_put_validates_required_fields():
    """ProactiveContextStore.put retorna False quando required fields vazios."""
    from app.shared.services.proactive_context_store import ProactiveContextStore

    # missing company_id
    assert await ProactiveContextStore.put(
        company_id="", user_id="u", action_id="a", section="s",
        field=None, value=None,
    ) is False

    # missing user_id
    assert await ProactiveContextStore.put(
        company_id="c", user_id="", action_id="a", section="s",
        field=None, value=None,
    ) is False

    # missing action_id
    assert await ProactiveContextStore.put(
        company_id="c", user_id="u", action_id="", section="s",
        field=None, value=None,
    ) is False
