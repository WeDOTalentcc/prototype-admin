# RecruiterAssistantAgent removido (Sprint 5) — use TalentFunnelReActAgent ou JobsMgmtReActAgent.
# TalentReActAgent mantido como alias de backward-compat via shim em talent_react_agent.py.
from .jobs_mgmt_react_agent import JobsManagementReActAgent
from .kanban_react_agent import KanbanReActAgent
from .talent_react_agent import TalentReActAgent  # backward-compat shim → TalentFunnelReActAgent
from .talent_funnel_react_agent import TalentFunnelReActAgent  # R-013: canonical name
