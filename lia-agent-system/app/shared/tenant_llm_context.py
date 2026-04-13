"""
Tenant LLM Context — contextvar that flows company_id to LLMService.

Set by AuthEnforcementMiddleware (already done in Work A).
Read by LLMService to determine which provider/config to use.

Usage:
    # Already set by middleware:
    _current_company_id.set(company_id)

    # LLMService reads it:
    company_id = get_current_llm_tenant()
    if company_id:
        config = get_tenant_llm_config(company_id)
        # Use tenant's provider + API key
"""
import logging
import os

logger = logging.getLogger(__name__)

# Reuse the same contextvar from auth_enforcement
def get_current_llm_tenant() -> str:
    """Get company_id from AuthEnforcementMiddleware contextvar."""
    try:
        from app.middleware.auth_enforcement import _current_company_id
        return _current_company_id.get("")
    except (ImportError, LookupError):
        return ""


# In-memory cache of tenant LLM configs (loaded from DB on first access)
_tenant_configs: dict = {}


async def get_tenant_llm_config(company_id: str) -> dict | None:
    """
    Get LLM config for a tenant. Returns dict with:
    {
        "primary_provider": "gemini",
        "fallback_order": ["gemini", "claude", "openai"],
        "providers": {
            "gemini": {"api_key": "...", "model": "gemini-2.5-flash"},
            "claude": {"api_key": "...", "model": "claude-sonnet-4-6"},
            "openai": {"api_key": "...", "model": "gpt-4o"},
        },
        "routing": {
            "chat": "gemini",
            "embedding": "openai",
            "screening": "claude",
            "voice": "gemini",
        }
    }
    Returns None if no custom config (use global defaults).
    """
    if company_id in _tenant_configs:
        return _tenant_configs[company_id]

    try:
        from lia_config.database import AsyncSessionLocal
        from app.domains.ai.repositories.llm_config_repository import LlmConfigRepository
        async with AsyncSessionLocal() as session:
            repo = LlmConfigRepository(session)
            row = await repo.get_by_company_id(company_id)
            if row and row.is_active:
                config = {
                    "primary_provider": row.primary_provider or "gemini",
                    "fallback_order": row.fallback_order or ["gemini", "claude", "openai"],
                    "providers": row.providers or {},
                    "routing": row.routing or {},
                }
                _tenant_configs[company_id] = config
                return config
    except Exception as e:
        logger.debug("[TenantLLM] No DB config for %s: %s", company_id, e)

    return None


def get_gemini_client_for_tenant(company_id: str | None = None):
    """Get a Gemini genai.Client respecting tenant LLM config.

    If tenant has a custom Gemini API key, creates a client with that key
    (direct Google API, no Replit proxy). Otherwise returns client with
    the global Replit AI Integration key.

    Safe to call from any context — returns a fresh client each time.
    The llm_bootstrap monkey-patch ensures audit logging regardless.
    """
    from google import genai

    tenant_id = company_id or get_current_llm_tenant()
    if tenant_id:
        config = _tenant_configs.get(tenant_id)
        if config:
            providers = config.get("providers", {})
            gemini_cfg = providers.get("gemini", {})
            tenant_key = gemini_cfg.get("api_key")
            if tenant_key:
                logger.info(
                    "[TenantLLM] Using tenant Gemini key for tenant=%s",
                    tenant_id,
                )
                return genai.Client(api_key=tenant_key)

    api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
    if not api_key:
        raise ValueError("AI_INTEGRATIONS_GEMINI_API_KEY not configured")

    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["http_options"] = {"api_version": "", "base_url": base_url}
    return genai.Client(**kwargs)


def get_claude_model_for_tenant(company_id: str | None = None):
    """Get a ChatAnthropic model respecting tenant LLM config.

    If tenant has a custom Claude/Anthropic API key, creates model with
    that key. Otherwise returns None (caller should use global default).
    """
    tenant_id = company_id or get_current_llm_tenant()
    if not tenant_id:
        return None

    config = _tenant_configs.get(tenant_id)
    if not config:
        return None

    providers = config.get("providers", {})
    claude_cfg = providers.get("claude", {})
    tenant_key = claude_cfg.get("api_key")
    if not tenant_key:
        return None

    try:
        from langchain_anthropic import ChatAnthropic

        from app.core.config import settings

        tenant_model = claude_cfg.get("model", settings.LLM_PRIMARY_MODEL)
        logger.info(
            "[TenantLLM] Using tenant Claude key for tenant=%s model=%s",
            tenant_id,
            tenant_model,
        )
        return ChatAnthropic(
            model_name=tenant_model,
            api_key=tenant_key,
            temperature=settings.LLM_DEFAULT_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.warning("[TenantLLM] Failed to create tenant Claude model: %s", exc)
        return None


def clear_tenant_config_cache(company_id: str = ""):
    """Clear cached config when tenant updates their LLM settings."""
    if company_id:
        _tenant_configs.pop(company_id, None)
    else:
        _tenant_configs.clear()


def get_anthropic_streaming_client_for_tenant(
    company_id: str | None = None,
) -> tuple["AsyncAnthropic", str]:
    """Return (AsyncAnthropic client, model_name) respecting tenant Choose Your AI.

    LIA-LLM-1 (Choose Your AI enforcement): Used by SSE/streaming endpoints
    that need native Anthropic streaming (LLMProviderABC does not yet expose
    a stream() method).

    Resolution order:
      1. Tenant has custom Claude key in DB → use tenant key + tenant model
      2. No tenant key → use global env key + global default model

    Args:
        company_id: explicit tenant id. If None, falls back to contextvar.

    Returns:
        (AsyncAnthropic client, model_name) tuple.

    Raises:
        ValueError: when no Claude API key is configured anywhere.
    """
    from anthropic import AsyncAnthropic
    import os as _os
    from app.core.config import settings

    tenant_id = company_id or get_current_llm_tenant()
    api_key: str | None = None
    base_url: str | None = None
    model: str = settings.LLM_PRIMARY_MODEL
    source = "global"

    if tenant_id:
        config = _tenant_configs.get(tenant_id)
        if config:
            providers = config.get("providers", {})
            claude_cfg = providers.get("claude", {})
            tenant_key = claude_cfg.get("api_key")
            if tenant_key:
                api_key = tenant_key
                model = claude_cfg.get("model", model)
                source = f"tenant={tenant_id}"

    if api_key is None:
        api_key = (
            _os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
            or _os.environ.get("ANTHROPIC_API_KEY")
        )
        base_url = _os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

    if not api_key:
        raise ValueError("No Claude API key configured (tenant or global)")

    logger.info(
        "[TenantLLM][stream] Anthropic streaming client source=%s model=%s",
        source, model,
    )

    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncAnthropic(**kwargs), model
