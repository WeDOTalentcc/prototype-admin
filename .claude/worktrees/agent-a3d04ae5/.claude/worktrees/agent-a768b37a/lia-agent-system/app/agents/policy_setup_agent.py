# Shim — real implementation moved to app/domains/policy/agents/ (I3c)
from app.domains.policy.agents.agent import PolicySetupAgent, policy_setup_agent  # noqa: F401
from app.domains.policy.agents.stage_context import (  # noqa: F401
    QUESTIONS,
    BLOCK_NAMES,
    BLOCK_FIELD_MAP,
    PolicySetupSession,
    get_or_create_session,
)
from app.domains.policy.agents.system_prompt import EXTRACTION_PROMPT, REPLY_PROMPT  # noqa: F401
