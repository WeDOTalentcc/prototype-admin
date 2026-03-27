# Sprint 5 — Arquitetura consolidada. Agentes canônicos:
# - 7 ReAct Agents (wizard, pipeline, sourcing, talent, jobs_management, kanban, policy)
# - 1 ReAct Agent (automation) — AutomationReActAgent
# - 3 LangGraph Graphs (JobWizardGraph, WSIInterviewGraph, InterviewGraph)
#
# Legacy removidos:
#   SchedulingAgent, EntrevistadorAgent → InterviewGraph
#   TaskPlannerAgent → AutomationReActAgent (app/domains/automation/agents/)
#   TriagemCurricularAgent → CVScreeningBatchService (app/domains/cv_screening/services/)
#   CommunicationAgent → CommunicationService
#   AnalyticsAgent, AnalistaFeedbackAgent → analytics services
#   IntegradorATSAgent → REST endpoints + Merge/StackOne
from app.domains.sourcing.services.query_builders import BooleanQueryBuilder, CandidateMatcher
from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph, interview_graph
from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
from app.domains.cv_screening.services.cv_screening_batch_service import run_batch as run_cv_screening_batch
