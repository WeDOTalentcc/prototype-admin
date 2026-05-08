# Backward compatibility re-export — canonical location: talent_funnel_react_agent.py
# R-013 (2026-05-08): TalentReActAgent renamed to TalentFunnelReActAgent to eliminate
# decorator collision risk with TalentPoolReActAgent. The two agents are NOT duplicates:
#   - TalentFunnelReActAgent: recruitment funnel (discovery, analysis, action planning)
#   - TalentPoolReActAgent:   talent bank (passive candidates, pool management)
from .talent_funnel_react_agent import TalentFunnelReActAgent as TalentReActAgent  # noqa: F401

__all__ = ["TalentReActAgent"]
