"""
Contract tests for Wave D2.1 + D2.2 multi-tenancy threading.

Registrado 2026-05-27 (Wave D2 saneamento Studio).

Sensores:
- D2.1 (onboarding.py): tenant_id threaded from JWT company_id into LLM factory.
- D2.2 (whatsapp_webhook.py): tenant_id threaded from session.account_id (post-phone
  lookup) into LLM factory.

Sem esses sensores, a recidiva é trivial: copy-paste de `tenant_id=None` em novo
endpoint quebra multi-tenancy sem CI alarme.
"""
from __future__ import annotations

import inspect

import pytest


@pytest.mark.contract
def test_onboarding_get_orchestrator_accepts_tenant_id():
    """D2.1: _get_orchestrator helper must accept tenant_id kwarg."""
    from app.api.v1 import onboarding

    sig = inspect.signature(onboarding._get_orchestrator)
    assert "tenant_id" in sig.parameters, (
        "Regression Wave D2.1: _get_orchestrator must thread tenant_id from caller. "
        "Previously hardcoded tenant_id=None — multi-tenancy gap (PII risk + "
        "BYOK config gap)."
    )


@pytest.mark.contract
def test_onboarding_endpoints_thread_company_id_into_orchestrator():
    """D2.1: all endpoints that touch orchestrator must pass tenant_id=company_id."""
    import ast
    from pathlib import Path

    src = Path("app/api/v1/onboarding.py").read_text()
    tree = ast.parse(src)

    calls_get_orch: list[tuple[int, list[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            call = node.value
            func = call.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name == "_get_orchestrator":
                kw_names = [kw.arg for kw in call.keywords]
                calls_get_orch.append((node.lineno, kw_names))

    # Every endpoint that calls _get_orchestrator MUST pass tenant_id.
    missing = [ln for ln, kw in calls_get_orch if "tenant_id" not in kw]
    assert not missing, (
        f"Wave D2.1 regression: _get_orchestrator calls at lines {missing} do "
        f"NOT thread tenant_id. Every endpoint with Depends(require_company_id) "
        f"MUST pass tenant_id=company_id."
    )


@pytest.mark.contract
def test_whatsapp_get_orchestrator_accepts_tenant_id():
    """D2.2: whatsapp webhook _get_orchestrator helper must accept tenant_id."""
    from app.api.v1 import whatsapp_webhook

    sig = inspect.signature(whatsapp_webhook._get_orchestrator)
    assert "tenant_id" in sig.parameters, (
        "Regression Wave D2.2: whatsapp webhook _get_orchestrator must accept "
        "tenant_id (resolved via session.account_id from phone lookup)."
    )


@pytest.mark.contract
def test_whatsapp_post_session_calls_pass_tenant_id():
    """D2.2: orchestrator calls after _find_session_by_phone must thread tenant_id."""
    import ast
    from pathlib import Path

    src = Path("app/api/v1/whatsapp_webhook.py").read_text()
    tree = ast.parse(src)

    calls: list[tuple[int, list[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            call = node.value
            func = call.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name == "_get_orchestrator":
                kw_names = [kw.arg for kw in call.keywords]
                calls.append((node.lineno, kw_names))

    # All 3 call sites must pass tenant_id (None acceptable only for pre-consent
    # LGPD flow, but the kwarg MUST be explicit so reader sees the decision).
    missing = [ln for ln, kw in calls if "tenant_id" not in kw]
    assert not missing, (
        f"Wave D2.2 regression: whatsapp _get_orchestrator calls at lines "
        f"{missing} omit tenant_id kwarg. Even tenant_id=None must be EXPLICIT "
        f"(documented pre-session/LGPD-rejection branch)."
    )
