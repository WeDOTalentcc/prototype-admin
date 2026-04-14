"""Analytics ReAct Agent — loads from YAML.
Content source: app/prompts/domains/analytics.yaml"""
import logging

logger = logging.getLogger(__name__)

def _load():
    try:
        from app.shared.prompts.loader import PromptLoader
        return PromptLoader.load("domains/analytics")
    except Exception:
        return {}

_cache = None
def _get(key, fallback=""):
    global _cache
    if _cache is None: _cache = _load()
    v = _cache.get(key, fallback)
    return v if isinstance(v, str) else fallback

ANALYTICS_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Analytics e Métricas.")

def get_analytics_system_prompt() -> str:
    return ANALYTICS_DOMAIN_SPECIFIC
