"""Interview Scheduling System Prompts — loads from YAML.
Content source: app/prompts/domains/interview_scheduling.yaml"""
import logging

logger = logging.getLogger(__name__)

try:
    from app.shared.prompts.interaction_patterns import NEGATION_DETECTION_BLOCK
except ImportError:
    NEGATION_DETECTION_BLOCK = ""

def _load():
    try:
        from app.shared.prompts.loader import PromptLoader
        return PromptLoader.load("domains/interview_scheduling")
    except Exception:
        return {}

_cache = None
def _get(key, fallback=""):
    global _cache
    if _cache is None: _cache = _load()
    v = _cache.get(key, fallback)
    return v if isinstance(v, str) else fallback

INTERVIEW_EXTRACTION_PROMPT = _get("system_prompt", "Especialista em Agendamento de Entrevistas.")
INTERVIEW_FEW_SHOT_EXAMPLES = _get("few_shot_examples", "")


def get_extraction_prompt(
    last_message: str,
    current_state: str,
    next_pending_field: str,
) -> str:
    """Retorna o prompt de extração formatado com contexto atual."""
    base = INTERVIEW_EXTRACTION_PROMPT
    # If prompt has format placeholders, fill them
    try:
        base = base.format(
            last_message=last_message,
            current_state=current_state,
            next_pending_field=next_pending_field or "nenhum (todos coletados)",
        )
    except (KeyError, IndexError):
        pass  # YAML prompt may not have placeholders
    return f"{base}\n\n{INTERVIEW_FEW_SHOT_EXAMPLES}\n\n{NEGATION_DETECTION_BLOCK}"
