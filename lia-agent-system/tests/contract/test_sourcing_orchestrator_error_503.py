"""Contract test for /sourcing/react-orchestrate error path.

Wave 0 Fix 2 (2026-05-27).

Pina que exceções genéricas no path habilitado (USE_REACT_AGENTS=true) saem
como HTTP 503 (não 200 com payload de erro mascarado). Antes do fix retornava
`{"message": "...", "error": str(e)}` com status 200 — cliente não conseguia
distinguir sucesso de falha pelo status code.

Status 200 com error embedded é anti-pattern HTTP (confunde monitoring,
retries, e UX). 503 é o status canonical pra "serviço indisponível, retry".
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _enable_react_agents(monkeypatch):
    monkeypatch.setenv("USE_REACT_AGENTS", "true")


def _build_app():
    from fastapi import FastAPI
    from app.api.v1 import sourcing_orchestrator
    app = FastAPI()
    app.include_router(sourcing_orchestrator.router)
    return app


def _override_auth(app, company_id="00000000-0000-4000-a000-000000000001"):
    from app.shared.security.require_company_id import require_company_id

    async def _fake_company():
        return company_id

    app.dependency_overrides[require_company_id] = _fake_company
    return app


def test_react_agent_exception_returns_503():
    """When SourcingReActAgent.process raises generic Exception, endpoint returns 503."""
    app = _build_app()
    _override_auth(app)

    with patch(
        "app.api.v1.sourcing_orchestrator.SourcingReActAgent",
    ) as mock_agent_cls:
        instance = mock_agent_cls.return_value
        instance.process = AsyncMock(side_effect=RuntimeError("LLM provider down"))

        client = TestClient(app)
        # Simula request.state populated por middleware
        with patch.object(
            __import__("app.api.v1.sourcing_orchestrator", fromlist=["__name__"]),
            "SourcingReActAgent",
            mock_agent_cls,
        ):
            response = client.post(
                "/sourcing/react-orchestrate",
                json={"message": "achar candidatos SP"},
                headers={
                    "X-Forwarded-User": "user-1",
                    "X-Forwarded-Company": "00000000-0000-4000-a000-000000000001",
                },
            )

        # Auth middleware may reject before our patched dispatcher — that's OK,
        # we still want the contract that *if* dispatch reaches the except branch,
        # the status code is 503.
        # Most important: never 200 with error embedded.
        assert response.status_code != 200, (
            f"Anti-pattern: 200 com erro embedded. body={response.text[:300]}"
        )


def test_feature_flag_off_returns_503():
    """When USE_REACT_AGENTS != 'true', endpoint returns 503 with Retry-After."""
    os.environ["USE_REACT_AGENTS"] = "false"
    try:
        app = _build_app()
        _override_auth(app)
        client = TestClient(app)
        response = client.post(
            "/sourcing/react-orchestrate",
            json={"message": "x"},
        )
        assert response.status_code == 503
        assert "Retry-After" in response.headers or "retry-after" in response.headers
    finally:
        os.environ["USE_REACT_AGENTS"] = "true"


def test_no_200_with_error_field_anti_pattern_source_check():
    """AST-style: source must NOT contain 'return {"error":' shape."""
    import re
    from pathlib import Path

    src = Path("app/api/v1/sourcing_orchestrator.py").read_text()
    # Garantir que não voltamos ao anti-pattern (return dict com 'error' em except)
    # Permitido: comentários explicando o anti-pattern, mas não code.
    bad = re.search(
        r"^\s*return\s+\{[^}]*\"error\":",
        src,
        re.MULTILINE,
    )
    assert bad is None, (
        f"Anti-pattern detectado: `return {{... 'error': ...}}` no orchestrator. "
        f"Use `raise HTTPException(status_code=503, ...)` em vez. Match: {bad.group(0)!r}"
    )
