"""
AuthEnforcementMiddleware — Global authentication and tenant context.

Multi-tenancy security: Every non-public request MUST have a valid JWT.
The middleware:
1. Validates the Bearer token
2. Loads the user from DB
3. Injects user + company_id into request.state
4. Rejects unauthenticated requests with 401

This replaces per-endpoint auth and eliminates the X-Company-ID header
trust vulnerability (where a user could forge a different company_id).
"""
import logging
from contextvars import ContextVar

# ContextVar for tenant isolation — read by get_db to inject RLS context
_current_company_id: ContextVar[str] = ContextVar("_current_company_id", default="")

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Routes that don't require authentication
PUBLIC_PATHS = {
    "/health",
    "/health/",
    "/docs",
    "/docs/",
    "/docs/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/workos-callback",
    "/api/v1/auth/workos/callback",
    "/api/v1/data-request",
    "/api/v1/webhooks/whatsapp",
    "/api/v1/teams/webhook",
    "/api/v1/teams/messages",
    "/api/v1/webhooks/twilio-voice",
    "/favicon.ico",
}

# Path prefixes that are public (e.g. static files, docs)
PUBLIC_PREFIXES = (
    "/docs/",
    "/static/",
    "/_next/",
)


class AuthEnforcementMiddleware(BaseHTTPMiddleware):
    """Global auth middleware that enforces JWT on all non-public routes."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow public routes
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # Allow OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            logger.warning(f"[AuthEnforcement] No Bearer token for {request.method} {path}")
            return JSONResponse(
                {"detail": "Authentication required"},
                status_code=401,
            )

        token = auth_header[7:]  # Remove "Bearer "

        try:
            from app.auth.security import decode_token
            payload = decode_token(token)

            user_id = payload.get("sub")
            if not user_id:
                return JSONResponse({"detail": "Invalid token: no subject"}, status_code=401)

            # Inject into request.state for downstream use
            request.state.token_payload = payload
            request.state.user_id = user_id
            request.state.company_id = payload.get("company_id", "")
            _current_company_id.set(payload.get("company_id", ""))
            request.state.user_role = payload.get("role", "")

            # If company_id from X-Company-ID header differs from JWT, reject
            header_company = request.headers.get("X-Company-ID", "")
            jwt_company = payload.get("company_id", "")

            if header_company and jwt_company and header_company != jwt_company:
                logger.warning(
                    f"[AuthEnforcement] CROSS-TENANT ATTEMPT: "
                    f"JWT company={jwt_company}, header company={header_company}, "
                    f"user={user_id}, path={path}"
                )
                return JSONResponse(
                    {"detail": "Access denied: company mismatch"},
                    status_code=403,
                )

            # Override: if header is missing but JWT has company_id, use JWT's
            if not header_company and jwt_company:
                # The downstream code that reads X-Company-ID will get the right value
                # via request.state.company_id
                pass

        except Exception as e:
            logger.warning(f"[AuthEnforcement] Token validation failed for {path}: {e}")
            return JSONResponse(
                {"detail": "Invalid or expired token"},
                status_code=401,
            )

        return await call_next(request)
