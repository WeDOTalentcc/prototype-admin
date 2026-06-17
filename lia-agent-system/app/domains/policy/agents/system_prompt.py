"""
System prompts for PolicySetupAgent.

W4-039 (2026-05-23): YAML migration · prompts agora carregam de
`app/prompts/shared/policy_setup.yaml` via canonical PromptLoader pattern.

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W4-039).
Consumers: app/domains/policy/agents/agent.py:202, 296, 324
"""
from app.shared.prompts.loader import PromptLoader


def _load_policy_setup_prompts() -> tuple[str, str]:
    """Load EXTRACTION_PROMPT + REPLY_PROMPT from YAML canonical.

    Cached por PromptLoader (LRU). Fail-fast se YAML missing — não há
    fallback Python (forçar canonical pattern adoption).
    """
    data = PromptLoader.load("shared/policy_setup")
    extraction = data.get("extraction_prompt", "")
    reply = data.get("reply_prompt", "")
    if not extraction or not reply:
        raise RuntimeError(
            "[W4-039] policy_setup.yaml missing extraction_prompt or reply_prompt"
        )
    return extraction, reply


# Module-level constants for back-compat with 3 callers in agent.py
EXTRACTION_PROMPT, REPLY_PROMPT = _load_policy_setup_prompts()

__all__ = ["EXTRACTION_PROMPT", "REPLY_PROMPT"]
