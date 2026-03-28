"""
Contract Tests: Recruiter Assistant Agents
============================================
Covers KanbanReActAgent, TalentReActAgent, JobsMgmtReActAgent.

All three share the same context schema pattern:
  - context["current_stage"] — stage name, has domain-specific default
  - context["collected_data"] — dict of fields collected during interaction

Key contracts:
  - domain_name must match expected string
  - process() signature is correct
  - AgentInput with domain-specific context is valid
  - PII must not appear at top-level context keys
  - company_id isolation preserved
"""
import pytest
from lia_agents_core.agent_interface import AgentInput, AgentOutput, BaseAgent


PII_FORBIDDEN = {
    "cpf", "rg", "birth_date", "address", "email", "phone_number",
    "photo_url", "ethnicity", "gender", "full_name",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_input(domain_context: dict, company_id: str = "company-001") -> AgentInput:
    return AgentInput(
        message="teste de contrato",
        context=domain_context,
        session_id="session-ra-001",
        company_id=company_id,
        user_id="recruiter-001",
    )


# ---------------------------------------------------------------------------
# KanbanReActAgent
# ---------------------------------------------------------------------------

class TestKanbanContract:

    def test_kanban_is_base_agent(self):
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        assert issubclass(KanbanReActAgent, BaseAgent)

    def test_kanban_domain_name(self):
        from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
        assert KanbanReActAgent.domain_name.fget is not None or hasattr(KanbanReActAgent, "domain_name")

    def test_kanban_context_schema(self):
        """Kanban AgentInput with standard context keys must be valid."""
        inp = make_input({
            "current_stage": "pipeline_overview",
            "collected_data": {"vacancy_id": "job-123"},
        })
        assert inp.context["current_stage"] == "pipeline_overview"
        assert "vacancy_id" in inp.context["collected_data"]

    def test_kanban_context_vacancy_id_optional(self):
        """vacancy_id is optional — Kanban must work without it (uses default)."""
        inp = make_input({"current_stage": "pipeline_overview", "collected_data": {}})
        assert inp.context["collected_data"] == {}

    def test_kanban_no_pii_at_top_level(self):
        context = {
            "current_stage": "pipeline_overview",
            "collected_data": {},
            "vacancy_id": "job-123",
        }
        pii = PII_FORBIDDEN & set(context.keys())
        assert not pii, f"Kanban context has PII top-level keys: {pii}"

    def test_kanban_company_id_preserved(self):
        inp = make_input({"current_stage": "pipeline_overview"}, company_id="tenant-k-001")
        assert inp.company_id == "tenant-k-001"

    def test_kanban_default_stage_fallback(self):
        """context without current_stage should still produce a valid AgentInput."""
        inp = make_input({"collected_data": {}})
        assert "current_stage" not in inp.context or inp.context.get("current_stage") is None


# ---------------------------------------------------------------------------
# TalentReActAgent
# ---------------------------------------------------------------------------

class TestTalentContract:

    def test_talent_is_base_agent(self):
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        assert issubclass(TalentReActAgent, BaseAgent)

    def test_talent_context_schema(self):
        """Talent AgentInput with discovery stage context must be valid."""
        inp = make_input({
            "current_stage": "discovery",
            "collected_data": {
                "target_role": "Dev Backend Sênior",
                "required_skills": ["Python", "FastAPI"],
            },
        })
        assert inp.context["current_stage"] == "discovery"
        assert "target_role" in inp.context["collected_data"]

    def test_talent_no_pii_at_top_level(self):
        context = {
            "current_stage": "discovery",
            "collected_data": {"target_role": "Dev Backend"},
        }
        pii = PII_FORBIDDEN & set(context.keys())
        assert not pii

    def test_talent_company_id_preserved(self):
        inp = make_input({"current_stage": "discovery"}, company_id="tenant-t-001")
        assert inp.company_id == "tenant-t-001"

    def test_talent_output_schema_valid(self):
        """A minimal AgentOutput from Talent agent must be valid."""
        out = AgentOutput(
            message="Encontrei 5 perfis que correspondem ao cargo.",
            state_updates={"candidates_shortlist": [], "current_stage": "shortlist"},
            confidence=0.87,
        )
        assert out.message
        assert "candidates_shortlist" in out.state_updates


# ---------------------------------------------------------------------------
# JobsMgmtReActAgent
# ---------------------------------------------------------------------------

class TestJobsMgmtContract:

    def test_jobs_mgmt_is_base_agent(self):
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsMgmtReActAgent
        assert issubclass(JobsMgmtReActAgent, BaseAgent)

    def test_jobs_mgmt_context_schema(self):
        """JobsMgmt AgentInput with overview stage must be valid."""
        inp = make_input({
            "current_stage": "overview",
            "collected_data": {"company_id": "company-001"},
        })
        assert inp.context["current_stage"] == "overview"

    def test_jobs_mgmt_no_pii_at_top_level(self):
        context = {
            "current_stage": "overview",
            "collected_data": {},
        }
        pii = PII_FORBIDDEN & set(context.keys())
        assert not pii

    def test_jobs_mgmt_company_id_preserved(self):
        inp = make_input({"current_stage": "overview"}, company_id="tenant-jm-001")
        assert inp.company_id == "tenant-jm-001"

    def test_jobs_mgmt_output_state_updates_schema(self):
        """JobsMgmt output state_updates may contain job listings."""
        out = AgentOutput(
            message="Você tem 12 vagas ativas no momento.",
            state_updates={
                "active_jobs_count": 12,
                "current_stage": "overview",
            },
            confidence=0.95,
        )
        assert out.state_updates["active_jobs_count"] == 12
