"""
Canonical Rails HTTP client · W2-010 Phase A (2026-05-22).

Esse módulo é o ÚNICO destino para chamadas HTTP a Rails API. Wraps
`WeDOTalentATSClient` (legacy, em `app/domains/ats_integration/...`) com:

- **Observability** · OTel span por método via `@trace_span` decorator
  (PRIMEIRA instrumentação no path Rails — antes desse W2-010 era zero)
- **Canonical home** · `app/shared/integration/` (não-existia antes)
- **Back-compat** · 3 thin async helpers (`rails_get`, `rails_post`,
  `rails_patch`) preservam a API original de `app/shared/rails_client.py`
  para os 13 callers existentes (lazy imports inside-function → migração
  sem mudança de código nos callers)

Phase A integra:
- W2-009 idempotency-key (já wirado em WeDOTalentATSClient._request)
- W2-012 region pinning (delegado pra LLM providers, não aplicável aqui)
- Observability OTel (novo)

Phase B (deferida) absorverá:
- Refactor WeDOTalentATSClient → mover body pra cá
- Compatibilizar OTT vs Bearer auth com JobCreationAPIClient
- Deletar `app/domains/ats_integration/services/ats_clients/wedotalent_rails.py`
- Deletar `app/shared/rails_client.py` shim (após 1 sprint estável)

NOTA · Audit W2-010 (2026-05-22):
Diagnostic original afirmava "2310 LOC duplicação HTTP". Audit live (3 agents
paralelos em 2026-05-22) revelou:
- `rails_adapter.py` 1100 LOC = MAJORITARIAMENTE business logic (mappers
  Rails↔fork, UUID/bigint discrimination, fallback orchestration). NÃO é HTTP dup.
- `api_client.py` 568 LOC = 280 LOC psycopg2 dev-fallback (Sprint L scar
  tissue). NÃO é HTTP dup. Plus sync httpx + OTT auth ≠ async + Bearer
  (incompatibilidade de modelos auth).
- True HTTP dup = ~160 LOC entre `_request` em WeDOTalentATSClient e
  api_client.JobCreationAPIClient.

Diagnostic over-stated 14× o ROI estrutural. Phase A entrega valor real
(observability + canonical home) sem tentar forçar consolidação que
requer fix de auth model primeiro.
"""
from __future__ import annotations

import logging
from typing import Any

from app.shared.observability.tracing import trace_span

logger = logging.getLogger(__name__)


def _get_underlying_client():
    """Lazy import do WeDOTalentATSClient (evita circular import com domains)."""
    from app.domains.ats_integration.services.ats_clients.wedotalent_rails import (
        WeDOTalentATSClient,
    )

    return WeDOTalentATSClient


# Module-level singleton (lazy-init)
_canonical_instance = None


class RailsClient:
    """
    Canonical Rails API client (W2-010 Phase A).

    Delegates HTTP to `WeDOTalentATSClient` while adding:
    - OTel spans (rails.get, rails.post, rails.put, rails.patch, rails.delete)
    - Canonical home em `app/shared/integration/`
    - W2-009 idempotency · transparente via delegate (já wirado downstream)

    Uso:
        from app.shared.integration.rails_client import RailsClient, rails_client

        # Instância nova com token específico
        client = RailsClient(token="...")
        resp = await client.get("/v1/jobs")

        # Singleton global (env-token default)
        await rails_client.get("/v1/jobs")
    """

    def __init__(self, token: str | None = None, base_url: str | None = None):
        WeDOTalentATSClient = _get_underlying_client()
        self._delegate = WeDOTalentATSClient(token=token, base_url=base_url)

    @trace_span("rails.get", attributes={"client": "canonical"})
    async def get(self, path: str, params: dict | None = None):
        return await self._delegate.get(path, params=params)

    @trace_span("rails.post", attributes={"client": "canonical"})
    async def post(
        self,
        path: str,
        json_body: dict | None = None,
        idempotency_key: str | None = None,
    ):
        # W2-009 idempotency_key passa transparentemente pro delegate
        return await self._delegate.post(
            path, json_body=json_body, idempotency_key=idempotency_key
        )

    @trace_span("rails.put", attributes={"client": "canonical"})
    async def put(
        self,
        path: str,
        json_body: dict | None = None,
        idempotency_key: str | None = None,
    ):
        return await self._delegate.put(
            path, json_body=json_body, idempotency_key=idempotency_key
        )

    @trace_span("rails.patch", attributes={"client": "canonical"})
    async def patch(
        self,
        path: str,
        json_body: dict | None = None,
        idempotency_key: str | None = None,
    ):
        return await self._delegate.patch(
            path, json_body=json_body, idempotency_key=idempotency_key
        )

    @trace_span("rails.delete", attributes={"client": "canonical"})
    async def delete(self, path: str, idempotency_key: str | None = None):
        return await self._delegate.delete(path, idempotency_key=idempotency_key)

    async def close(self):
        await self._delegate.close()


def _get_singleton() -> RailsClient:
    """Lazy module-level singleton (env-token default)."""
    global _canonical_instance
    if _canonical_instance is None:
        _canonical_instance = RailsClient()
    return _canonical_instance


# ─────────────────────────────────────────────────────────────────────────────
# Back-compat thin async helpers (preservam API de app/shared/rails_client.py).
# 13 callers existentes (grep `rails_get|rails_patch|rails_post` em app/) usam
# lazy inside-function imports → migram via shim em rails_client.py sem mudar
# código dos callers.
# ─────────────────────────────────────────────────────────────────────────────


async def rails_get(path: str, params: dict | None = None) -> dict:
    """GET canonical (OTel span wired). Returns response data dict (empty on error)."""
    try:
        resp = await _get_singleton().get(path, params=params)
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] GET %s failed: %s", path, exc)
        return {}


async def rails_patch(path: str, data: dict | None = None) -> dict:
    """PATCH canonical (OTel span wired). Returns response data dict (empty on error)."""
    try:
        resp = await _get_singleton().patch(path, json_body=data or {})
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] PATCH %s failed: %s", path, exc)
        return {}


async def rails_post(path: str, data: dict | None = None) -> dict:
    """POST canonical (OTel span wired). Returns response data dict (empty on error)."""
    try:
        resp = await _get_singleton().post(path, json_body=data or {})
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] POST %s failed: %s", path, exc)
        return {}


__all__ = [
    "RailsClient",
    "rails_get",
    "rails_patch",
    "rails_post",
]
