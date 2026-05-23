"""
Canonical Rails HTTP client · W2-010 Phase A + Phase B autonomous (2026-05-23).

Esse módulo é o ÚNICO destino para chamadas HTTP a Rails API. Contém:

1. **WeDOTalentATSClient** (autonomous, 598+ LOC) — full implementation
   movida em W2-010-B (2026-05-23) de `app/domains/ats_integration/services/
   ats_clients/wedotalent_rails.py` (DELETED). Retry+backoff+circuit breaker+
   JSONAPI parsing+401 handling+idempotency-key (W2-009) já wirados.

2. **RailsClient** (Phase A thin wrapper) — wrappa WeDOTalentATSClient com
   OTel `@trace_span` decorator pra observability canonical (PRIMEIRA
   instrumentação no path Rails). Para novo código preferir esta classe.

3. **3 thin async helpers** (`rails_get`, `rails_post`, `rails_patch`) —
   preservam API original de `app/shared/rails_client.py` (13 callers
   in-tree via lazy import).

W2-010-B (2026-05-23) — Phase B autonomous:
- Body de WeDOTalentATSClient movido pra cá (era em domains/ats_integration/)
- 1 caller atualizado (rails_adapter.py:382 → import from canonical home)
- Legacy file deletado (zero residue)

W2-009 (2026-05-22) idempotency · transparente via delegate (já wirado).
W2-008 (2026-05-22) Anthropic caching · não aplicável (HTTP, não LLM).
W2-012 (2026-05-22) LGPD region pinning · delegado pra LLM providers.

Audit W2-010 (2026-05-22, 3 parallel agents):
- Diagnostic over-stated 14× (true HTTP dup ~160 LOC, não 2310)
- rails_adapter.py 1100 LOC = business logic (mappers), NÃO HTTP dup
- api_client.py 568 LOC = psycopg2 dev-fallback + OTT auth (incompat)
- Phase B realista: mover apenas WeDOTalentATSClient (598 LOC) pra canonical

JobCreationAPIClient permanece separado (OTT auth pattern diferente).
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import httpx
import uuid

from app.domains.ats_integration.services.ats_clients.base import (
    ATSCandidate,
    ATSJob,
)

logger = logging.getLogger(__name__)

RAILS_API_URL = os.environ.get("RAILS_API_URL", "http://localhost:3000")
RAILS_API_TIMEOUT = int(os.environ.get("RAILS_API_TIMEOUT", "30"))
RAILS_API_TOKEN = os.environ.get("RAILS_API_TOKEN", "")

_RETRY_BASE_DELAY = 0.5
_RETRY_MAX_DELAY = 8.0


@dataclass
class RailsAPIResponse:
    """Parsed JSONAPI response from Rails."""
    data: Any = None
    meta: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    status_code: int = 0
    success: bool = False


class WeDOTalentATSClient:
    """HTTP client for WeDOTalent ats_api (Rails).

    Implements retry with exponential backoff, auto-refresh on 401,
    JSONAPI response parsing, and circuit breaker integration.

    Auth precedence:
      1. ``token`` argument (user JWT forwarded from request)
      2. ``RAILS_API_TOKEN`` env var (service-to-service token)

    Usage:
        client = WeDOTalentATSClient(token="eyJ...")
        jobs = await client.list_jobs(search="developer", page=1, limit=20)
        candidate = await client.get_candidate(candidate_id=5)
    """

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: int = RAILS_API_TIMEOUT,
    ):
        self.base_url = (base_url or RAILS_API_URL).rstrip("/")
        self.token = token or RAILS_API_TOKEN or None
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Low-level HTTP (retry + backoff + circuit breaker)
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: dict | None = None,
        retry: int = 3,
        idempotency_key: str | None = None,
    ) -> RailsAPIResponse:
        """Make HTTP request with retry, exponential backoff, and JSONAPI parsing."""
        from app.shared.resilience.circuit_breaker import RAILS_CIRCUIT, CircuitBreakerError

        async def _do_request() -> RailsAPIResponse:
            """
            Inner retry loop. Raises on retryable failure (timeout / 5xx) so the
            outer circuit-breaker wrapper can track the failure correctly.
            Non-retryable responses (401, 4xx client errors) are returned as
            RailsAPIResponse with success=False — they do NOT open the circuit.
            """
            client = await self._get_client()
            last_error: Exception | None = None

            # W2-009 (2026-05-22): Idempotency-Key em mutations Rails.
            # Mesmo key persiste entre retries → Rails-side cache dedup
            # (ver: REPLIT_LIA_REMEDIATION_BACKLOG W2-009).
            mutation_method = method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
            request_headers: dict[str, str] = {}
            if mutation_method:
                request_headers["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())

            for attempt in range(retry):
                try:
                    response = await client.request(
                        method=method,
                        url=path,
                        params=params,
                        json=json_body,
                        headers=request_headers or None,
                    )

                    # 401 — auth problem: non-retryable, not a Rails service fault
                    if response.status_code == 401:
                        logger.warning("[RailsClient] 401 Unauthorized on %s %s", method, path)
                        return RailsAPIResponse(
                            status_code=401,
                            errors=["Unauthorized"],
                        )

                    # 5xx — server fault: retryable, counts against circuit
                    if response.status_code >= 500:
                        body = response.json() if response.content else {}
                        errors = body.get("errors", [str(response.status_code)])
                        exc = httpx.HTTPStatusError(
                            f"Rails server error {response.status_code}",
                            request=response.request,
                            response=response,
                        )
                        last_error = exc
                        delay = min(_RETRY_BASE_DELAY * (2 ** attempt), _RETRY_MAX_DELAY)
                        logger.warning(
                            "[RailsClient] 5xx (%s) on %s %s (attempt %d/%d) — retrying in %.1fs",
                            response.status_code, method, path, attempt + 1, retry, delay,
                        )
                        if attempt < retry - 1:
                            await asyncio.sleep(delay)
                        continue

                    # 4xx client error — non-retryable, not a Rails service fault
                    if response.status_code >= 400:
                        body = response.json() if response.content else {}
                        return RailsAPIResponse(
                            status_code=response.status_code,
                            errors=body.get("errors", [str(response.status_code)]),
                        )

                    # 2xx / 3xx — success
                    body = response.json() if response.content else {}
                    return RailsAPIResponse(
                        data=body.get("data"),
                        meta=body.get("meta", {}),
                        status_code=response.status_code,
                        success=True,
                    )

                except httpx.TimeoutException as e:
                    last_error = e
                    delay = min(_RETRY_BASE_DELAY * (2 ** attempt), _RETRY_MAX_DELAY)
                    logger.warning(
                        "[RailsClient] Timeout on %s %s (attempt %d/%d) — retrying in %.1fs",
                        method, path, attempt + 1, retry, delay,
                    )
                    if attempt < retry - 1:
                        await asyncio.sleep(delay)

                except Exception as e:
                    # Unexpected error (connection refused, DNS, etc.) — raise immediately
                    logger.error("[RailsClient] Error on %s %s: %s", method, path, e)
                    raise

            # All retry attempts exhausted — raise so circuit breaker records failure
            raise RuntimeError(
                f"[RailsClient] All {retry} attempts failed for {method} {path}: {last_error}"
            )

        try:
            return await RAILS_CIRCUIT.call(_do_request)
        except CircuitBreakerError as e:
            logger.warning("[RailsClient] Circuit OPEN for rails_api: retry_after=%.0fs", e.retry_after)
            return RailsAPIResponse(
                errors=[f"Rails API unavailable (circuit open, retry after {e.retry_after:.0f}s)"],
                status_code=503,
            )
        except Exception as e:
            # Circuit recorded failure; return safe error response
            logger.warning("[RailsClient] Rails call failed (recorded in circuit): %s", e)
            return RailsAPIResponse(
                errors=[str(e)],
                status_code=0,
            )

    async def get(self, path: str, params: dict | None = None) -> RailsAPIResponse:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json_body: dict | None = None, idempotency_key: str | None = None) -> RailsAPIResponse:
        return await self._request("POST", path, json_body=json_body, idempotency_key=idempotency_key)

    async def put(self, path: str, json_body: dict | None = None, idempotency_key: str | None = None) -> RailsAPIResponse:
        return await self._request("PUT", path, json_body=json_body, idempotency_key=idempotency_key)

    async def delete(self, path: str, idempotency_key: str | None = None) -> RailsAPIResponse:
        return await self._request("DELETE", path, idempotency_key=idempotency_key)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def login(self, email: str, password: str) -> str | None:
        """Authenticate and get JWT token from Rails."""
        resp = await self.post("/v1/sessions", json_body={
            "email": email,
            "password": password,
        })
        if resp.success and isinstance(resp.data, dict):
            token = resp.data.get("token")
            if token:
                self.token = token
                self._client = None
                return token
        return None

    async def get_current_user(self) -> dict | None:
        """Get authenticated user info (/v1/me)."""
        resp = await self.get("/v1/me")
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------

    async def list_jobs(
        self, search: str = "*", page: int = 1, limit: int = 30, **filters
    ) -> list[dict]:
        params = {"search": search, "page": page, "limit": limit}
        if filters:
            import json
            params["where"] = json.dumps(filters)
        resp = await self.get("/v1/users/jobs", params=params)
        return self._extract_list(resp)

    async def list_jobs_or_none(
        self, search: str = "*", page: int = 1, limit: int = 30, **filters
    ) -> list[dict] | None:
        """Like list_jobs but returns None on any Rails failure (non-success response).

        This distinguishes a successful empty list [] from a Rails error,
        allowing callers to fall back to a local data source on failure.
        """
        params = {"search": search, "page": page, "limit": limit}
        if filters:
            import json
            params["where"] = json.dumps(filters)
        resp = await self.get("/v1/users/jobs", params=params)
        if not resp.success:
            return None
        return self._extract_list(resp)

    async def get_job(self, job_id: int) -> dict | None:
        resp = await self.get(f"/v1/users/jobs/{job_id}")
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    # ------------------------------------------------------------------
    # Candidates
    # ------------------------------------------------------------------

    async def list_candidates(
        self, search: str = "*", page: int = 1, limit: int = 30, **filters
    ) -> list[dict]:
        params = {"search": search, "page": page, "limit": limit}
        if filters:
            import json
            params["where"] = json.dumps(filters)
        resp = await self.get("/v1/users/candidates", params=params)
        return self._extract_list(resp)

    async def list_candidates_or_none(
        self, search: str = "*", page: int = 1, limit: int = 30, **filters
    ) -> list[dict] | None:
        """Like list_candidates but returns None on any Rails failure (non-success response).

        This distinguishes a successful empty list [] from a Rails error,
        allowing callers to fall back to a local data source on failure.
        """
        params = {"search": search, "page": page, "limit": limit}
        if filters:
            import json
            params["where"] = json.dumps(filters)
        resp = await self.get("/v1/users/candidates", params=params)
        if not resp.success:
            return None
        return self._extract_list(resp)

    async def get_candidate(self, candidate_id: int) -> dict | None:
        resp = await self.get(f"/v1/users/candidates/{candidate_id}")
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    # ------------------------------------------------------------------
    # Applies (Applications)
    # ------------------------------------------------------------------

    async def list_applies(
        self, search: str = "*", page: int = 1, limit: int = 30, **filters
    ) -> list[dict]:
        params = {"search": search, "page": page, "limit": limit}
        if filters:
            import json
            params["where"] = json.dumps(filters)
        resp = await self.get("/v1/users/applies", params=params)
        return self._extract_list(resp)

    async def get_apply(self, apply_id: int) -> dict | None:
        resp = await self.get(f"/v1/users/applies/{apply_id}")
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    async def create_apply(self, candidate_id: int, job_id: int) -> dict | None:
        resp = await self.post("/v1/users/applies", json_body={
            "candidate_id": candidate_id,
            "job_id": job_id,
        })
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    # ------------------------------------------------------------------
    # Selective Processes
    # ------------------------------------------------------------------

    async def list_selective_processes(
        self, job_id: int | None = None, **filters
    ) -> list[dict]:
        params: dict[str, Any] = {"search": "*"}
        if job_id:
            import json
            params["where"] = json.dumps({"job_id": job_id})
        resp = await self.get("/v1/users/selective_processes", params=params)
        return self._extract_list(resp)

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def list_messages(
        self,
        page: int = 1,
        limit: int = 30,
        reference_type: str | None = None,
        reference_id: int | None = None,
    ) -> list[dict]:
        """List messages from Rails (/v1/users/messages)."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if reference_type:
            params["reference_type"] = reference_type
        if reference_id:
            params["reference_id"] = reference_id
        resp = await self.get("/v1/users/messages", params=params)
        return self._extract_list(resp)

    async def send_message(
        self,
        content: str,
        entity: str | None = None,
        reference_type: str | None = None,
        reference_id: int | None = None,
        parent_message_id: int | None = None,
        metadata: dict | None = None,
    ) -> dict | None:
        """Send a message via Rails (/v1/users/messages)."""
        payload: dict[str, Any] = {"content": content}
        if entity:
            payload["entity"] = entity
        if reference_type:
            payload["reference_type"] = reference_type
        if reference_id:
            payload["reference_id"] = reference_id
        if parent_message_id:
            payload["parent_message_id"] = parent_message_id
        if metadata:
            payload["metadata"] = metadata
        resp = await self.post("/v1/users/messages", json_body={"message": payload})
        if resp.success:
            return self._extract_attributes(resp.data)
        logger.warning("[RailsClient] send_message failed: %s", resp.errors)
        return None

    # ------------------------------------------------------------------
    # Write Operations
    # ------------------------------------------------------------------

    async def create_candidate(self, candidate_data: dict) -> dict | None:
        """Create a candidate in Rails."""
        resp = await self.post("/v1/users/candidates", json_body={"candidate": candidate_data})
        if resp.success:
            return self._extract_attributes(resp.data)
        logger.warning("[RailsClient] create_candidate failed: %s", resp.errors)
        return None

    async def update_candidate(self, candidate_id: int, candidate_data: dict) -> dict | None:
        """Update a candidate in Rails."""
        resp = await self.put(f"/v1/users/candidates/{candidate_id}", json_body={"candidate": candidate_data})
        if resp.success:
            return self._extract_attributes(resp.data)
        logger.warning("[RailsClient] update_candidate %s failed: %s", candidate_id, resp.errors)
        return None

    async def delete_candidate(self, candidate_id: int) -> bool:
        """Delete a candidate in Rails."""
        resp = await self.delete(f"/v1/users/candidates/{candidate_id}")
        return resp.success

    async def create_job(self, job_data: dict) -> dict | None:
        """Create a job in Rails."""
        resp = await self.post("/v1/users/jobs", json_body={"job": job_data})
        if resp.success:
            return self._extract_attributes(resp.data)
        logger.warning("[RailsClient] create_job failed: %s", resp.errors)
        return None

    async def update_job(self, job_id: int, job_data: dict) -> dict | None:
        """Update a job in Rails."""
        resp = await self.put(f"/v1/users/jobs/{job_id}", json_body={"job": job_data})
        if resp.success:
            return self._extract_attributes(resp.data)
        logger.warning("[RailsClient] update_job %s failed: %s", job_id, resp.errors)
        return None

    async def delete_job(self, job_id: int) -> bool:
        """Delete a job in Rails."""
        resp = await self.delete(f"/v1/users/jobs/{job_id}")
        return resp.success

    async def update_apply(self, apply_id: int, apply_data: dict) -> dict | None:
        """Update an apply in Rails."""
        resp = await self.put(f"/v1/users/applies/{apply_id}", json_body={"apply": apply_data})
        if resp.success:
            return self._extract_attributes(resp.data)
        logger.warning("[RailsClient] update_apply %s failed: %s", apply_id, resp.errors)
        return None

    async def delete_apply(self, apply_id: int) -> bool:
        """Delete (cancel) an apply in Rails."""
        resp = await self.delete(f"/v1/users/applies/{apply_id}")
        return resp.success

    # ------------------------------------------------------------------
    # New Resources
    # ------------------------------------------------------------------

    async def list_interviews(self, **filters) -> list[dict]:
        params = {"search": "*"}
        if filters:
            import json
            params["where"] = json.dumps(filters)
        resp = await self.get("/v1/users/interviews", params=params)
        return self._extract_list(resp)

    async def list_notifications(self, **filters) -> list[dict]:
        resp = await self.get("/v1/users/notifications")
        return self._extract_list(resp)

    async def list_email_templates(self, **filters) -> list[dict]:
        resp = await self.get("/v1/users/email_templates")
        return self._extract_list(resp)

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    async def health_check(self) -> dict:
        """Probe Rails API availability. Returns status dict."""
        import time
        start = time.monotonic()
        try:
            resp = await self.get("/v1/me")
            latency_ms = int((time.monotonic() - start) * 1000)
            if resp.success or resp.status_code in (200, 401):
                return {
                    "status": "ok",
                    "latency_ms": latency_ms,
                    "rails_reachable": True,
                    "status_code": resp.status_code,
                }
            return {
                "status": "degraded",
                "latency_ms": latency_ms,
                "rails_reachable": True,
                "status_code": resp.status_code,
                "errors": resp.errors,
            }
        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "status": "unreachable",
                "latency_ms": latency_ms,
                "rails_reachable": False,
                "error": str(e),
            }

    # ------------------------------------------------------------------
    # JSONAPI Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_attributes(data: Any) -> dict | None:
        """Extract attributes from JSONAPI data object."""
        if isinstance(data, dict):
            attrs = data.get("attributes", {})
            attrs["id"] = data.get("id")
            attrs["type"] = data.get("type")
            return attrs
        return None

    @staticmethod
    def _extract_list(resp: RailsAPIResponse) -> list[dict]:
        """Extract list of attributes from JSONAPI data array."""
        if not resp.success or not isinstance(resp.data, list):
            return []
        results = []
        for item in resp.data:
            if isinstance(item, dict):
                attrs = item.get("attributes", {})
                attrs["id"] = item.get("id")
                attrs["type"] = item.get("type")
                results.append(attrs)
        return results

    def to_ats_candidate(self, data: dict) -> ATSCandidate:
        """Convert Rails candidate data to normalized ATSCandidate."""
        return ATSCandidate(
            ats_id=str(data.get("id", "")),
            name=f"{data.get('name', '')} {data.get('surname', '')}".strip(),
            email=data.get("email", ""),
            phone=data.get("mobile_phone") or data.get("phone"),
            linkedin_url=data.get("linkedin"),
            location=f"{data.get('city', '')}, {data.get('state', '')}".strip(", "),
            notes=data.get("comments"),
            raw_data=data,
        )

    def to_ats_job(self, data: dict) -> ATSJob:
        """Convert Rails job data to normalized ATSJob."""
        return ATSJob(
            ats_id=str(data.get("id", "")),
            title=data.get("title", ""),
            description=data.get("description"),
            location=f"{data.get('city', '')}, {data.get('state', '')}".strip(", "),
            status="remote" if data.get("is_remote") else data.get("workplace_type", ""),
            raw_data=data,
        )



# ─────────────────────────────────────────────────────────────────────────────
# Phase A · RailsClient thin wrapper + 3 helpers (W2-010 commit 4a3339701)
# ─────────────────────────────────────────────────────────────────────────────

from app.shared.observability.tracing import trace_span  # noqa: E402


_canonical_instance: "RailsClient | None" = None


class RailsClient:
    """Phase A canonical wrapper · OTel observability layer sobre WeDOTalentATSClient.

    Para novo código preferir esta classe (5 spans `rails.<method>` automáticos).
    Para código legado/business-logic preferir `WeDOTalentATSClient` direto
    (mais control sobre business methods como `list_jobs`, `create_candidate`).
    """

    def __init__(self, token: str | None = None, base_url: str | None = None):
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
        # WeDOTalentATSClient não tem método patch público; usa _request direto
        return await self._delegate._request(
            "PATCH", path, json_body=json_body, idempotency_key=idempotency_key
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
# 13 callers in-tree usam lazy inside-function imports → migram via shim.
# ─────────────────────────────────────────────────────────────────────────────


async def rails_get(path: str, params: dict | None = None) -> dict:
    """GET canonical (OTel span). Returns response data dict (empty on error)."""
    try:
        resp = await _get_singleton().get(path, params=params)
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] GET %s failed: %s", path, exc)
        return {}


async def rails_patch(path: str, data: dict | None = None) -> dict:
    """PATCH canonical (OTel span). Returns response data dict (empty on error)."""
    try:
        resp = await _get_singleton().patch(path, json_body=data or {})
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] PATCH %s failed: %s", path, exc)
        return {}


async def rails_post(path: str, data: dict | None = None) -> dict:
    """POST canonical (OTel span). Returns response data dict (empty on error)."""
    try:
        resp = await _get_singleton().post(path, json_body=data or {})
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] POST %s failed: %s", path, exc)
        return {}


__all__ = [
    "WeDOTalentATSClient",
    "RailsClient",
    "RailsAPIResponse",
    "rails_get",
    "rails_patch",
    "rails_post",
]
