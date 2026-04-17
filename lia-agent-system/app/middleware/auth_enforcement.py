"""
AuthEnforcementMiddleware — Global authentication, tenant context, and prompt injection guard.

Multi-tenancy security: Every non-public request MUST have a valid JWT.
The middleware:
1. Validates the Bearer token
2. Loads the user from DB
3. Injects user + company_id into request.state
4. Rejects unauthenticated requests with 401
5. Checks all incoming text bodies for prompt injection before reaching agents

This replaces per-endpoint auth and eliminates the X-Company-ID header
trust vulnerability (where a user could forge a different company_id).
"""
import logging
import os
from contextvars import ContextVar

# ContextVar for tenant isolation — read by get_db to inject RLS context
_current_company_id: ContextVar[str] = ContextVar("_current_company_id", default="")

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Eagerly import security guard at module scope (avoids per-request import overhead)
try:
    from app.shared.robustness.security_patterns import (
        check_input_security as _check_input_security,
        get_block_response as _get_block_response,
    )
    _SECURITY_GUARD_AVAILABLE = True
except ImportError:
    _check_input_security = None  # type: ignore[assignment]
    _get_block_response = None  # type: ignore[assignment]
    _SECURITY_GUARD_AVAILABLE = False

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
    "/api/v1/auth/dev-login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/public-register",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/resend-verification",
    "/api/v1/auth/check-sso-domain",
    "/api/v1/auth/workos-callback",
    "/api/v1/auth/workos/callback",
    "/api/v1/data-request",
    "/api/v1/webhooks/whatsapp",
    "/api/v1/teams/webhook",
    "/api/v1/teams/messages",
    "/api/v1/webhooks/twilio-voice",
    "/api/v1/webhooks/mailgun",
    "/api/v1/openmic/webhook",
    "/favicon.ico",
    "/api/v1/health",
    "/api/v1/rails/health",
    "/api/v1/performance",
    "/api/v1/health/performance",
    "/api/v1/health/",
    "/api/v1/health/langgraph",
    "/api/v1/health/providers",
    "/api/v1/navigation-intent",
    # Calendar OAuth callbacks — provider redirects do not carry Bearer tokens;
    # CSRF protection is enforced via HMAC-signed state parameter in each callback handler.
    "/api/v1/calendar/google/callback",
    "/api/v1/calendar/microsoft/callback",
}

# Path prefixes that are public (e.g. static files, docs)
# Dev-mode flag: when True, unauthenticated requests get a synthetic dev-user context
# instead of 401. This allows the Replit demo to work without full SSO/JWT setup.
# SECURITY: Only explicit LIA_DEV_MODE activates dev mode — REPL_ID is NOT used.
_DEV_MODE = os.environ.get("LIA_DEV_MODE", "").lower() in ("1", "true", "yes")
_DEV_API_KEY = os.environ.get("LIA_DEV_API_KEY", "")

if _DEV_MODE:
    logger.warning("[AuthEnforcement] ⚠ DEV_MODE is ACTIVE — authentication is relaxed")


def _check_dev_api_key(request: Request, path: str) -> JSONResponse | None:
    """Validate X-Dev-Api-Key header when DEV_MODE is active.

    Fail-closed: if LIA_DEV_MODE is active but LIA_DEV_API_KEY is NOT configured,
    the request is rejected. This prevents the previous bypass where forgetting
    to set the dev key opened full admin access to every request.

    Returns 401 JSONResponse if auth fails, or None if request should proceed
    with synthetic user injection.
    """
    if not _DEV_API_KEY:
        # LIA-SEC-01: fail-closed. Previously this logged a warning and allowed
        # unauthenticated access — now it rejects the request.
        logger.error(
            "[AuthEnforcement] DEV_MODE active but LIA_DEV_API_KEY not set — rejecting %s %s. "
            "Set LIA_DEV_API_KEY in env or disable LIA_DEV_MODE.",
            request.method, path,
        )
        return JSONResponse(
            {"detail": "DEV_MODE misconfigured: LIA_DEV_API_KEY required"},
            status_code=401,
        )

    provided = request.headers.get("X-Dev-Api-Key", "")
    if provided != _DEV_API_KEY:
        logger.warning(
            "[AuthEnforcement] DEV_MODE request rejected — invalid or missing X-Dev-Api-Key for %s %s",
            request.method, path,
        )
        return JSONResponse({"detail": "Invalid or missing dev API key"}, status_code=401)

    return None

PUBLIC_PREFIXES = (
    "/api/v1/teams/",
    "/api/v1/auth/invitation-info/",
    "/api/v1/wsi/async/",
    "/api/public/",
    "/docs/",
    "/static/",
    "/_next/",
    "/ws/",
    "/teams-icons/",
)


class AuthEnforcementMiddleware(BaseHTTPMiddleware):
    """Global auth middleware that enforces JWT on all non-public routes."""

    # Paths where we perform prompt injection checks on body content
    AGENT_PATHS = (
        "/api/v1/chat",
        "/api/v1/jobs",
        "/api/v1/candidates",
        "/api/v1/wsi",
        "/api/v1/search",
        # LIA-P02 (Wave 2 Fase 3c): user-facing LLM endpoints that previously
        # bypassed PromptInjectionGuard. Background handlers (/api/v1/automation)
        # NOT added — payloads are internal events, not user input.
        "/api/v1/interview-notes",
        "/api/v1/interview_notes",  # both URL forms
        "/api/v1/journey-mapping",
        "/api/v1/journey_mapping",
        "/api/v1/lia",
        "/api/v1/company",
    )

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow public routes
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # Allow OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # ── Prompt injection guard on agent-bound routes ──────────────────────
        # For POST/PUT JSON requests to agent-facing endpoints, check the body.
        # Restricted to application/json content-type to avoid scanning binary
        # or multipart data (e.g. file uploads) and minimize false positives.
        content_type = request.headers.get("content-type", "")
        is_json_body = "application/json" in content_type or content_type == ""
        if (
            request.method in ("POST", "PUT")
            and path.startswith(self.AGENT_PATHS)
            and is_json_body
        ):
            body_bytes = b""
            if not _SECURITY_GUARD_AVAILABLE:
                logger.error("[PromptInjectionGuard] Security guard unavailable — blocking agent route")
                return JSONResponse(
                    {"detail": "Serviço temporariamente indisponível."},
                    status_code=503,
                )
            try:
                body_bytes = await request.body()
                body_text = body_bytes.decode("utf-8", errors="replace")

                if body_text:
                    result = _check_input_security(body_text)
                    if result.is_blocked:
                        logger.warning(
                            f"[PromptInjectionGuard] Blocked on {path}: "
                            f"threats={result.threat_categories}, "
                            f"risk={result.risk_level}, "
                            f"patterns={result.matched_pattern_names}"
                        )
                        return JSONResponse(
                            {"detail": _get_block_response(result, language="pt")},
                            status_code=400,
                        )

            except Exception as guard_err:
                logger.error(f"[PromptInjectionGuard] Guard error on {path}: {guard_err}")
                # Fail-closed: unknown guard errors block agent-bound requests
                return JSONResponse(
                    {"detail": "Solicitação não pôde ser processada."},
                    status_code=400,
                )

            # Reconstruct request with consumed body for downstream handlers
            async def receive():
                return {"type": "http.request", "body": body_bytes, "more_body": False}

            request = Request(request.scope, receive)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            if _DEV_MODE:
                rejection = _check_dev_api_key(request, path)
                if rejection is not None:
                    return rejection
                # Canonical demo UUID (the legacy non-UUID slug is in
                # _INVALID_TENANT_VALUES and breaks resolve_tenant_id).
                from app.core.tenant import DEMO_COMPANY_UUID
                request.state.token_payload = {"sub": "dev-user", "company_id": DEMO_COMPANY_UUID, "role": "admin"}
                request.state.user_id = "dev-user"
                request.state.company_id = DEMO_COMPANY_UUID
                _current_company_id.set(DEMO_COMPANY_UUID)
                request.state.user_role = "admin"
                logger.debug(f"[AuthEnforcement] DEV MODE: synthetic user for {request.method} {path}")
                return await call_next(request)
            logger.warning(f"[AuthEnforcement] No Bearer token for {request.method} {path}")
            return JSONResponse(
                {"detail": "Authentication required"},
                status_code=401,
            )

        token = auth_header[7:]  # Remove "Bearer "

        try:
            from app.auth.security import decode_token
            payload = decode_token(token)
            if payload is None and _DEV_MODE:
                rejection = _check_dev_api_key(request, path)
                if rejection is not None:
                    return rejection
                from app.core.tenant import DEMO_COMPANY_UUID
                request.state.token_payload = {"sub": "dev-user", "company_id": DEMO_COMPANY_UUID, "role": "admin"}
                request.state.user_id = "dev-user"
                request.state.company_id = DEMO_COMPANY_UUID
                _current_company_id.set(DEMO_COMPANY_UUID)
                request.state.user_role = "admin"
                logger.debug(f"[AuthEnforcement] DEV MODE: synthetic user for invalid token on {path}")
                return await call_next(request)

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
            if _DEV_MODE:
                rejection = _check_dev_api_key(request, path)
                if rejection is not None:
                    return rejection
                from app.core.tenant import DEMO_COMPANY_UUID
                request.state.token_payload = {"sub": "dev-user", "company_id": DEMO_COMPANY_UUID, "role": "admin"}
                request.state.user_id = "dev-user"
                request.state.company_id = DEMO_COMPANY_UUID
                _current_company_id.set(DEMO_COMPANY_UUID)
                request.state.user_role = "admin"
                logger.debug(f"[AuthEnforcement] DEV MODE: synthetic user after token error on {path}: {e}")
                return await call_next(request)
            logger.warning(f"[AuthEnforcement] Token validation failed for {path}: {e}")
            return JSONResponse(
                {"detail": "Invalid or expired token"},
                status_code=401,
            )

        return await call_next(request)
