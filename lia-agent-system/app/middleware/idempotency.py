"""W2-009-B · Idempotency Middleware (Stripe-style) para FastAPI.

Intercepta mutations (POST/PUT/PATCH/DELETE) com header `Idempotency-Key`.
Cache em DB table `idempotency_keys` (migration 181_idempotency_keys).

Comportamento canonical:
1. **Header ausente** → passthrough normal (back-compat 100%, todas 913 endpoints
   continuam funcionando sem opt-in).
2. **Header presente, primeira execução** → request executa, response cacheada,
   próximos replays retornam cache.
3. **Header presente, replay com mesmo body** → cached response retornada
   (NÃO reexecuta side effects).
4. **Header presente, replay com body DIFERENTE** → 409 Conflict (Stripe behavior:
   key reuse abuse).

Multi-tenancy: PK composta (idempotency_key, company_id). Isola fail-closed.
Sem company_id (anon/pre-auth) → passthrough sem cache (não há como segregar).

Stub-only para endpoints GET/HEAD/OPTIONS (HTTP semantics já idempotentes).

TTL: 24h via job cleanup periódico (out of scope deste commit).
"""
from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
IDEMPOTENCY_HEADER = "Idempotency-Key"
MAX_KEY_LENGTH = 255
MAX_BODY_BYTES = 5 * 1024 * 1024  # 5 MB hard cap pra cache (segurança)


def _hash_request(body: bytes) -> str:
    """SHA-256 do body para detectar replay com payload diferente."""
    return hashlib.sha256(body).hexdigest()


def _is_idempotency_enabled() -> bool:
    """Feature flag para desativar middleware em emergency (ex: DB down)."""
    return os.environ.get("IDEMPOTENCY_MIDDLEWARE_ENABLED", "true").lower() == "true"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware Stripe-style para Idempotency-Key cache."""

    async def dispatch(self, request: Request, call_next):
        # Skip por método (GET/HEAD/OPTIONS são idempotentes by HTTP semantics)
        if request.method not in MUTATION_METHODS:
            return await call_next(request)

        # Skip se feature flag off
        if not _is_idempotency_enabled():
            return await call_next(request)

        # Skip se header ausente (back-compat opt-in)
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            return await call_next(request)

        # Validate key length
        if len(idempotency_key) > MAX_KEY_LENGTH:
            from starlette.responses import JSONResponse
            return JSONResponse(
                {"error": True, "message": f"Idempotency-Key exceeds {MAX_KEY_LENGTH} chars"},
                status_code=400,
            )

        # Skip se sem company_id (anon/pre-auth — sem como isolar por tenant)
        company_id = getattr(request.state, "company_id", None)
        if not company_id:
            return await call_next(request)

        # Read body for hashing — must NOT exhaust stream for downstream handler
        body_bytes = await request.body()
        if len(body_bytes) > MAX_BODY_BYTES:
            return await call_next(request)  # body too large, skip cache

        request_hash = _hash_request(body_bytes)

        # Re-inject body so downstream handlers can read it
        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request._receive = receive

        # Check cache
        try:
            cached = await self._get_cached(
                request, idempotency_key, company_id, request.method, request.url.path
            )
        except Exception as e:
            # DB error — fail open (passthrough) to not break entire API
            logger.error(
                "IdempotencyMiddleware cache read failed, passthrough: %s", e,
                exc_info=True,
            )
            return await call_next(request)

        if cached:
            stored_hash, status, body = cached
            if stored_hash != request_hash:
                # Stripe behavior: same key, different body = conflict
                from starlette.responses import JSONResponse
                logger.warning(
                    "IdempotencyMiddleware conflict: key=%s company=%s "
                    "stored_hash=%s != request_hash=%s",
                    idempotency_key, company_id, stored_hash, request_hash,
                )
                return JSONResponse(
                    {
                        "error": True,
                        "message": (
                            "Idempotency-Key already used with different request body. "
                            "Reuse the same Idempotency-Key only for retries of the EXACT same request."
                        ),
                    },
                    status_code=409,
                )
            # Replay hit — return cached response
            logger.info(
                "IdempotencyMiddleware replay hit: key=%s company=%s status=%d",
                idempotency_key, company_id, status,
            )
            return Response(
                content=body,
                status_code=status,
                media_type="application/json",
                headers={"X-Idempotent-Replay": "true"},
            )

        # Cache miss — execute request, capture response
        response = await call_next(request)

        # Only cache successful + client-error responses (2xx, 4xx — not 5xx)
        # 5xx = server bug, retry is reasonable (don't cache failure)
        if not (200 <= response.status_code < 500):
            return response

        # Capture body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Store
        try:
            await self._store_cache(
                request,
                idempotency_key,
                company_id,
                request.method,
                request.url.path,
                request_hash,
                response.status_code,
                response_body,
            )
        except IntegrityError:
            # Race: another request inserted same key concurrently — that's fine
            logger.info(
                "IdempotencyMiddleware race insert ignored: key=%s company=%s",
                idempotency_key, company_id,
            )
        except Exception as e:
            # DB error on insert — log but return response anyway (fail open)
            logger.error(
                "IdempotencyMiddleware cache write failed: %s", e, exc_info=True,
            )

        # Re-emit response with captured body
        return Response(
            content=response_body,
            status_code=response.status_code,
            media_type=response.media_type,
            headers=dict(response.headers),
        )

    async def _get_cached(
        self,
        request: Request,
        idempotency_key: str,
        company_id: str,
        method: str,
        path: str,
    ) -> tuple[str, int, bytes] | None:
        """Lookup cache entry. Returns (request_hash, status, body) or None."""
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT request_hash, response_status, response_body "
                    "FROM idempotency_keys "
                    "WHERE idempotency_key = :key AND company_id = :cid "
                    "AND method = :method AND path = :path "
                    "AND created_at > now() - interval '24 hours'"
                ),
                {"key": idempotency_key, "cid": company_id, "method": method, "path": path},
            )
            row = result.first()
            if row is None:
                return None
            return (row[0], row[1], bytes(row[2]))

    async def _store_cache(
        self,
        request: Request,
        idempotency_key: str,
        company_id: str,
        method: str,
        path: str,
        request_hash: str,
        response_status: int,
        response_body: bytes,
    ) -> None:
        """Persist cache entry."""
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            await session.execute(
                text(
                    "INSERT INTO idempotency_keys "
                    "(idempotency_key, company_id, method, path, request_hash, "
                    "response_status, response_body, created_at) "
                    "VALUES (:key, :cid, :method, :path, :hash, :status, :body, :ts) "
                    "ON CONFLICT (idempotency_key, company_id) DO NOTHING"
                ),
                {
                    "key": idempotency_key,
                    "cid": company_id,
                    "method": method,
                    "path": path,
                    "hash": request_hash,
                    "status": response_status,
                    "body": response_body,
                    "ts": datetime.now(timezone.utc),
                },
            )
            await session.commit()
