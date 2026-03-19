# Shim de compatibilidade — implementação real em app/domains/policy/agents/ (Z5-02)
# DEPRECATED: importe diretamente de app.domains.policy.agents.agent
# Este shim será removido em sprint futura.
import warnings
warnings.warn(
    "app.agents.policy_setup_agent está depreciado. "
    "Use app.domains.policy.agents.agent.PolicySetupAgent diretamente.",
    DeprecationWarning,
    stacklevel=2,
)
from app.domains.policy.agents.agent import PolicySetupAgent, policy_setup_agent  # noqa: F401
from app.domains.policy.agents.stage_context import (  # noqa: F401
    QUESTIONS,
    BLOCK_NAMES,
    BLOCK_FIELD_MAP,
    PolicySetupSession,
    get_or_create_session,
)
from app.domains.policy.agents.system_prompt import EXTRACTION_PROMPT, REPLY_PROMPT  # noqa: F401
