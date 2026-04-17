"""
Structured provider healthcheck — Task #297.

Reports OK / WARN / FAIL for every external provider that the platform depends
on (sourcing, LLM, auth, dev-mode), based on the presence of the required
environment variables. No external network calls — purely configuration check
suitable for boot-time logging and a lightweight `/health/providers` endpoint.

Status semantics
----------------
- OK    → provider fully usable with current env (key + flags coherent)
- WARN  → provider degraded but platform keeps working (fallback active)
- FAIL  → provider unusable; some user-facing feature will break

Used by:
- `app/main.py` lifespan startup (structured log)
- `app/api/v1/system_health.py` → `/api/v1/health/providers`
"""
from __future__ import annotations

import logging
import os
from typing import Literal, TypedDict

logger = logging.getLogger(__name__)

Status = Literal["ok", "warn", "fail"]


class ProviderStatus(TypedDict):
    status: Status
    detail: str
    env_vars: list[str]
    impacts: list[str]


def _truthy(value: str | None) -> bool:
    return bool(value) and value.strip().lower() not in ("", "false", "0", "no", "off")


def _has_any(*names: str) -> bool:
    return any(_truthy(os.getenv(n)) for n in names)


def collect_provider_health() -> dict[str, ProviderStatus]:
    """Return structured status for every provider the platform depends on."""
    out: dict[str, ProviderStatus] = {}

    # ------------------------------------------------------------------
    # Sourcing — Pearch (global candidate search, 190M+ profiles)
    # ------------------------------------------------------------------
    pearch_key = _truthy(os.getenv("PEARCH_API_KEY"))
    out["pearch"] = {
        "status": "ok" if pearch_key else "fail",
        "detail": (
            "Pearch API key configurada"
            if pearch_key
            else "PEARCH_API_KEY ausente — busca global cai em circuit-open / fallback RAG local"
        ),
        "env_vars": ["PEARCH_API_KEY", "PEARCH_API_URL"],
        "impacts": ["search.candidates(include_pearch=true)", "/api/v1/search/candidates"],
    }

    # ------------------------------------------------------------------
    # Sourcing — Apify (fallback when Pearch circuit is open)
    # ------------------------------------------------------------------
    apify_key = _has_any("APIFY_API_KEY", "APIFY_TOKEN")
    apify_fallback_on = _truthy(os.getenv("APIFY_SEARCH_FALLBACK_ENABLED"))
    if apify_key and apify_fallback_on:
        apify_status: Status = "ok"
        apify_detail = "Apify configurado e fallback de busca ativo"
    elif apify_key and not apify_fallback_on:
        apify_status = "warn"
        apify_detail = (
            "APIFY_API_KEY presente mas APIFY_SEARCH_FALLBACK_ENABLED=false — "
            "fallback do Apify desligado por flag"
        )
    elif not apify_key and apify_fallback_on:
        apify_status = "fail"
        apify_detail = (
            "APIFY_SEARCH_FALLBACK_ENABLED=true mas APIFY_API_KEY/APIFY_TOKEN ausentes — "
            "fallback vai falhar"
        )
    else:
        apify_status = "warn"
        apify_detail = "Apify não configurado (key + flag ausentes) — sem fallback de sourcing"
    out["apify"] = {
        "status": apify_status,
        "detail": apify_detail,
        "env_vars": ["APIFY_API_KEY", "APIFY_TOKEN", "APIFY_SEARCH_FALLBACK_ENABLED"],
        "impacts": ["search.candidates fallback quando Pearch circuit aberto"],
    }

    # ------------------------------------------------------------------
    # LLM — OpenAI (embeddings default, RAG, alguns rubrics)
    # ------------------------------------------------------------------
    openai_key = _has_any("OPENAI_API_KEY", "AI_INTEGRATIONS_OPENAI_API_KEY")
    out["openai"] = {
        "status": "ok" if openai_key else "warn",
        "detail": (
            "OpenAI configurada"
            if openai_key
            else "OPENAI_API_KEY ausente — embeddings/RAG/rubric podem cair em fallback Gemini/Anthropic"
        ),
        "env_vars": ["OPENAI_API_KEY", "AI_INTEGRATIONS_OPENAI_API_KEY"],
        "impacts": ["embeddings_openai", "RAGPipelineService", "RubricEvaluationService"],
    }

    # ------------------------------------------------------------------
    # LLM — Anthropic (Claude — provider primário do orchestrator)
    # ------------------------------------------------------------------
    anthropic_key = _has_any("ANTHROPIC_API_KEY", "AI_INTEGRATIONS_ANTHROPIC_API_KEY")
    out["anthropic"] = {
        "status": "ok" if anthropic_key else "warn",
        "detail": (
            "Anthropic configurada"
            if anthropic_key
            else "ANTHROPIC_API_KEY ausente — provider Claude indisponível"
        ),
        "env_vars": ["ANTHROPIC_API_KEY", "AI_INTEGRATIONS_ANTHROPIC_API_KEY"],
        "impacts": ["LLMProviderFactory[claude]", "Orchestrator (default)"],
    }

    # ------------------------------------------------------------------
    # LLM — Gemini (Google)
    # ------------------------------------------------------------------
    gemini_key = _has_any(
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "AI_INTEGRATIONS_GEMINI_API_KEY",
    )
    out["gemini"] = {
        "status": "ok" if gemini_key else "warn",
        "detail": (
            "Gemini configurado"
            if gemini_key
            else "GEMINI_API_KEY ausente — fallback Gemini indisponível"
        ),
        "env_vars": [
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "AI_INTEGRATIONS_GEMINI_API_KEY",
        ],
        "impacts": ["LLMProviderFactory[gemini]", "embeddings_gemini"],
    }

    # ------------------------------------------------------------------
    # LLM fallback chain — pelo menos UM provider precisa estar OK
    # ------------------------------------------------------------------
    if not (openai_key or anthropic_key or gemini_key):
        out["llm_chain"] = {
            "status": "fail",
            "detail": "Nenhum provider LLM configurado — agentes irão falhar em runtime",
            "env_vars": ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"],
            "impacts": ["TODOS os agentes ReAct e fluxos de chat"],
        }
    else:
        out["llm_chain"] = {
            "status": "ok",
            "detail": "Pelo menos um provider LLM ativo (chain anthropic→gemini→openai)",
            "env_vars": [],
            "impacts": [],
        }

    # ------------------------------------------------------------------
    # Auth — WorkOS (SSO oficial)
    # ------------------------------------------------------------------
    workos_ok = _has_any("WORKOS_API_KEY") and _has_any("WORKOS_CLIENT_ID")
    out["workos"] = {
        "status": "ok" if workos_ok else "warn",
        "detail": (
            "WorkOS configurado"
            if workos_ok
            else "WORKOS_API_KEY/WORKOS_CLIENT_ID ausentes — SSO indisponível, sessão depende de DEV_MODE"
        ),
        "env_vars": ["WORKOS_API_KEY", "WORKOS_CLIENT_ID"],
        "impacts": ["/api/auth/ws-token", "Login SSO"],
    }

    # ------------------------------------------------------------------
    # DEV_MODE — atalho de auth para ambiente local/Replit
    # ------------------------------------------------------------------
    app_env = (os.getenv("APP_ENV") or "development").lower()
    dev_mode_on = _truthy(os.getenv("LIA_DEV_MODE"))
    dev_key = _truthy(os.getenv("LIA_DEV_API_KEY"))
    if app_env in ("production", "prod", "staging"):
        if dev_mode_on:
            dev_status: Status = "fail"
            dev_detail = "LIA_DEV_MODE=true em produção — atalho de auth precisa ser desligado"
        else:
            dev_status = "ok"
            dev_detail = f"APP_ENV={app_env}; DEV_MODE corretamente desligado"
    else:
        if dev_mode_on and dev_key:
            dev_status = "ok"
            dev_detail = "DEV_MODE ativo com API key (uso esperado em dev)"
        elif dev_mode_on and not dev_key:
            dev_status = "warn"
            dev_detail = "LIA_DEV_MODE=true mas LIA_DEV_API_KEY ausente — middleware vai rejeitar"
        else:
            dev_status = "warn"
            dev_detail = "DEV_MODE desligado em ambiente de dev — login real exigido"
    out["dev_mode"] = {
        "status": dev_status,
        "detail": dev_detail,
        "env_vars": ["APP_ENV", "LIA_DEV_MODE", "LIA_DEV_API_KEY"],
        "impacts": ["AuthEnforcementMiddleware (atalho demo)"],
    }

    return out


def overall_status(report: dict[str, ProviderStatus]) -> Status:
    """Reduz o relatório para um único status (worst-of)."""
    if any(p["status"] == "fail" for p in report.values()):
        return "fail"
    if any(p["status"] == "warn" for p in report.values()):
        return "warn"
    return "ok"


def log_boot_report(report: dict[str, ProviderStatus]) -> None:
    """Emite um log estruturado por provider no boot — visível e ruidoso."""
    icons = {"ok": "✅", "warn": "⚠️ ", "fail": "❌"}
    log_funcs = {
        "ok": logger.info,
        "warn": logger.warning,
        "fail": logger.error,
    }
    overall = overall_status(report)
    logger.info("───── Provider healthcheck (boot) ─────")
    for name, status in report.items():
        log_funcs[status["status"]](
            "  %s %-12s [%s] %s",
            icons[status["status"]],
            name,
            status["status"].upper(),
            status["detail"],
        )
    logger.info(
        "───── Overall: %s — runbook: docs/runbooks/sourcing-env-vars.md ─────",
        overall.upper(),
    )
