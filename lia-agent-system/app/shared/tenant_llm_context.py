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

    # Try loading from DB
    try:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT config FROM tenant_llm_configs WHERE company_id = :cid AND is_active = true"),
                {"cid": company_id}
            )
            row = result.fetchone()
            if row:
                import json
                config = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                _tenant_configs[company_id] = config
                return config
    except Exception as e:
        logger.debug("[TenantLLM] No DB config for %s: %s", company_id, e)

    return None


def clear_tenant_config_cache(company_id: str = ""):
    """Clear cached config when tenant updates their LLM settings."""
    if company_id:
        _tenant_configs.pop(company_id, None)
    else:
        _tenant_configs.clear()
