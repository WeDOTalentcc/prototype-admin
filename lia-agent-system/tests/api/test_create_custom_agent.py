"""P0 regression guard — POST /custom-agents must return 201, not 500.

Root cause (2026-05-27, Wave C2.1): custom_agents.create_custom_agent referenced
`body.category`, but CreateCustomAgentRequest has no `category` field — it has
`domain` (default "general"). `body.category` raised AttributeError on EVERY
create call => raw Internal Server Error 500. ALL agent creation was broken.

Why the existing smoke test (tests/contract/test_endpoint_smoke.py) did NOT catch
it: the smoke test hits endpoints without constructing a valid request body, so the
POST never reached the `body.category` line with a real CreateCustomAgentRequest.

This test calls the handler directly with a fully-populated request body — the path
that was broken — so AttributeError surfaces immediately and any future drift to a
non-existent field is caught in CI.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v1 import custom_agents as ca_module
from app.schemas.custom_agent import CreateCustomAgentRequest

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def current_user():
    u = MagicMock()
    u.id = "user-1"
    u.company_id = "comp-1"
    return u


def _valid_body(domain="screening"):
    return CreateCustomAgentRequest(
        name="Recrutador Tech",
        role="Triagem de candidatos backend",
        description="Agente de triagem",
        system_prompt="Você é um agente de triagem que avalia candidatos de forma justa.",
        allowed_tools=["search_candidates", "get_candidate_details"],
        domain=domain,
        context_level="standard",
        max_steps=8,
        temperature=0.5,
    )


def _fake_created_agent(domain="screening"):
    agent = MagicMock()
    agent.id = "agent-1"
    agent.name = "Recrutador Tech"
    agent.domain = domain
    agent.allowed_tools = ["search_candidates", "get_candidate_details"]
    agent.status = "draft"
    agent.to_dict = MagicMock(
        return_value={
            "id": "agent-1",
            "company_id": "comp-1",
            "created_by": "user-1",
            "name": "Recrutador Tech",
            "role": "Triagem de candidatos backend",
            "system_prompt": "Você é um agente de triagem que avalia candidatos de forma justa.",
            "allowed_tools": ["search_candidates", "get_candidate_details"],
            "domain": domain,
            "status": "draft",
        }
    )
    return agent


def _patches(quota_keys, created_agent):
    """Patch quota enforcement + marketplace service + audit + FairnessGuard.

    quota_keys is a list captured by the fake enforce_quota.
    """

    async def fake_enforce_quota(quota_key, company_id, db):  # noqa: ANN001
        quota_keys.append(quota_key)

    fg_instance = MagicMock()
    fg_result = MagicMock()
    fg_result.is_blocked = False
    fg_instance.check = MagicMock(return_value=fg_result)

    return [
        patch(
            "app.services.quota_enforcement.enforce_quota",
            side_effect=fake_enforce_quota,
        ),
        patch.object(
            ca_module.agent_marketplace_service,
            "create_agent",
            AsyncMock(return_value=created_agent),
        ),
        patch(
            "app.domains.agent_studio._audit_helper.studio_audit",
            AsyncMock(return_value=None),
        ),
        patch(
            "app.shared.compliance.fairness_guard.FairnessGuard",
            return_value=fg_instance,
        ),
    ]


async def test_create_custom_agent_valid_payload_returns_201(mock_db, current_user):
    """Full valid payload => handler succeeds (no AttributeError / no 500).

    This is THE guard that was missing: before the fix `body.category` raised
    AttributeError here and the response was Internal Server Error 500.
    """
    quota_keys = []
    created = _fake_created_agent(domain="screening")
    patches = _patches(quota_keys, created)
    for p in patches:
        p.start()
    try:
        resp = await ca_module.create_custom_agent(
            body=_valid_body(domain="screening"),
            current_user=current_user,
            db=mock_db,
            company_id="comp-1",
        )
    finally:
        for p in patches:
            p.stop()

    assert resp.id == "agent-1"
    assert resp.domain == "screening"
    mock_db.commit.assert_awaited()


async def test_create_custom_agent_domain_sourcing_uses_sourcing_quota(mock_db, current_user):
    """domain='sourcing' => quota_key 'sourcing_agents' (separate quota)."""
    quota_keys = []
    created = _fake_created_agent(domain="sourcing")
    patches = _patches(quota_keys, created)
    for p in patches:
        p.start()
    try:
        await ca_module.create_custom_agent(
            body=_valid_body(domain="sourcing"),
            current_user=current_user,
            db=mock_db,
            company_id="comp-1",
        )
    finally:
        for p in patches:
            p.stop()

    assert quota_keys == ["sourcing_agents"]


async def test_create_custom_agent_domain_screening_uses_custom_quota(mock_db, current_user):
    """domain='screening' => quota_key 'custom_agents'."""
    quota_keys = []
    created = _fake_created_agent(domain="screening")
    patches = _patches(quota_keys, created)
    for p in patches:
        p.start()
    try:
        await ca_module.create_custom_agent(
            body=_valid_body(domain="screening"),
            current_user=current_user,
            db=mock_db,
            company_id="comp-1",
        )
    finally:
        for p in patches:
            p.stop()

    assert quota_keys == ["custom_agents"]


async def test_create_custom_agent_default_domain_uses_custom_quota(mock_db, current_user):
    """No explicit domain => default 'general' => quota_key 'custom_agents' (no crash)."""
    quota_keys = []
    created = _fake_created_agent(domain="general")
    patches = _patches(quota_keys, created)

    body = CreateCustomAgentRequest(
        name="Agente Geral",
        role="Tarefas gerais",
        system_prompt="Você é um agente que ajuda com tarefas gerais de recrutamento.",
        allowed_tools=["search_candidates"],
        # domain omitted => defaults to "general"
    )
    assert body.domain == "general"

    for p in patches:
        p.start()
    try:
        await ca_module.create_custom_agent(
            body=body,
            current_user=current_user,
            db=mock_db,
            company_id="comp-1",
        )
    finally:
        for p in patches:
            p.stop()

    assert quota_keys == ["custom_agents"]


async def test_create_custom_agent_uses_jwt_company_id_not_payload(mock_db, current_user):
    """Multi-tenancy: create_agent is called with current_user.company_id (from JWT).

    CreateCustomAgentRequest has no company_id field (REGRA 2), so the only source
    is the authenticated user. This pins that invariant.
    """
    quota_keys = []
    created = _fake_created_agent(domain="screening")

    captured = {}

    async def capture_create(**kwargs):  # noqa: ANN003
        captured.update(kwargs)
        return created

    patches = _patches(quota_keys, created)
    # Replace the marketplace patch with a capturing one (last item is FairnessGuard,
    # marketplace is index 1 — rebuild explicitly for clarity).
    for p in patches:
        p.stop() if False else None  # no-op; patches not started yet

    with patch(
        "app.services.quota_enforcement.enforce_quota",
        side_effect=lambda *a, **k: quota_keys.append(a[0] if a else k.get("quota_key")),
    ), patch.object(
        ca_module.agent_marketplace_service, "create_agent", side_effect=capture_create
    ), patch(
        "app.domains.agent_studio._audit_helper.studio_audit", AsyncMock(return_value=None)
    ), patch(
        "app.shared.compliance.fairness_guard.FairnessGuard"
    ) as fg_cls:
        fg_res = MagicMock()
        fg_res.is_blocked = False
        fg_cls.return_value.check = MagicMock(return_value=fg_res)
        await ca_module.create_custom_agent(
            body=_valid_body(domain="screening"),
            current_user=current_user,
            db=mock_db,
            company_id="comp-1",
        )

    assert captured.get("company_id") == "comp-1"
    assert captured.get("created_by") == "user-1"
    # The request body dict must NOT carry a company_id field.
    assert "company_id" not in captured.get("data", {})
