"""
AuditAccessMiddleware — LGPD Art. 37 V (registro de operações de tratamento).

Sprint 3 RBAC (2026-05-25, plan canonical: ~/.claude/plans/jolly-roaming-moler.md).

Função: registrar automaticamente em SOXAuditLog (action_category=DATA_ACCESS)
toda requisição GET em endpoints de PII crítica (candidate, job, audit log).

Por que middleware vs decorator por endpoint:
- 1 file edit vs N edits = menos risco de quebrar LIA chat
- Logging centralizado e auditável
- Fire-and-forget asyncio — zero impacto em latência
- Falha de log NUNCA propaga (não bloqueia request principal)

Compliance: LGPD Art. 37 V "registro das operações de tratamento de dados pessoais".
Retention: 7 anos (SOX 802 — herdado de SOXAuditLog default).

Observability: count exposto via /api/v1/observability/data-access (já existente).
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Patterns de paths PII críticas. Match contra request.url.path.
# Cada tupla: (regex, resource_type, capture_group_index_for_id).
PII_PATTERNS: list[tuple[re.Pattern[str], str, int]] = [
    # GET /api/v1/candidates/{candidate_id}
    (re.compile(r"^/api/v1/candidates/([a-fA-F0-9-]{36}|[0-9]+)/?$"), "candidate", 1),
    # GET /api/v1/job-vacancies/{job_vacancy_id} (inclui confidenciais)
    (re.compile(r"^/api/v1/job-vacancies/([a-fA-F0-9-]{36}|[0-9]+)/?$"), "job_vacancy", 1),
    # GET /api/v1/audit-logs/{log_id}
    (re.compile(r"^/api/v1/audit-logs/([a-fA-F0-9-]{36})/?$"), "audit_log", 1),
]


class AuditAccessMiddleware(BaseHTTPMiddleware):
    """LGPD Art. 37 V data-access audit logger."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        # Only log successful GET requests on PII patterns.
        # Failures (4xx/5xx) are noise — successful access is what LGPD audits.
        if request.method != "GET":
            return response
        if response.status_code >= 400:
            return response

        match_data = self._match_pii_path(request.url.path)
        if match_data is None:
            return response

        resource_type, resource_id = match_data

        # Fire-and-forget — never block response.
        # Audit log failure must NOT propagate to user.
        try:
            asyncio.create_task(self._log_access(request, resource_type, resource_id))
        except Exception as exc:
            logger.debug("[AuditAccessMiddleware] schedule failed: %s", exc)

        return response

    @staticmethod
    def _match_pii_path(path: str) -> tuple[str, str] | None:
        for pattern, resource_type, group_idx in PII_PATTERNS:
            m = pattern.match(path)
            if m:
                return resource_type, m.group(group_idx)
        return None

    @staticmethod
    async def _log_access(request: Request, resource_type: str, resource_id: str) -> None:
        try:
            # Lazy import to avoid circular dependency at module load
            from app.shared.compliance.audit_service import audit_service

            # company_id from ContextVar (canonical multi-tenancy 2026-05-21)
            company_id: str | None = None
            user_id: str | None = None
            user_email: str | None = None

            # Extract from request.state (populated by auth_enforcement middleware).
            # Canonical state fields per auth_enforcement.py:407-414:
            #   request.state.user_id, request.state.company_id, request.state.user_role,
            #   request.state.token_payload (JWT claims dict).
            # user_email não é state direto — extrair do payload se disponível.
            company_id = getattr(request.state, "company_id", None)
            user_id = getattr(request.state, "user_id", None)
            token_payload = getattr(request.state, "token_payload", {}) or {}
            user_email = token_payload.get("email") or token_payload.get("sub")

            # If auth_enforcement ran before us, these should be populated.
            # If missing, skip log silently (anonymous request shouldn't reach PII anyway).
            if not company_id:
                return

            # Extract client info
            ip_address: str | None = None
            try:
                if request.client:
                    ip_address = request.client.host
            except Exception:
                pass

            user_agent = request.headers.get("user-agent")
            request_id = getattr(request.state, "request_id", None)

            await audit_service.log_data_access(
                company_id=str(company_id),
                user_id=str(user_id) if user_id else None,
                user_email=user_email,
                resource_type=resource_type,
                resource_id=resource_id,
                action="view",
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                details={"path": request.url.path},
            )
        except Exception as exc:
            # Never propagate — audit failure must not impact UX or compliance flow.
            logger.debug(
                "[AuditAccessMiddleware] log_access failed (non-blocking): %s", exc
            )
