"""
Rails Migration — Deprecation guard for Python CRUD endpoints.

Context: MIGRATION_PLAN items 7.1 and 7.2 require removing the Python CRUD
endpoints for jobs and candidates because Rails (`ats-api-copia`) is the
source of truth for those resources.

Instead of deleting the files outright (HIGH RISK), this module provides a
FastAPI dependency that:

  1. Logs a structured deprecation warning every time the endpoint is hit,
     so we can track who's still calling the old API.
  2. Adds `Deprecation: true` + `Sunset` + `Link` response headers so HTTP
     clients get the industry-standard signal (RFC 8594 / draft-ietf-deprecation).
  3. When the env var `STRICT_RAILS_ONLY=true` is set, refuses the request
     with HTTP 410 Gone and a pointer to the Rails endpoint. This lets us
     flip the kill-switch in staging/prod independently without redeploy.
  4. Falls through to the legacy Python handler otherwise, so dev
     environments and the transition period keep working.

Usage:
    from app.shared.rails_migration.deprecation import (
        deprecated_in_favor_of_rails,
    )

    router = APIRouter(
        dependencies=[Depends(deprecated_in_favor_of_rails(
            resource="job-vacancies",
            rails_path="/v1/job_vacancies",
            sunset="2026-07-31",
        ))],
    )

Environment variables:
    STRICT_RAILS_ONLY=true   # reject with 410 (default false)
    RAILS_API_URL=<url>      # used in Link header to point at Rails
"""
from __future__ import annotations

import logging
import os
import time
from typing import Callable

import httpx
from fastapi import Depends, HTTPException, Request, Response, status

logger = logging.getLogger(__name__)


def _is_strict_mode() -> bool:
    """Return True when the operator has flipped the kill-switch."""
    return os.environ.get("STRICT_RAILS_ONLY", "false").lower() in {"1", "true", "yes"}


def _rails_url() -> str:
    """Return the configured Rails API URL, or empty string if unset."""
    return os.environ.get("RAILS_API_URL", "").rstrip("/")


# Estado de logging idempotente — emitir ERROR/WARNING apenas uma vez por
# boot por causa, em vez de poluir o log a cada request. Resetado
# naturalmente no próximo restart.
_strict_mode_no_url_logged = False
_strict_mode_unhealthy_logged = False

# Cache simples do health-probe do Rails para não bater na rede a cada
# request guardado. TTL curto: queremos detectar recuperação rápida.
_RAILS_HEALTH_TTL_SECS = 30.0
_RAILS_HEALTH_TIMEOUT_SECS = 2.0
_rails_health_cache: dict[str, float | bool] = {"ok": False, "checked_at": 0.0}


def _probe_rails_healthy(rails_url: str) -> bool:
    """Best-effort sync probe contra `RAILS_HEALTH_PATH` (default /health).

    Resultado cacheado por `_RAILS_HEALTH_TTL_SECS`. Timeout curto pra não
    pendurar requests do usuário se Rails estiver lento. Qualquer 2xx/3xx
    conta como saudável; rede caída ou 5xx contam como unhealthy.
    """
    now = time.monotonic()
    last_check = float(_rails_health_cache.get("checked_at", 0.0))
    if now - last_check < _RAILS_HEALTH_TTL_SECS:
        return bool(_rails_health_cache.get("ok", False))

    health_path = os.environ.get("RAILS_HEALTH_PATH", "/health").lstrip("/")
    url = f"{rails_url}/{health_path}"
    try:
        resp = httpx.get(url, timeout=_RAILS_HEALTH_TIMEOUT_SECS)
        ok = resp.status_code < 500
    except Exception as exc:  # noqa: BLE001 — best-effort probe
        logger.debug("[rails-migration] health probe failed: %s", exc)
        ok = False

    _rails_health_cache["ok"] = ok
    _rails_health_cache["checked_at"] = now
    return ok


def _strict_mode_is_safe() -> bool:
    """Validate that STRICT_RAILS_ONLY pode realmente ser honrado.

    Task #298 / audit causa raiz #9: se alguém liga STRICT_RAILS_ONLY=true sem
    `RAILS_API_URL` configurado, ou com Rails fora do ar, todas as rotas
    guardadas devolveriam 410 Gone — derrubando o Funil. Este guard:

      1. Sem `RAILS_API_URL`: log ERROR uma vez e devolve False (ignora
         kill-switch, cai no fallback Python local).
      2. Com URL mas adapter unhealthy (probe `RAILS_HEALTH_PATH`, default
         /health, com timeout curto e cache de 30s): log WARNING uma vez e
         devolve False — mesmo fallback.
      3. Tudo OK: devolve True, kill-switch honrado normalmente.

    Operador vê o motivo nos logs; usuário não vê 410 surpresa.
    """
    global _strict_mode_no_url_logged, _strict_mode_unhealthy_logged
    rails_url = _rails_url()
    if not rails_url:
        if not _strict_mode_no_url_logged:
            logger.error(
                "[rails-migration] STRICT_RAILS_ONLY=true mas RAILS_API_URL "
                "está vazio — kill-switch IGNORADO para não derrubar "
                "endpoints. Configure RAILS_API_URL ou desligue "
                "STRICT_RAILS_ONLY."
            )
            _strict_mode_no_url_logged = True
        return False

    if not _probe_rails_healthy(rails_url):
        if not _strict_mode_unhealthy_logged:
            logger.warning(
                "[rails-migration] STRICT_RAILS_ONLY=true mas Rails adapter "
                "(%s) está unhealthy — kill-switch IGNORADO temporariamente. "
                "Endpoints servem fallback local até Rails recuperar.",
                rails_url,
            )
            _strict_mode_unhealthy_logged = True
        return False

    # Rails recuperou — permite que próximo log de unhealthy seja emitido.
    _strict_mode_unhealthy_logged = False
    return True


def deprecated_in_favor_of_rails(
    *,
    resource: str,
    rails_path: str,
    sunset: str,
    migration_item: str | None = None,
) -> Callable:
    """Build a FastAPI dependency that marks a router as deprecated.

    Args:
        resource: Short name of the resource (e.g. "job-vacancies"). Used
            in log entries and error messages.
        rails_path: Path on the Rails side where the canonical resource
            lives (e.g. "/v1/job_vacancies"). Appended to RAILS_API_URL
            in the Link header.
        sunset: ISO date (YYYY-MM-DD) after which strict mode should be
            enforced by the operator. Emitted as the `Sunset` header.
        migration_item: Optional MIGRATION_PLAN item reference (e.g. "7.1")
            for traceability in logs.
    """

    async def _enforce(request: Request, response: Response) -> None:
        path = request.url.path
        method = request.method

        # Always log — we want to see the usage pattern of deprecated endpoints
        # until we can safely delete them.
        logger.warning(
            "[rails-migration] deprecated endpoint hit: "
            "method=%s path=%s resource=%s migration_item=%s strict=%s",
            method,
            path,
            resource,
            migration_item or "?",
            _is_strict_mode(),
        )

        # Standard deprecation headers (RFC 8594 / IETF draft).
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = sunset
        rails_url = _rails_url()
        if rails_url:
            response.headers["Link"] = (
                f'<{rails_url}{rails_path}>; rel="successor-version"'
            )

        if _is_strict_mode() and _strict_mode_is_safe():
            detail = {
                "error": "resource_moved",
                "resource": resource,
                "message": (
                    f"The Python API for '{resource}' has been retired. "
                    "The canonical source is Rails."
                ),
                "rails_url": f"{rails_url}{rails_path}" if rails_url else rails_path,
                "migration_item": migration_item,
                "sunset": sunset,
            }
            raise HTTPException(status_code=status.HTTP_410_GONE, detail=detail)

    # Return a callable suitable for `Depends(...)`.
    return _enforce


# Convenience pre-configured dependencies for the two items in Sprint 7.
# Importing these keeps the router files terse.

enforce_job_vacancies_deprecation = deprecated_in_favor_of_rails(
    resource="job-vacancies",
    rails_path="/v1/job_vacancies",
    sunset="2026-07-31",
    migration_item="7.1",
)

enforce_candidates_deprecation = deprecated_in_favor_of_rails(
    resource="candidates",
    rails_path="/v1/candidates",
    sunset="2026-07-31",
    migration_item="7.2",
)
