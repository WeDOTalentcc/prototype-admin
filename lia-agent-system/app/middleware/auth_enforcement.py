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
from app.core.tenant import DEMO_COMPANY_UUID  # canonical demo UUID (not DEMO_COMPANY_UUID)
from contextvars import ContextVar

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ContextVar for tenant isolation — read by get_db to inject RLS context.
#
# R-008 (Sprint 1 Quick Wins): hardening contra JWT forgery / cross-tenant.
# Esta ContextVar SO PODE ser populada via _set_company_id_from_jwt()
# (helper canonical abaixo) ou via _set_company_id_synthetic_dev_only()
# em paths DEV_MODE explicitamente gateados. NUNCA setar a partir de
# request.body, query params ou headers customizados (X-Company-ID e' usado
# apenas para validar mismatch contra o JWT, nao para preencher o ContextVar).
# Hashimoto: nunca mais cross-tenant via header forging.
_current_company_id: ContextVar[str] = ContextVar("_current_company_id", default="")


def _set_company_id_from_jwt(verified_payload: dict) -> str:
    """R-008: helper canonical — UNICA forma valida de popular ContextVar a partir
    de auth real. Recebe payload JA verificado (signature OK + exp OK) e extrai
    apenas claims do JWT.

    Args:
        verified_payload: dict retornado por decode_token(...) ou validate_rails_token_from_env(...).
            DEVE ser de um token cuja signature ja foi verificada — caller responsavel.

    Returns:
        company_id (str) extraido do payload (vazio se nao houver claim).
    """
    company_id = verified_payload.get("company_id") or ""
    _current_company_id.set(str(company_id))
    return str(company_id)


def _set_company_id_synthetic_dev_only(synthetic_company_id: str = DEMO_COMPANY_UUID) -> str:
    """R-008: helper para path DEV_MODE — APENAS chamavel quando _DEV_MODE=True
    (ja gateado pelo R-006: ENVIRONMENT in safe envs). Documenta intent
    claramente e separa do path de auth real.
    """
    if not _DEV_MODE:
        # Defesa em profundidade: se alguem chamar este helper fora de DEV_MODE,
        # falha alta em vez de silently corromper ContextVar de prod.
        raise RuntimeError(
            "R-008: _set_company_id_synthetic_dev_only chamado mas _DEV_MODE=False. "
            "Synthetic company_id NAO pode ser usado em production/staging."
        )
    _current_company_id.set(synthetic_company_id)
    return synthetic_company_id


# Eagerly import security guard at module scope (avoids per-request import overhead)
try:
    from app.shared.robustness.security_patterns import (
        check_input_security as _check_input_security,
    )
    from app.shared.robustness.security_patterns import (
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
    # Task #1250: env isolation diagnostic — masked, credential-free; used for
    # post-publish curl validation that develop/main use separate DB/Redis.
    "/api/v1/health/environment",
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
#
# R-006 (Sprint 1 Quick Wins): DEV_MODE gateado por ENV. Mesmo que LIA_DEV_MODE=true
# esteja na env, ignoramos se ENVIRONMENT NAO for "test"|"development"|"local".
# Hashimoto: nunca mais bypass de auth ativo em staging/production por config drift.
_LIA_DEV_MODE_RAW = os.environ.get("LIA_DEV_MODE", "").lower() in ("1", "true", "yes")
_ALLOWED_DEV_ENVIRONMENTS = ("test", "development", "local", "dev")
# R-006: check ENVIRONMENT first, fall back to APP_ENV (test compatibility)
_CURRENT_ENVIRONMENT = (os.environ.get("ENVIRONMENT") or os.environ.get("APP_ENV", "")).lower()
_DEV_MODE = _LIA_DEV_MODE_RAW and _CURRENT_ENVIRONMENT in _ALLOWED_DEV_ENVIRONMENTS
_DEV_API_KEY = os.environ.get("LIA_DEV_API_KEY", "")

if _LIA_DEV_MODE_RAW and not _DEV_MODE:
    # LIA_DEV_MODE foi requisitado mas ENVIRONMENT bloqueia — log critico.
    logger.error(
        "[AuthEnforcement] ⛔ R-006: LIA_DEV_MODE=%s requisitado MAS ENVIRONMENT=%r "
        "NAO esta em %s — DEV_MODE PERMANECE INATIVO. Config drift detectado.",
        _LIA_DEV_MODE_RAW,
        _CURRENT_ENVIRONMENT or "(unset)",
        _ALLOWED_DEV_ENVIRONMENTS,
    )
elif _DEV_MODE:
    logger.warning(
        "[AuthEnforcement] ⚠ DEV_MODE is ACTIVE (ENVIRONMENT=%r) — authentication is relaxed",
        _CURRENT_ENVIRONMENT,
    )


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
            request.method,
            path,
        )
        return JSONResponse(
            {"detail": "DEV_MODE misconfigured: LIA_DEV_API_KEY required"},
            status_code=401,
        )

    provided = request.headers.get("X-Dev-Api-Key", "")
    if provided != _DEV_API_KEY:
        logger.warning(
            "[AuthEnforcement] DEV_MODE request rejected — invalid or missing X-Dev-Api-Key for %s %s",
            request.method,
            path,
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

# T-1157: padrões públicos EXPLÍCITOS — substituem o prefixo amplo
# `/api/v1/scheduling/link/` para evitar que sub-rotas futuras (ex.:
# `/api/v1/scheduling/link/admin/X`) fiquem acidentalmente sem auth.
# Apenas o token endpoint e o confirm endpoint são públicos; qualquer
# adição AQUI exige revisão de segurança explícita.
import re as _re

PUBLIC_REGEX_PATHS: tuple[_re.Pattern[str], ...] = (
    # GET /api/v1/scheduling/link/{token}
    _re.compile(r"^/api/v1/scheduling/link/[A-Za-z0-9_\-]{16,128}$"),
    # POST /api/v1/scheduling/link/{token}/confirm
    _re.compile(r"^/api/v1/scheduling/link/[A-Za-z0-9_\-]{16,128}/confirm$"),
    # Sprint 4 B.1 (Paulo 2026-05-23) — candidate-facing triagem endpoints.
    # Resolução de tenant via session_token (UUID v4, não-guessable, expires_at
    # validado). Candidato anônimo acessa o link sem JWT. Multi-tenancy:
    # company_id é lido de session.company_id (set no create_session do recrutador
    # autenticado), NUNCA do request. Audit: AUDIT_CANDIDATE_CHAT_PUBLIC_2026-05-23.md
    # Endpoints admin /triagem/invite e /triagem/voice/* permanecem JWT-only
    # (NÃO matchados pelo regex — só caem nas paths {token}/<verb> abaixo).
    #
    # Token = UUID v4 (36 chars: 8-4-4-4-12). Regex aceita formato canonical apenas.
    _re.compile(
        r"^/api/v1/triagem/"
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        r"(/[A-Za-z0-9_\-/]+)?$"
    ),
    # Twilio Voice webhooks (Paulo 2026-05-23) — P0 phone test unblock.
    # Twilio chama esses endpoints externamente SEM JWT. Autenticação canonical:
    # X-Twilio-Signature header (HMAC-SHA1 com auth_token) validado em cada handler
    # via twilio_voice_service.verify_webhook_signature. Endpoints admin
    # (/initiate, /end-call, /sessions, /voip-token) PRESERVAM JWT — NÃO matchados.
    # Pattern espelha Sprint 4 B.1 (triagem candidato).
    #
    # Endpoints PUBLIC (Twilio externo OR monitoring):
    #   POST   /api/v1/twilio-voice/greeting          (Twilio TwiML callback)
    #   POST   /api/v1/twilio-voice/consent-response  (Twilio Gather speech)
    #   POST   /api/v1/twilio-voice/status            (Twilio status callback)
    #   WS     /api/v1/twilio-voice/audio-stream      (Twilio Media Stream)
    #   POST   /api/v1/twilio-voice/voip-connect      (Twilio VoIP TwiML)
    #   GET    /api/v1/twilio-voice/health            (monitoring externo)
    _re.compile(r"^/api/v1/twilio-voice/greeting/?$"),
    _re.compile(r"^/api/v1/twilio-voice/consent-response/?$"),
    _re.compile(r"^/api/v1/twilio-voice/status/?$"),
    _re.compile(r"^/api/v1/twilio-voice/audio-stream/?$"),
    _re.compile(r"^/api/v1/twilio-voice/voip-connect/?$"),
    _re.compile(r"^/api/v1/twilio-voice/health/?$"),
    # Manager alignment + Hiring NPS — links públicos para gestor/candidato
    # responderem sem JWT. Token = prova de capability (secrets.token_urlsafe(32),
    # validado no handler via get_by_token; company_id derivado do registro,
    # NUNCA do request). Mesmo modelo auditado de scheduling/triagem.
    # Endpoints admin (GET ""/POST de criar) PERMANECEM JWT-only (não matchados).
    _re.compile(r"^/api/v1/manager-alignments/respond/?$"),
    _re.compile(r"^/api/v1/manager-alignments/[0-9a-fA-F\-]{36}/respond/?$"),
    _re.compile(r"^/api/v1/hiring-nps/respond/?$"),
    _re.compile(r"^/api/v1/hiring-nps/[0-9a-fA-F\-]{36}/respond/?$"),
)


def _path_matches_public_regex(path: str) -> bool:
    return any(p.match(path) for p in PUBLIC_REGEX_PATHS)


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
        if (
            path in PUBLIC_PATHS
            or path.startswith(PUBLIC_PREFIXES)
            or _path_matches_public_regex(path)  # T-1157
        ):
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
        if request.method in ("POST", "PUT") and path.startswith(self.AGENT_PATHS) and is_json_body:
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
                request.state.token_payload = {"sub": "dev-user", "company_id": DEMO_COMPANY_UUID, "role": "admin"}
                request.state.user_id = "dev-user"
                request.state.company_id = DEMO_COMPANY_UUID
                _set_company_id_synthetic_dev_only(DEMO_COMPANY_UUID)  # R-008
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

            try:
                payload = decode_token(token)
            except Exception:
                payload = None

            # Fallback: Rails JWT (token assinado pelo ats_api, secret compartilhado)
            if payload is None or not payload.get("sub"):
                from app.auth.rails_jwt import fetch_rails_user_info, validate_rails_token_from_env

                rails_payload = validate_rails_token_from_env(token)
                if rails_payload:
                    rails_info = await fetch_rails_user_info(token, rails_payload.user_id)
                    if rails_info and rails_info.get("email"):
                        payload = {
                            "sub": rails_info["email"],  # placeholder; real user resolvido em get_current_user
                            "company_id": str(rails_info.get("account_id") or ""),
                            "role": "admin" if rails_info.get("is_admin") else "recruiter",
                            "rails_user_id": rails_payload.user_id,
                            "email": rails_info["email"],
                        }

            if payload is None and _DEV_MODE:
                rejection = _check_dev_api_key(request, path)
                if rejection is not None:
                    return rejection
                request.state.token_payload = {"sub": "dev-user", "company_id": DEMO_COMPANY_UUID, "role": "admin"}
                request.state.user_id = "dev-user"
                request.state.company_id = DEMO_COMPANY_UUID
                _set_company_id_synthetic_dev_only(DEMO_COMPANY_UUID)  # R-008
                request.state.user_role = "admin"
                logger.debug(f"[AuthEnforcement] DEV MODE: synthetic user for invalid token on {path}")
                return await call_next(request)

            if payload is None:
                raise ValueError("Invalid or expired token")

            user_id = payload.get("sub")
            if not user_id:
                return JSONResponse({"detail": "Invalid token: no subject"}, status_code=401)

            # Inject into request.state for downstream use.
            # R-008: ContextVar populado APENAS via helper canonical, com payload
            # ja verificado pelo decode_token / validate_rails_token_from_env.
            request.state.token_payload = payload
            request.state.user_id = user_id
            request.state.company_id = payload.get("company_id", "")
            _set_company_id_from_jwt(payload)  # R-008 — ContextVar so via helper
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
                request.state.token_payload = {"sub": "dev-user", "company_id": DEMO_COMPANY_UUID, "role": "admin"}
                request.state.user_id = "dev-user"
                request.state.company_id = DEMO_COMPANY_UUID
                _set_company_id_synthetic_dev_only(DEMO_COMPANY_UUID)  # R-008
                request.state.user_role = "admin"
                logger.debug(f"[AuthEnforcement] DEV MODE: synthetic user after token error on {path}: {e}")
                return await call_next(request)
            logger.warning(f"[AuthEnforcement] Token validation failed for {path}: {e}")
            return JSONResponse(
                {"detail": "Invalid or expired token"},
                status_code=401,
            )

        return await call_next(request)
