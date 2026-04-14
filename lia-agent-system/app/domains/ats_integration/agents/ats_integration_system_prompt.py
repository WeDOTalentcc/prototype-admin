"""ATS Integration ReAct Agent — loads from YAML.
Content source: app/prompts/domains/ats_integration.yaml"""
import logging

logger = logging.getLogger(__name__)

def _load():
    try:
        from app.shared.prompts.loader import PromptLoader
        return PromptLoader.load("domains/ats_integration")
    except Exception:
        return {}

_cache = None
def _get(key, fallback=""):
    global _cache
    if _cache is None: _cache = _load()
    v = _cache.get(key, fallback)
    return v if isinstance(v, str) else fallback

ATS_INTEGRATION_DOMAIN_SPECIFIC = _get("system_prompt", "Especialista em Integração ATS.")

def get_ats_integration_system_prompt() -> str:
    return ATS_INTEGRATION_DOMAIN_SPECIFIC
