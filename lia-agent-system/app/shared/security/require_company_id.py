"""
require_company_id — canonical FastAPI dependency that gates every per-tenant
endpoint with an explicit ``company_id`` resolution.

Why this exists
===============
The platform already enforces multi-tenancy at two layers:

1. ``AuthEnforcementMiddleware`` validates the JWT and populates
   ``request.state.company_id`` from the verified claim.
2. ``get_tenant_db`` / Postgres RLS enforces ``SET app.company_id`` on every
   query.

But ~90 endpoints in ``app/api/v1/**`` carried the TODO
``Sprint follow-up: add _require_company_id explicit gate`` — meaning they
relied entirely on those two layers without an *explicit* contract at the
endpoint level. Any future bug that:

- forgot to set ``app.company_id`` on the session, or
- bypassed the middleware via a misconfigured public-path glob, or
- accepted a ``company_id`` in the body without cross-checking the JWT

…would silently exfiltrate cross-tenant data.

This helper closes that gap as Task #1143 (Multi-tenant Ownership — Foundation):

- HTTP 401 when no JWT context is present (middleware did not run / public path).
- HTTP 400 when the resolved ``company_id`` fails ``CompanyId.parse``
  (``""`` / ``"default"`` / ``"none"`` / malformed UUID).
- HTTP 403 (only in ``strict_match=True`` mode) when a payload / path /
  query carries a ``company_id`` that does not match the JWT-resolved one.
- Prometheus counter ``lia_endpoint_require_company_id_total{endpoint,outcome}``
  for every call (outcome ∈ ``ok | missing_jwt | invalid | mismatch | error``).

Usage
=====
Default mode — pure JWT-resolved gate::

    from app.shared.security.require_company_id import require_company_id

    @router.get("/jobs")
    async def list_jobs(
        company_id: str = Depends(require_company_id),
    ):
        ...

Strict-match mode — cross-check against a body / path / query ``company_id``::

    from app.shared.security.require_company_id import require_company_id_strict_match

    @router.post("/transfer")
    async def transfer(
        body: TransferRequest,
        company_id: str = Depends(require_company_id_strict_match("body.company_id")),
    ):
        ...

See also
========
- ``app/middleware/auth_enforcement.py`` — populates ``request.state.company_id``.
- ``app/shared/value_objects/company_id.py`` — canonical parser (T-A).
- ``app/shared/exceptions/tenant_errors.py`` — ``InvalidCompanyIdError``.
- ``.local/tasks/task-1143.md`` — Foundation task spec.
- ``.local/tasks/T-1129-multi-tenant-ownership-plan.md`` — multi-camada plan.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from fastapi import HTTPException, Request, status

from app.shared.exceptions.tenant_errors import InvalidCompanyIdError
from app.shared.value_objects.company_id import CompanyId

logger = logging.getLogger(__name__)

# Prometheus counter — fail-open if prometheus_client is unavailable in tests.
try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter

    _METRIC_NAME = "lia_endpoint_require_company_id_total"
    if _METRIC_NAME in _PROM_REGISTRY._names_to_collectors:  # type: ignore[attr-defined]
        _REQUIRE_COUNTER = _PROM_REGISTRY._names_to_collectors[_METRIC_NAME]  # type: ignore[attr-defined]
    else:
        _REQUIRE_COUNTER = _PromCounter(
            _METRIC_NAME,
            "Outcome of require_company_id endpoint gate.",
            ["endpoint", "outcome"],
        )
except Exception:  # pragma: no cover — fail-open
    _REQUIRE_COUNTER = None


def _emit(endpoint: str, outcome: str) -> None:
    if _REQUIRE_COUNTER is None:
        return
    try:
        _REQUIRE_COUNTER.labels(endpoint=endpoint, outcome=outcome).inc()
    except Exception:  # pragma: no cover
        pass


def _resolve_jwt_company_id(request: Request) -> str:
    """Read company_id from request.state (populated by AuthEnforcementMiddleware).

    Returns the raw string. Empty string means "not authenticated".
    """
    state = getattr(request, "state", None)
    if state is None:
        return ""
    return str(getattr(state, "company_id", "") or "")


def require_company_id(request: Request) -> str:
    """Canonical FastAPI dependency — gates the endpoint on a valid tenant.

    Returns the normalized ``company_id`` string (lower-case UUID v4 or slug).

    Raises:
        HTTPException(401): no JWT-resolved tenant in request.state.
        HTTPException(400): JWT-resolved tenant fails ``CompanyId.parse``.
    """
    endpoint = request.url.path if request.url else "unknown"

    raw = _resolve_jwt_company_id(request)
    if not raw:
        _emit(endpoint, "missing_jwt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: no tenant context.",
        )

    try:
        cid = CompanyId.parse(raw)
    except InvalidCompanyIdError as exc:
        _emit(endpoint, "invalid")
        logger.warning(
            "[require_company_id] invalid JWT company_id raw=%r on %s: %s",
            raw,
            endpoint,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant identifier in token.",
        ) from exc

    _emit(endpoint, "ok")
    return cid.as_str()


def require_company_id_strict_match(
    payload_company_id_getter: Callable[[Request], Any] | str,
) -> Callable[[Request], str]:
    """Factory for a stricter gate: cross-check JWT vs. payload/path/query.

    Args:
        payload_company_id_getter: either a callable ``(Request) -> Any`` that
            returns the candidate ``company_id`` (e.g. from path params /
            cached body), or a dotted accessor string like ``"path.company_id"``
            / ``"query.company_id"`` used for path and query params resolved
            from ``request.path_params`` / ``request.query_params``.

    Returns:
        A FastAPI dependency callable.

    Raises:
        HTTPException(403): when the JWT tenant and payload tenant differ.
        (Plus the 401/400 cases from ``require_company_id``.)
    """

    async def _get(request: Request) -> Any:
        if callable(payload_company_id_getter):
            res = payload_company_id_getter(request)
            # Allow either sync or async callables.
            if hasattr(res, "__await__"):
                res = await res
            return res
        accessor = str(payload_company_id_getter)
        if accessor.startswith("path."):
            key = accessor[len("path."):]
            return (request.path_params or {}).get(key)
        if accessor.startswith("query."):
            key = accessor[len("query."):]
            return (request.query_params or {}).get(key)
        if accessor.startswith("form."):
            key = accessor[len("form."):]
            try:
                form = await request.form()
            except Exception:
                return None
            return form.get(key)
        if accessor.startswith("body."):
            key = accessor[len("body."):]
            try:
                body = await request.json()
            except Exception:
                return None
            if isinstance(body, dict):
                return body.get(key)
            return None
        return None

    async def _dep(request: Request) -> str:
        jwt_company = require_company_id(request)
        endpoint = request.url.path if request.url else "unknown"

        candidate = await _get(request)
        if candidate in (None, ""):
            # Nothing to cross-check — JWT wins.
            return jwt_company

        try:
            parsed = CompanyId.parse(candidate).as_str()
        except InvalidCompanyIdError as exc:
            _emit(endpoint, "invalid")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant identifier in payload.",
            ) from exc

        if parsed != jwt_company:
            # Architectural drift tolerance 2026-05-24: the platform has TWO
            # tenancy entities — ``client_accounts`` (billing/auth, what JWT
            # carries) and ``company_profiles`` (HR/recruiting child). Many
            # endpoints receive the company_profile.id in the payload while
            # the JWT carries the parent client_account.id. Strict literal
            # comparison would reject every such request as cross-tenant.
            #
            # Safe fuzzy match: if ``parsed`` is a company_profiles row whose
            # ``client_account_id == jwt_company``, the payload references the
            # same logical tenant — accept. Otherwise reject as before.
            try:
                from app.core.database import get_db
                from app.domains.company.repositories.company_profile_repository import (
                    CompanyProfileRepository,
                )

                async for db in get_db():
                    repo = CompanyProfileRepository(db)
                    if await repo.belongs_to_client_account(parsed, jwt_company):
                        logger.info(
                            "[require_company_id_strict_match] resolved "
                            "company_profile_id=%s to client_account_id=%s "
                            "(endpoint=%s) — payload uses company_profile.id "
                            "while JWT carries parent client_account.id; "
                            "auto-resolved via FK lookup.",
                            parsed,
                            jwt_company,
                            endpoint,
                        )
                        _emit(endpoint, "ok")
                        return jwt_company
                    break
            except Exception as resolve_err:  # pragma: no cover
                logger.warning(
                    "[require_company_id_strict_match] FK lookup failed "
                    "jwt=%s payload=%s endpoint=%s err=%s",
                    jwt_company,
                    parsed,
                    endpoint,
                    resolve_err,
                )

            _emit(endpoint, "mismatch")
            logger.warning(
                "[require_company_id_strict_match] CROSS-TENANT ATTEMPT "
                "jwt=%s payload=%s endpoint=%s",
                jwt_company,
                parsed,
                endpoint,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant mismatch between token and payload.",
            )

        return jwt_company

    return _dep


__all__ = [
    "require_company_id",
    "require_company_id_strict_match",
]
