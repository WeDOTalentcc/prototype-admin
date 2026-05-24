"""
Contract smoke test canonical — cada endpoint declarado na OpenAPI responde algo válido.

Registrado 2026-05-20 pós-audit E2E (sensor #2 do harness analysis).

Detecta — em CI, ANTES de produção:
  - NameError em handlers (audit F7.B1 sourcing_pipeline_service)
  - Imports faltando que só crasham em runtime
  - UUID + Path pattern Pydantic 2.10 regression (audit F2.B1)
  - Service methods referenciados mas não implementados (audit F8.B1)
  - Schema mismatches DB ↔ Pydantic response (audit F8.B2)

Princípio: nenhum endpoint deveria retornar HTTP 500 em smoke test com payload
mínimo. Se retorna, é defeito de implementação que escapou code review.

Roda contra uvicorn local (port 8001) com demo user seedado.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_URL = os.environ.get("LIA_BACKEND_URL", "http://127.0.0.1:8001")
DEMO_EMAIL = os.environ.get("DEV_AUTO_LOGIN_EMAIL", "demo@wedotalent.com")
DEMO_PASSWORD = os.environ.get("DEV_AUTO_LOGIN_PASSWORD", "demo123")

# Status codes que NÃO indicam bug de implementação:
#   200, 201, 204 — success
#   400, 401, 403, 404 — client error (esperado em payload incompleto)
#   422 — validation error (esperado em sample payload genérico)
#   413, 429 — payload too large / rate limited (acceptable em smoke)
EXPECTED_NON_500_CODES = {200, 201, 204, 400, 401, 403, 404, 413, 422, 429}

# Endpoints conhecidos como problemáticos — skip explícito com motivo.
# REGRA: nunca adicione skip sem motivo + ticket associado.
SKIP_ENDPOINTS: dict[tuple[str, str], str] = {
    # ("/api/v1/example", "POST"): "Ticket WT-XXXX — endpoint requer fixture específica",
}

# Sample payload por endpoint (quando default {} não é suficiente).
# Path placeholders são substituídos no test.
SAMPLE_PAYLOADS: dict[tuple[str, str], dict[str, Any]] = {
    ("/api/v1/jd/generate", "POST"): {
        "job_title": "Test Job (smoke)",
        "company_id": "00000000-0000-4000-a000-000000000001",
    },
    ("/api/v1/skills-catalog/wizard/suggest-skills", "POST"): {
        "job_title": "Test Job (smoke)",
        "company_id": "00000000-0000-4000-a000-000000000001",
    },
    # Bug A fix (2026-05-24): endpoint requer `identifier` no body.
    # Smoke test estava enviando {} → 422 falso positivo. Endpoint deprecated
    # (rails-migration 7.1) mas ainda no canonical até migração completar.
    ("/api/v1/job-vacancies/find-by-identifier", "POST"): {
        "identifier": "V0001",  # short-ID válido (PLACEHOLDER); endpoint retornará 404 se não existir
    },
    # Adicionar mais payloads conforme falsos positivos aparecem.
}

# ID placeholder canonical para path params {job_id}, {candidate_id}, etc.
# Usar UUID v4 válido — endpoints com Path(pattern=UUID_OR_BIGINT_PATTERN) aceitam.
PLACEHOLDER_ID = "00000000-0000-4000-a000-000000000000"  # zero UUID, não existirá no DB → 404


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def access_token() -> str:
    """Obtém JWT do demo user. Falha hard se backend offline."""
    response = httpx.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("data", {}).get("access_token")
    if not token:
        pytest.fail(f"Auth login não retornou access_token. Response: {payload}")
    return token


@pytest.fixture(scope="session")
def openapi_routes(access_token: str) -> list[tuple[str, str]]:
    """Extrai (path, method) de cada endpoint registrado na OpenAPI."""
    response = httpx.get(f"{BACKEND_URL}/openapi.json", timeout=10)
    response.raise_for_status()
    spec = response.json()
    routes = []
    for path, methods in spec.get("paths", {}).items():
        for method in methods:
            if method.lower() in ("get", "post", "put", "patch", "delete"):
                routes.append((path, method.upper()))
    return routes


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _substitute_path_params(path: str) -> str:
    """Substitui {param} por placeholder UUID. Endpoint deve retornar 404 (id inexistente)."""
    import re
    return re.sub(r"\{[^}]+\}", PLACEHOLDER_ID, path)


def _build_payload(path: str, method: str) -> dict[str, Any]:
    """Retorna sample payload pra (path, method) ou {} default."""
    return SAMPLE_PAYLOADS.get((path, method), {})


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────
def pytest_generate_tests(metafunc):
    """Parametrize dynamicamente a partir do openapi.json."""
    if "route" in metafunc.fixturenames:
        # Need to fetch OpenAPI at collection time — use httpx direct
        try:
            response = httpx.get(f"{BACKEND_URL}/openapi.json", timeout=10)
            response.raise_for_status()
            spec = response.json()
            routes = [
                (path, method.upper())
                for path, methods in spec.get("paths", {}).items()
                for method in methods
                if method.lower() in ("get", "post", "put", "patch", "delete")
            ]
            metafunc.parametrize(
                "route",
                routes,
                ids=[f"{m} {p}" for p, m in routes],
            )
        except Exception as e:
            pytest.skip(f"Backend offline ou OpenAPI inacessível: {e}")


def test_endpoint_does_not_500(route: tuple[str, str], access_token: str):
    """
    Cada endpoint da OpenAPI responde com status válido (não 500).

    HTTP 500 em smoke indica defeito de implementação:
      - NameError, ImportError (símbolo faltando)
      - Service method ausente
      - Pydantic constraint inválida em path param
      - Schema mismatch DB ↔ response
    """
    path, method = route

    # Skip endpoints conhecidos
    if (path, method) in SKIP_ENDPOINTS:
        pytest.skip(f"SKIP documentado: {SKIP_ENDPOINTS[(path, method)]}")

    # Substituir path params + montar payload
    resolved_path = _substitute_path_params(path)
    payload = _build_payload(path, method)
    url = f"{BACKEND_URL}{resolved_path}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = httpx.request(
        method,
        url,
        headers=headers,
        json=payload if method in ("POST", "PUT", "PATCH") else None,
        timeout=30,
        follow_redirects=True,
    )

    assert response.status_code != 500, (
        f"\n❌ Endpoint {method} {path} retornou HTTP 500 — defeito de implementação detectado.\n"
        f"\n"
        f"   Resolved URL: {url}\n"
        f"   Payload: {payload}\n"
        f"   Response body: {response.text[:600]}\n"
        f"\n"
        f"   Hipóteses comuns (audit 2026-05-20):\n"
        f"   1. NameError no handler — rode `mypy --strict` no arquivo do handler.\n"
        f"   2. Service method missing — verifique se método existe na class do service.\n"
        f"   3. Pydantic 2.10 regression — Path(..., pattern=...) só funciona em `str`, não em `UUID`.\n"
        f"      Use o type alias `JobIdParam` em `app/shared/types.py`.\n"
        f"   4. Schema mismatch DB ↔ response — verifique `from_attributes=True` no Pydantic model.\n"
        f"\n"
        f"   Repro local:\n"
        f"     curl -X {method} '{url}' -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' -d '{payload}'\n"
    )

    # Sensor adicional: response em 4xx ou 5xx deveria ter envelope canonical
    # (error envelope middleware), não stack trace. Auditt F2.B2 detectou leak.
    if response.status_code >= 400:
        body = response.text.lower()
        assert "traceback" not in body, (
            f"❌ Endpoint {method} {path} vazou stack trace na response (audit F2.B2).\n"
            f"   Adicione handler global em main.py com debug=False.\n"
            f"   Response: {response.text[:600]}"
        )
        assert "/home/runner/" not in body and "/usr/lib/python" not in body, (
            f"❌ Endpoint {method} {path} vazou file path absoluto (info disclosure).\n"
            f"   Response: {response.text[:600]}"
        )
