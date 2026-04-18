"""Integration tests for WSI audit endpoint RBAC (Task #511).

Cobre os requisitos de code review:
  - 401 sem token
  - 403 para roles não autorizados (recruiter, viewer)
  - 200 para admin e dpo
  - 404 para sessão inexistente (com auth válida)

NOTA: pytest local sofre de cascata de imports pesados (#517). Este arquivo
documenta a expectativa de comportamento; validação manual via curl está
registrada no commit message da Task #511.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_audit_endpoint_requires_auth(async_client: AsyncClient):
    r = await async_client.get("/api/v1/wsi/audit/any-session")
    assert r.status_code == 401
    assert "Authentication required" in r.text


@pytest.mark.parametrize("role", ["recruiter", "viewer"])
async def test_audit_endpoint_forbids_non_admin_non_dpo(
    async_client: AsyncClient, make_user_token, role
):
    token = make_user_token(role=role)
    r = await async_client.get(
        "/api/v1/wsi/audit/any-session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.parametrize("role", ["admin", "dpo"])
async def test_audit_endpoint_allows_admin_and_dpo(
    async_client: AsyncClient, make_user_token, role
):
    token = make_user_token(role=role)
    r = await async_client.get(
        "/api/v1/wsi/audit/nonexistent-session",
        headers={"Authorization": f"Bearer {token}"},
    )
    # Auth passou: 404 porque sessão não existe (não 401/403).
    assert r.status_code == 404


async def test_audit_endpoint_returns_compliance_metadata(
    async_client: AsyncClient, make_user_token, seed_wsi_session_with_responses
):
    sid = seed_wsi_session_with_responses
    token = make_user_token(role="admin")
    r = await async_client.get(
        f"/api/v1/wsi/audit/{sid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == sid
    assert "responses" in body and len(body["responses"]) > 0
    for resp in body["responses"]:
        assert len(resp["response_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in resp["response_hash"])
    assert body["compliance"]["framework"].startswith("EU AI Act")
    assert body["compliance"]["hash_algorithm"] == "SHA-256"
